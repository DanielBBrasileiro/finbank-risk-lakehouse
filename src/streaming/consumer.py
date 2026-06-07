from __future__ import annotations

import json
import os
from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

FALLBACK_PATH = Path("data/streaming/suspicious_transactions_fallback.jsonl")


def get_engine():
    db_target = os.getenv("DB_TARGET", "").lower()
    duckdb_file = Path(os.getenv("DUCKDB_PATH", "data/warehouse.duckdb"))

    if db_target == "duckdb" and (duckdb_file.exists() or os.getenv("DUCKDB_PATH")):
        from sqlalchemy import create_engine
        return create_engine(f"duckdb:///{duckdb_file}")

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


def process_event(event: dict, engine) -> None:
    customer_id = str(event["customer_id"])
    amount = float(event["amount"])
    timestamp = event.get("timestamp", event.get("transaction_date"))

    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS raw.streaming_suspicious_summary ("
                "  customer_id VARCHAR PRIMARY KEY,"
                "  suspicious_count INTEGER,"
                "  total_suspicious_amount DOUBLE PRECISION,"
                "  last_suspicious_timestamp VARCHAR"
                ");"
            )
        )

        res = conn.execute(
            text(
                "SELECT suspicious_count, total_suspicious_amount FROM raw.streaming_suspicious_summary WHERE customer_id = :cid"
            ),
            {"cid": customer_id},
        ).fetchone()

        if res:
            new_count = res[0] + 1
            new_amount = res[1] + amount
            conn.execute(
                text(
                    "UPDATE raw.streaming_suspicious_summary "
                    "SET suspicious_count = :count, total_suspicious_amount = :amount, last_suspicious_timestamp = :ts "
                    "WHERE customer_id = :cid"
                ),
                {"count": new_count, "amount": new_amount, "ts": timestamp, "cid": customer_id},
            )
        else:
            conn.execute(
                text(
                    "INSERT INTO raw.streaming_suspicious_summary (customer_id, suspicious_count, total_suspicious_amount, last_suspicious_timestamp) "
                    "VALUES (:cid, 1, :amount, :ts)"
                ),
                {"cid": customer_id, "amount": amount, "ts": timestamp},
            )


def run_consumer(one_shot: bool = False) -> None:
    broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    engine = get_engine()

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
            consumer = KafkaConsumer(
                "suspicious-transactions",
                bootstrap_servers=[broker],
                auto_offset_reset="earliest",
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                consumer_timeout_ms=2000 if one_shot else None,
            )
            print(f"Connected to Redpanda at {broker}. Consuming from 'suspicious-transactions' topic...")
        except Exception as e:
            print(f"Could not connect to Kafka: {e}. Consuming from local fallback file.")
    else:
        print(f"Broker {broker} is not reachable. Consuming from local fallback file.")

    if consumer:
        try:
            events_processed = 0
            for message in consumer:
                process_event(message.value, engine)
                events_processed += 1
                if one_shot and events_processed >= 1000:
                    break
            print(f"One-shot finish: Processed {events_processed} events from Kafka.")
        finally:
            consumer.close()
    else:
        if not FALLBACK_PATH.exists():
            print("No fallback file found. Nothing to consume.")
            engine.dispose()
            return

        events_processed = 0
        with FALLBACK_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    process_event(event, engine)
                    events_processed += 1
        print(f"Processed {events_processed} events from local JSONL fallback.")

    engine.dispose()


def main() -> None:
    parser = ArgumentParser(description="Consume suspicious transactions stream.")
    parser.add_argument("--one-shot", action="store_true", help="Process currently buffered events and exit.")
    args = parser.parse_args()

    run_consumer(one_shot=args.one_shot)


if __name__ == "__main__":
    main()
