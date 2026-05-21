from pathlib import Path

import pandas as pd

from src.lakehouse.local_layers import build_local_layers


def test_build_local_layers_writes_bronze_silver_gold_and_manifest(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    lakehouse_dir = tmp_path / "lakehouse"
    raw_dir.mkdir()

    pd.DataFrame(
        [
            {"customer_id": "c1", "segment": "PF_MASS", "state": "SP", "internal_score": 710},
            {"customer_id": "c2", "segment": "PJ_SMALL", "state": "RJ", "internal_score": 640},
        ]
    ).to_csv(raw_dir / "customers.csv", index=False)
    pd.DataFrame(
        [
            {
                "loan_id": "l1",
                "customer_id": "c1",
                "principal_amount": 1000.0,
                "outstanding_balance": 700.0,
                "days_past_due": 0,
            },
            {
                "loan_id": "l2",
                "customer_id": "c1",
                "principal_amount": 500.0,
                "outstanding_balance": 300.0,
                "days_past_due": 45,
            },
        ]
    ).to_csv(raw_dir / "loans.csv", index=False)

    result = build_local_layers(raw_dir=raw_dir, lakehouse_dir=lakehouse_dir, batch_id="test-batch")

    assert result.batch_id == "test-batch"
    assert result.tables == {"customers": 2, "loans": 2}
    assert (lakehouse_dir / "bronze" / "customers" / "batch_id=test-batch" / "customers.csv").exists()
    assert (lakehouse_dir / "silver" / "loans" / "batch_id=test-batch" / "loans.parquet").exists()
    assert (lakehouse_dir / "gold" / "customer_credit_snapshot" / "batch_id=test-batch" / "data.parquet").exists()
    assert (lakehouse_dir / "manifest.json").exists()

    gold = pd.read_parquet(
        lakehouse_dir / "gold" / "customer_credit_snapshot" / "batch_id=test-batch" / "data.parquet"
    )
    row = gold.loc[gold["customer_id"] == "c1"].iloc[0]
    assert row["loan_count"] == 2
    assert row["total_outstanding_balance"] == 1000.0
    assert row["max_days_past_due"] == 45
