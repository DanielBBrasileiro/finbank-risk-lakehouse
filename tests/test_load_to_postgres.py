from pathlib import Path

import pandas as pd
import pytest

from src.python_ingestion import load_to_postgres
from src.python_ingestion.load_to_postgres import _read_csv, load_all, load_csv, tables_to_load


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement) -> None:
        self.statements.append(str(statement))


class FakeTransaction:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def __enter__(self) -> FakeConnection:
        return self.connection

    def __exit__(self, *_args) -> None:
        return None


class FakeEngine:
    def __init__(self) -> None:
        self.connection = FakeConnection()
        self.disposed = False

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self.connection)

    def dispose(self) -> None:
        self.disposed = True


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


def test_load_all_refreshes_core_tables_in_one_transaction(tmp_path: Path, monkeypatch) -> None:
    engine = FakeEngine()
    appended: list[str] = []
    monkeypatch.setattr(load_to_postgres, "get_engine", lambda: engine)
    monkeypatch.setattr(
        load_to_postgres,
        "_read_csv",
        lambda table_name, _file_name, raw_dir: pd.DataFrame([{"table": table_name}]),
    )
    monkeypatch.setattr(
        load_to_postgres,
        "_append_frame",
        lambda _connection, table_name, _frame: appended.append(table_name),
    )

    load_all(raw_dir=tmp_path)

    assert appended == ["customers", "accounts", "transactions", "loans"]
    assert "TRUNCATE TABLE raw.customers, raw.accounts, raw.transactions, raw.loans" in engine.connection.statements[0]
    assert engine.disposed is True


def test_load_csv_truncates_without_replacing_table(tmp_path: Path, monkeypatch) -> None:
    engine = FakeEngine()
    appended: list[str] = []
    monkeypatch.setattr(load_to_postgres, "get_engine", lambda: engine)
    monkeypatch.setattr(
        load_to_postgres,
        "_read_csv",
        lambda *_args, **_kwargs: pd.DataFrame([{"customer_id": "c1"}]),
    )
    monkeypatch.setattr(
        load_to_postgres,
        "_append_frame",
        lambda _connection, table_name, _frame: appended.append(table_name),
    )

    load_csv("customers", "customers.csv", raw_dir=tmp_path)

    assert appended == ["customers"]
    assert engine.connection.statements == ["TRUNCATE TABLE raw.customers CASCADE"]
    assert engine.disposed is True


def test_get_engine_uses_configured_postgres_credentials(monkeypatch) -> None:
    observed = {}
    sentinel = object()
    monkeypatch.setenv("POSTGRES_USER", "reader")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("POSTGRES_HOST", "db")
    monkeypatch.setenv("POSTGRES_PORT", "5544")
    monkeypatch.setenv("POSTGRES_DB", "risk")

    def fake_create_engine(url: str):
        observed["url"] = url
        return sentinel

    monkeypatch.setattr(load_to_postgres, "create_engine", fake_create_engine)

    result = load_to_postgres.get_engine()

    assert result is sentinel
    assert observed["url"] == "postgresql+psycopg2://reader:secret@db:5544/risk"


def test_read_csv_rejects_unsupported_or_missing_table(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported raw table"):
        _read_csv("unknown", "unknown.csv", raw_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="customers.csv"):
        _read_csv("customers", "customers.csv", raw_dir=tmp_path)
