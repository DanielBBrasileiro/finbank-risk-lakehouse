from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError

RAW_DIR = Path("data/raw")
FALLBACK_PATH = Path("data/streaming/suspicious_transactions_fallback.jsonl")


def run_producer() -> None:
    transactions_path = RAW_DIR / "transactions.csv"
    if not transactions_path.exists():
        raise FileNotFoundError(f"Missing transactions file: {transactions_path}. Run make generate first.")

    transactions = pd.read_csv(transactions_path)
    suspicious = transactions[transactions["is_suspicious"].astype(bool)].copy()

    print(f"Loaded {len(suspicious):,} suspicious transactions to stream.")

    # Try connecting to Redpanda
    producer = None
    broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    try:
        producer = KafkaProducer(
            bootstrap_servers=[broker],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=3000,
        )
        print(f"Connected to Redpanda broker at {broker}.")
    except Exception as e:
        print(f"Could not connect to Redpanda broker: {e}. Falling back to local JSONL streaming file.")
        FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Clear fallback file first
        FALLBACK_PATH.write_text("")

    events_sent = 0
    for row in suspicious.sort_values("transaction_id").to_dict(orient="records"):
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
            except KafkaError as err:
                print(f"Kafka send error: {err}. Writing to fallback.")
                with FALLBACK_PATH.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
        else:
            with FALLBACK_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
            events_sent += 1

        time.sleep(0.001)

    if producer:
        producer.flush()
        producer.close()

    print(f"Producer finished. Streamed {events_sent} events successfully.")


if __name__ == "__main__":
    run_producer()
