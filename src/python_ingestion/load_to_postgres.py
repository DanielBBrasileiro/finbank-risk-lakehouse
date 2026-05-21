from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

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
]


def get_engine():
    user = os.getenv("POSTGRES_USER", "finbank")
    password = os.getenv("POSTGRES_PASSWORD", "finbank")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "finbank")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")


def load_csv(table_name: str, file_name: str) -> None:
    path = RAW_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}. Run synthetic_generator.py first.")

    df = pd.read_csv(path)
    engine = get_engine()

    df.to_sql(
        name=table_name,
        con=engine,
        schema="raw",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1_000,
    )
    print(f"Loaded raw.{table_name}: {len(df):,} rows")


def tables_to_load(*, raw_dir: Path = RAW_DIR) -> list[tuple[str, str]]:
    tables = list(CORE_TABLES)
    tables.extend((table_name, file_name) for table_name, file_name in OPTIONAL_TABLES if (raw_dir / file_name).exists())
    return tables


def main() -> None:
    for table_name, file_name in tables_to_load(raw_dir=RAW_DIR):
        load_csv(table_name, file_name)


if __name__ == "__main__":
    main()
