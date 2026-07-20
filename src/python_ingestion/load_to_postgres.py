from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Connection, create_engine, text

load_dotenv()

RAW_DIR = Path("data/raw")

CORE_TABLES = [
    ("customers", "customers.csv"),
    ("accounts", "accounts.csv"),
    ("transactions", "transactions.csv"),
    ("loans", "loans.csv"),
]
OPTIONAL_TABLES = [
    ("macro_indicators", "macro_indicators.csv"),
    ("cvm_funds", "cvm_funds.csv"),
]
TABLE_COLUMNS = {
    "customers": [
        "customer_id", "customer_name", "document_type", "segment", "state", "created_at", "internal_score"
    ],
    "accounts": ["account_id", "customer_id", "account_type", "opened_at", "status"],
    "transactions": [
        "transaction_id", "customer_id", "account_id", "transaction_date", "channel",
        "transaction_type", "amount", "is_suspicious",
    ],
    "loans": [
        "loan_id", "customer_id", "product_type", "origination_date", "maturity_date",
        "principal_amount", "outstanding_balance", "interest_rate", "days_past_due", "risk_rating",
    ],
    "macro_indicators": ["observation_date", "indicator_name", "series_id", "value"],
    "cvm_funds": ["cnpj", "fund_name", "fund_type", "status", "class_type", "net_worth"],
}


def get_engine():
    user = os.getenv("POSTGRES_USER", "finbank")
    password = os.getenv("POSTGRES_PASSWORD", "finbank")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "finbank")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")


def _read_csv(table_name: str, file_name: str, *, raw_dir: Path) -> pd.DataFrame:
    if table_name not in TABLE_COLUMNS:
        raise ValueError(f"Unsupported raw table: {table_name}")

    path = raw_dir / file_name
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}. Run synthetic_generator.py first.")

    df = pd.read_csv(path)
    expected = TABLE_COLUMNS[table_name]
    missing = sorted(set(expected) - set(df.columns))
    unexpected = sorted(set(df.columns) - set(expected))
    if missing or unexpected:
        raise ValueError(
            f"Column contract mismatch for raw.{table_name}: missing={missing}, unexpected={unexpected}"
        )
    return df[expected]


def _append_frame(connection: Connection, table_name: str, frame: pd.DataFrame) -> None:
    frame.to_sql(
        name=table_name,
        con=connection,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1_000,
    )


def load_csv(table_name: str, file_name: str, *, raw_dir: Path = RAW_DIR) -> None:
    """Replace one raw table's data without replacing its DDL definition."""
    frame = _read_csv(table_name, file_name, raw_dir=raw_dir)
    engine = get_engine()
    try:
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE TABLE raw.{table_name} CASCADE"))
            _append_frame(connection, table_name, frame)
    finally:
        engine.dispose()
    print(f"Loaded raw.{table_name}: {len(frame):,} rows")


def load_all(*, raw_dir: Path = RAW_DIR) -> None:
    """Atomically refresh all available raw tables while preserving constraints."""
    selected_tables = tables_to_load(raw_dir=raw_dir)
    frames = [
        (table_name, _read_csv(table_name, file_name, raw_dir=raw_dir))
        for table_name, file_name in selected_tables
    ]
    qualified_tables = ", ".join(f"raw.{table_name}" for table_name, _ in selected_tables)
    engine = get_engine()
    try:
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE TABLE {qualified_tables}"))
            for table_name, frame in frames:
                _append_frame(connection, table_name, frame)
                print(f"Loaded raw.{table_name}: {len(frame):,} rows")
    finally:
        engine.dispose()


def tables_to_load(*, raw_dir: Path = RAW_DIR) -> list[tuple[str, str]]:
    tables = list(CORE_TABLES)
    tables.extend((table_name, file_name) for table_name, file_name in OPTIONAL_TABLES if (raw_dir / file_name).exists())
    return tables


def main() -> None:
    load_all(raw_dir=RAW_DIR)


if __name__ == "__main__":
    main()
