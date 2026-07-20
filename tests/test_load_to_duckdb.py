from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.python_ingestion.load_to_duckdb import load_to_duckdb


def _write_core_fixtures(raw_dir: Path) -> None:
    raw_dir.mkdir()
    pd.DataFrame([{"customer_id": "c1"}]).to_csv(raw_dir / "customers.csv", index=False)
    pd.DataFrame([{"account_id": "a1", "customer_id": "c1"}]).to_csv(
        raw_dir / "accounts.csv", index=False
    )
    pd.DataFrame([{"transaction_id": "t1", "customer_id": "c1", "amount": 10.0}]).to_csv(
        raw_dir / "transactions.csv", index=False
    )
    pd.DataFrame([{"loan_id": "l1", "customer_id": "c1"}]).to_csv(
        raw_dir / "loans.csv", index=False
    )


def test_load_to_duckdb_loads_core_and_available_optional_tables(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    _write_core_fixtures(raw_dir)
    pd.DataFrame([{"observation_date": "2026-01-01", "indicator_name": "selic", "value": 12.0}]).to_csv(
        raw_dir / "macro_indicators.csv", index=False
    )
    database = tmp_path / "warehouse.duckdb"

    load_to_duckdb(database, raw_dir)

    with duckdb.connect(str(database)) as connection:
        assert connection.execute("select count(*) from raw.customers").fetchone()[0] == 1
        assert connection.execute("select count(*) from raw.macro_indicators").fetchone()[0] == 1


def test_load_to_duckdb_rejects_missing_core_file(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    _write_core_fixtures(raw_dir)
    (raw_dir / "loans.csv").unlink()

    with pytest.raises(FileNotFoundError, match="loans.csv"):
        load_to_duckdb(tmp_path / "warehouse.duckdb", raw_dir)
