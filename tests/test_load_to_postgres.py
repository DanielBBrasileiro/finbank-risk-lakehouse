from pathlib import Path

import pandas as pd
import pytest

from src.python_ingestion.load_to_postgres import _read_csv, tables_to_load


def test_tables_to_load_includes_macro_indicators_when_present(tmp_path: Path) -> None:
    (tmp_path / "macro_indicators.csv").write_text("observation_date,indicator_name,series_id,value\n", encoding="utf-8")

    tables = tables_to_load(raw_dir=tmp_path)

    assert ("macro_indicators", "macro_indicators.csv") in tables


def test_read_csv_rejects_column_contract_mismatch(tmp_path: Path) -> None:
    pd.DataFrame([{"customer_id": "c1", "unexpected": "value"}]).to_csv(
        tmp_path / "customers.csv", index=False
    )

    with pytest.raises(ValueError, match="Column contract mismatch"):
        _read_csv("customers", "customers.csv", raw_dir=tmp_path)


def test_postgres_loader_preserves_table_definitions() -> None:
    source = Path("src/python_ingestion/load_to_postgres.py").read_text(encoding="utf-8")

    assert 'if_exists="append"' in source
    assert 'if_exists="replace"' not in source
    assert "TRUNCATE TABLE" in source
