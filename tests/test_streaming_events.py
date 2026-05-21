from pathlib import Path

import pandas as pd

from src.streaming.suspicious_events import write_suspicious_event_batch


def test_write_suspicious_event_batch_filters_and_serializes_suspicious_transactions(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    output_dir = tmp_path / "streaming"
    raw_dir.mkdir()
    pd.DataFrame(
        [
            {
                "transaction_id": "t1",
                "customer_id": "c1",
                "account_id": "a1",
                "transaction_date": "2026-01-01",
                "channel": "PIX",
                "amount": 3000.0,
                "is_suspicious": True,
            },
            {
                "transaction_id": "t2",
                "customer_id": "c2",
                "account_id": "a2",
                "transaction_date": "2026-01-01",
                "channel": "CARD",
                "amount": 50.0,
                "is_suspicious": False,
            },
        ]
    ).to_csv(raw_dir / "transactions.csv", index=False)

    output = write_suspicious_event_batch(raw_dir=raw_dir, output_dir=output_dir, batch_id="demo")

    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert '"event_type": "suspicious_transaction_detected"' in lines[0]
    assert '"transaction_id": "t1"' in lines[0]
