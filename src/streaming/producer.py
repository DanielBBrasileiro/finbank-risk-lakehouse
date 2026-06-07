from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

RAW_DIR = Path("data/raw")
FALLBACK_PATH = Path("data/streaming/suspicious_transactions_fallback.jsonl")


def run_producer() -> None:
    transactions_path = RAW_DIR / "transactions.csv"
    if not transactions_path.exists():
        raise FileNotFoundError(f"Missing transactions file: {transactions_path}. Run make generate first.")

    import csv

    with open(transactions_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        suspicious = [row for row in reader if row["is_suspicious"].lower() in ("true", "1", "t", "yes")]

    # Sort by transaction_id to match original behavior
    suspicious.sort(key=lambda x: x["transaction_id"])

    print(f"Loaded {len(suspicious):,} suspicious transactions to stream.")

    # Try connecting to Redpanda
    producer = None
    broker = os.getenv("KAFKA_BROKER", "localhost:9092")

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

    if broker_reachable:
        try:
            from kafka import KafkaProducer

            producer = KafkaProducer(
                bootstrap_servers=[broker],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                request_timeout_ms=1000,
            )
            print(f"Connected to Redpanda broker at {broker}.")
        except Exception as e:
            print(f"Could not connect to Redpanda broker: {e}. Falling back to local JSONL streaming file.")
            FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
            FALLBACK_PATH.write_text("")
    else:
        print(f"Broker {broker} is not reachable. Falling back to local JSONL streaming file.")
        FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Clear fallback file first
        FALLBACK_PATH.write_text("")

    events_sent = 0
    for row in suspicious:
        event = {
            "event_type": "suspicious_transaction_detected",
            "timestamp": datetime.now(UTC).isoformat(),
            "transaction_id": str(row["transaction_id"]),
            "customer_id": str(row["customer_id"]),
            "account_id": str(row["account_id"]),
            "transaction_date": str(row["transaction_date"]),
            "channel": row["channel"],
            "amount": float(row["amount"]),
        }

        if producer:
            try:
                producer.send("suspicious-transactions", value=event)
                events_sent += 1
            except Exception as err:
                print(f"Kafka send error: {err}. Writing to fallback.")
                with FALLBACK_PATH.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
        else:
            with FALLBACK_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
            events_sent += 1

        time.sleep(0.0001)

    if producer:
        producer.flush()
        producer.close()

    print(f"Producer finished. Streamed {events_sent} events successfully.")


if __name__ == "__main__":
    run_producer()
