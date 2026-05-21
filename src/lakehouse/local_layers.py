from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class LocalLayerBuildResult:
    batch_id: str
    tables: dict[str, int]
    bronze_files: list[str]
    silver_files: list[str]
    gold_files: list[str]
    manifest_path: str


def build_local_layers(
    *,
    raw_dir: Path = Path("data/raw"),
    lakehouse_dir: Path = Path("data/lakehouse"),
    batch_id: str | None = None,
    processed_at: datetime | None = None,
) -> LocalLayerBuildResult:
    """Build a free local Bronze/Silver/Gold path from raw CSV files."""
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    batch = batch_id or datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    timestamp = processed_at or datetime.now(UTC)
    raw_files = sorted(raw_dir.glob("*.csv"))
    if not raw_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    tables: dict[str, int] = {}
    bronze_files: list[str] = []
    silver_files: list[str] = []
    frames: dict[str, pd.DataFrame] = {}

    for source in raw_files:
        table_name = source.stem
        raw_frame = pd.read_csv(source)
        tables[table_name] = len(raw_frame)
        frames[table_name] = raw_frame

        bronze_dir = lakehouse_dir / "bronze" / table_name / f"batch_id={batch}"
        bronze_dir.mkdir(parents=True, exist_ok=True)
        bronze_csv = bronze_dir / source.name
        bronze_parquet = bronze_dir / f"{table_name}.parquet"
        shutil.copy2(source, bronze_csv)
        raw_frame.to_parquet(bronze_parquet, index=False)
        bronze_files.extend([str(bronze_csv), str(bronze_parquet)])

        silver = _standardize_frame(raw_frame, processed_at=timestamp)
        silver_dir = lakehouse_dir / "silver" / table_name / f"batch_id={batch}"
        silver_dir.mkdir(parents=True, exist_ok=True)
        silver_path = silver_dir / f"{table_name}.parquet"
        silver.to_parquet(silver_path, index=False)
        silver_files.append(str(silver_path))

    gold_files = _write_gold_outputs(frames, lakehouse_dir=lakehouse_dir, batch_id=batch)
    manifest_path = lakehouse_dir / "manifest.json"
    result = LocalLayerBuildResult(
        batch_id=batch,
        tables=tables,
        bronze_files=bronze_files,
        silver_files=silver_files,
        gold_files=gold_files,
        manifest_path=str(manifest_path),
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True), encoding="utf-8")
    return result


def _standardize_frame(frame: pd.DataFrame, *, processed_at: datetime) -> pd.DataFrame:
    silver = frame.copy()
    silver.columns = [str(column).strip().lower() for column in silver.columns]
    silver = silver.drop_duplicates()
    silver["ingestion_processed_at"] = processed_at.isoformat()
    return silver


def _write_gold_outputs(frames: dict[str, pd.DataFrame], *, lakehouse_dir: Path, batch_id: str) -> list[str]:
    gold_files: list[str] = []
    if {"customers", "loans"}.issubset(frames):
        customers = frames["customers"].copy()
        loans = frames["loans"].copy()
        loan_agg = (
            loans.groupby("customer_id", as_index=False)
            .agg(
                loan_count=("loan_id", "nunique"),
                total_principal_amount=("principal_amount", "sum"),
                total_outstanding_balance=("outstanding_balance", "sum"),
                max_days_past_due=("days_past_due", "max"),
            )
        )
        snapshot = customers.merge(loan_agg, on="customer_id", how="left")
        snapshot["loan_count"] = snapshot["loan_count"].fillna(0).astype(int)
        for column in ("total_principal_amount", "total_outstanding_balance", "max_days_past_due"):
            snapshot[column] = snapshot[column].fillna(0)
        gold_files.append(_write_gold_frame(snapshot, "customer_credit_snapshot", lakehouse_dir, batch_id))

    if "transactions" in frames:
        transactions = frames["transactions"].copy()
        if {"transaction_date", "channel", "amount", "is_suspicious"}.issubset(transactions.columns):
            transactions["is_suspicious"] = transactions["is_suspicious"].astype(bool)
            daily = (
                transactions.groupby(["transaction_date", "channel"], as_index=False)
                .agg(
                    transaction_count=("transaction_id", "nunique"),
                    total_amount=("amount", "sum"),
                    suspicious_count=("is_suspicious", "sum"),
                )
                .sort_values(["transaction_date", "channel"])
            )
            gold_files.append(_write_gold_frame(daily, "daily_transaction_monitoring", lakehouse_dir, batch_id))

    return gold_files


def _write_gold_frame(frame: pd.DataFrame, name: str, lakehouse_dir: Path, batch_id: str) -> str:
    target_dir = lakehouse_dir / "gold" / name / f"batch_id={batch_id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "data.parquet"
    frame.to_parquet(target, index=False)
    return str(target)


def main() -> None:
    result = build_local_layers()
    print(f"Built local lakehouse batch {result.batch_id}")
    print(f"Tables: {result.tables}")
    print(f"Manifest: {result.manifest_path}")


if __name__ == "__main__":
    main()
