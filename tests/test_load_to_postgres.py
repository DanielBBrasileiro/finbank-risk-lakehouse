from pathlib import Path

from src.python_ingestion.load_to_postgres import tables_to_load


def test_tables_to_load_includes_macro_indicators_when_present(tmp_path: Path) -> None:
    (tmp_path / "macro_indicators.csv").write_text("observation_date,indicator_name,series_id,value\n", encoding="utf-8")

    tables = tables_to_load(raw_dir=tmp_path)

    assert ("macro_indicators", "macro_indicators.csv") in tables
