from __future__ import annotations

import json
import os
import time
from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv

FALLBACK_PATH = Path("data/streaming/suspicious_transactions_fallback.jsonl")
DEFAULT_GROUP_ID = "finbank-suspicious-summary-v1"
_LOCK_ERROR_MARKERS = (
    "database is locked",
    "database is busy",
    "could not set lock",
    "conflicting lock",
    "lock conflict",
)


def get_engine():
    db_target = os.getenv("DB_TARGET", "").lower()
    duckdb_file = Path(os.getenv("DUCKDB_PATH", "data/warehouse.duckdb"))

    if db_target == "duckdb" and (duckdb_file.exists() or os.getenv("DUCKDB_PATH")):
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        # DuckDB is embedded; closing every short transaction releases the file
        # handle instead of retaining it in SQLAlchemy's connection pool.
        return create_engine(f"duckdb:///{duckdb_file}", poolclass=NullPool)

    user = os.getenv("POSTGRES_USER", "finbank")
    password = os.getenv("POSTGRES_PASSWORD", "finbank")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "finbank")

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as err:
        if duckdb_file.exists():
            from sqlalchemy import create_engine
            return create_engine(f"duckdb:///{duckdb_file}")
        raise ValueError("Could not connect to Postgres and no local DuckDB found.") from err


def initialize_storage(engine) -> None:
    """Create idempotency and serving tables in a short transaction."""
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS raw.streaming_suspicious_events ("
                "  transaction_id VARCHAR PRIMARY KEY,"
                "  customer_id VARCHAR NOT NULL,"
                "  amount DOUBLE PRECISION NOT NULL,"
                "  event_timestamp VARCHAR,"
                "  event_payload VARCHAR NOT NULL"
                ");"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS raw.streaming_suspicious_summary ("
                "  customer_id VARCHAR PRIMARY KEY,"
                "  suspicious_count INTEGER NOT NULL,"
                "  total_suspicious_amount DOUBLE PRECISION NOT NULL,"
                "  last_suspicious_timestamp VARCHAR"
                ");"
            )
        )


def process_event(event: dict, engine) -> bool:
    """Persist one event and update its summary exactly once.

    Returns ``True`` when the transaction was new and ``False`` for a replay.
    The event insert and aggregate update share one transaction, so a retry
    cannot leave the idempotency ledger ahead of the summary.
    """
    transaction_id = str(event.get("transaction_id", "")).strip()
    customer_id = str(event.get("customer_id", "")).strip()
    if not transaction_id:
        raise ValueError("Streaming event requires a non-empty transaction_id.")
    if not customer_id:
        raise ValueError("Streaming event requires a non-empty customer_id.")

    amount = float(event["amount"])
    timestamp = event.get("timestamp", event.get("transaction_date"))
    payload = json.dumps(event, sort_keys=True, default=str)

    from sqlalchemy import text

    retries = max(1, int(os.getenv("STREAMING_DB_RETRIES", "5")))
    base_delay = max(0.0, float(os.getenv("STREAMING_DB_RETRY_DELAY_SECONDS", "0.05")))
    for attempt in range(retries):
        try:
            with engine.begin() as conn:
                inserted = conn.execute(
                    text(
                        "INSERT INTO raw.streaming_suspicious_events "
                        "(transaction_id, customer_id, amount, event_timestamp, event_payload) "
                        "VALUES (:tid, :cid, :amount, :ts, :payload) "
                        "ON CONFLICT (transaction_id) DO NOTHING "
                        "RETURNING transaction_id"
                    ),
                    {
                        "tid": transaction_id,
                        "cid": customer_id,
                        "amount": amount,
                        "ts": timestamp,
                        "payload": payload,
                    },
                ).fetchone()
                if inserted is None:
                    return False

                conn.execute(
                    text(
                        "INSERT INTO raw.streaming_suspicious_summary "
                        "(customer_id, suspicious_count, total_suspicious_amount, last_suspicious_timestamp) "
                        "VALUES (:cid, 1, :amount, :ts) "
                        "ON CONFLICT (customer_id) DO UPDATE SET "
                        "suspicious_count = raw.streaming_suspicious_summary.suspicious_count + 1, "
                        "total_suspicious_amount = "
                        "raw.streaming_suspicious_summary.total_suspicious_amount + EXCLUDED.total_suspicious_amount, "
                        "last_suspicious_timestamp = EXCLUDED.last_suspicious_timestamp"
                    ),
                    {"cid": customer_id, "amount": amount, "ts": timestamp},
                )
            return True
        except Exception as exc:
            if not _is_retryable_lock_error(exc) or attempt == retries - 1:
                raise
            time.sleep(base_delay * (2**attempt))

    return False


def _is_retryable_lock_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in _LOCK_ERROR_MARKERS)


def run_consumer(one_shot: bool = False) -> None:
    load_dotenv()
    broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    engine = get_engine()
    initialize_storage(engine)

    print("Starting Streaming Consumer...")

    # Check if broker is reachable using a fast socket connection
    import socket
    broker_reachable = False
    try:
        host, port_str = broker.split(":")
        port = int(port_str)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            if s.connect_ex((host, port)) == 0:
                broker_reachable = True
    except Exception:
        pass

    consumer = None
    if broker_reachable:
        try:
            from kafka import KafkaConsumer
            auto_offset_reset = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest").lower()
            if auto_offset_reset not in {"earliest", "latest"}:
                raise ValueError("KAFKA_AUTO_OFFSET_RESET must be 'earliest' or 'latest'.")
            consumer_options = {
                "bootstrap_servers": [broker],
                "group_id": os.getenv("KAFKA_GROUP_ID", DEFAULT_GROUP_ID),
                "auto_offset_reset": auto_offset_reset,
                "enable_auto_commit": False,
                "value_deserializer": lambda x: json.loads(x.decode("utf-8")),
            }
            if one_shot:
                consumer_options["consumer_timeout_ms"] = 2000
            consumer = KafkaConsumer("suspicious-transactions", **consumer_options)
            print(f"Connected to Redpanda at {broker}. Consuming from 'suspicious-transactions' topic...")
        except Exception as e:
            print(f"Could not connect to Kafka: {e}. Consuming from local fallback file.")
    else:
        print(f"Broker {broker} is not reachable. Consuming from local fallback file.")

    if consumer:
        try:
            events_processed = 0
            duplicate_events = 0
            for message in consumer:
                if process_event(message.value, engine):
                    events_processed += 1
                else:
                    duplicate_events += 1
                # Commit only after the database transaction succeeds. Replays
                # after a crash are harmless because transaction_id is unique.
                consumer.commit()
                if one_shot and events_processed >= 1000:
                    break
            print(
                f"One-shot finish: Processed {events_processed} new events from Kafka "
                f"({duplicate_events} duplicates skipped)."
            )
        finally:
            consumer.close()
    else:
        if not FALLBACK_PATH.exists():
            print("No fallback file found. Nothing to consume.")
            engine.dispose()
            return

        events_processed = 0
        duplicate_events = 0
        with FALLBACK_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if process_event(event, engine):
                        events_processed += 1
                    else:
                        duplicate_events += 1
        print(
            f"Processed {events_processed} new events from local JSONL fallback "
            f"({duplicate_events} duplicates skipped)."
        )

    engine.dispose()


def main() -> None:
    parser = ArgumentParser(description="Consume suspicious transactions stream.")
    parser.add_argument("--one-shot", action="store_true", help="Process currently buffered events and exit.")
    args = parser.parse_args()

    run_consumer(one_shot=args.one_shot)


if __name__ == "__main__":
    main()
