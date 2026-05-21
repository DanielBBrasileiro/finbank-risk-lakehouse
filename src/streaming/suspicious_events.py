from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def write_suspicious_event_batch(
    *,
    raw_dir: Path = Path("data/raw"),
    output_dir: Path = Path("data/streaming"),
    batch_id: str | None = None,
) -> Path:
    transactions_path = raw_dir / "transactions.csv"
    if not transactions_path.exists():
        raise FileNotFoundError(f"Missing transactions file: {transactions_path}. Run make generate first.")

    batch = batch_id or datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"suspicious_transactions_{batch}.jsonl"

    transactions = pd.read_csv(transactions_path)
    suspicious = transactions[transactions["is_suspicious"].astype(bool)].copy()
    with output.open("w", encoding="utf-8") as handle:
        for row in suspicious.sort_values("transaction_id").to_dict(orient="records"):
            event = {
                "event_type": "suspicious_transaction_detected",
                "batch_id": batch,
                "transaction_id": row["transaction_id"],
                "customer_id": row["customer_id"],
                "account_id": row["account_id"],
                "transaction_date": str(row["transaction_date"]),
                "channel": row["channel"],
                "amount": float(row["amount"]),
            }
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    return output


def main() -> None:
    output = write_suspicious_event_batch()
    print(output)


if __name__ == "__main__":
    main()
