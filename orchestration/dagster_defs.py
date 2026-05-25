import os
import subprocess
from pathlib import Path

from dagster import AssetExecutionContext, Definitions, asset


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


@asset(group_name="bronze")
def synthetic_raw_files(context: AssetExecutionContext) -> list[str]:
    _run(["python", "src/python_ingestion/synthetic_generator.py"])
    files = sorted(str(path.relative_to(PROJECT_ROOT)) for path in (PROJECT_ROOT / "data/raw").glob("*.csv"))
    context.add_output_metadata({"files": files, "file_count": len(files)})
    return files


@asset(group_name="quality", deps=[synthetic_raw_files])
def rust_csv_validation(context: AssetExecutionContext) -> str:
    output = _run(
        [
            "cargo",
            "run",
            "--manifest-path",
            "src/rust_validator/Cargo.toml",
            "--",
            "validate",
            "--input",
            "data/raw/transactions.csv",
            "--schema",
            "schemas/transactions_schema.json",
        ]
    )
    context.add_output_metadata({"validator_output": output})
    return output


@asset(group_name="bronze", deps=[rust_csv_validation])
def local_bronze_batch(context: AssetExecutionContext) -> str:
    output = _run(["python", "src/python_ingestion/publish_bronze.py"])
    context.add_output_metadata({"publisher_output": output})
    return output


@asset(group_name="warehouse", deps=[local_bronze_batch])
def warehouse_raw_tables(context: AssetExecutionContext) -> str:
    db_target = os.getenv("DB_TARGET", "").lower()
    if db_target == "duckdb":
        output = _run(["python", "src/python_ingestion/load_to_duckdb.py"])
    else:
        output = _run(["python", "src/python_ingestion/load_to_postgres.py"])
    context.add_output_metadata({"loader_output": output, "db_target": db_target or "postgres"})
    return output


@asset(group_name="analytics", deps=[warehouse_raw_tables])
def dbt_risk_marts(context: AssetExecutionContext) -> str:
    output = _run(["dbt", "build", "--profiles-dir", "."], cwd=PROJECT_ROOT / "dbt")
    context.add_output_metadata({"dbt_output_tail": output[-2000:]})
    return output


@asset(group_name="ai", deps=[dbt_risk_marts])
def governed_ai_eval(context: AssetExecutionContext) -> str:
    output = _run(["python", "-m", "src.ai_assistant.eval_runner", "--eval-file", "ai/evals/risk_copilot.yml"])
    context.add_output_metadata({"eval_output": output})
    return output


defs = Definitions(
    assets=[
        synthetic_raw_files,
        rust_csv_validation,
        local_bronze_batch,
        warehouse_raw_tables,
        dbt_risk_marts,
        governed_ai_eval,
    ]
)

