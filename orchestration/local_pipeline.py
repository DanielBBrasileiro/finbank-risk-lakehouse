from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(
    os.getenv("FINBANK_PROJECT_ROOT_IN_CONTAINER", Path(__file__).resolve().parents[1])
).resolve()
STEP_ORDER = ("sources", "contracts", "lakehouse", "warehouse", "marts", "ai_eval")


@dataclass(frozen=True)
class Command:
    argv: tuple[str, ...]
    cwd: Path


def _python() -> str:
    return os.getenv("FINBANK_PYTHON_BIN", sys.executable)


def _validator() -> str:
    return os.getenv(
        "FINBANK_VALIDATOR_BIN",
        str(PROJECT_ROOT / "src/rust_validator/target/release/finbank-validator"),
    )


def _dbt() -> str:
    configured = os.getenv("FINBANK_DBT_BIN")
    if configured:
        return configured
    return shutil.which("dbt") or str(Path(sys.executable).with_name("dbt"))


def pipeline_steps() -> dict[str, tuple[Command, ...]]:
    python = _python()
    validator = _validator()
    dbt = _dbt()
    raw = PROJECT_ROOT / "data/raw"
    schemas = PROJECT_ROOT / "schemas"

    validation_commands = tuple(
        Command(
            (validator, "validate", "--input", str(raw / f"{dataset}.csv"), "--schema", str(schemas / schema)),
            PROJECT_ROOT,
        )
        for dataset, schema in (
            ("customers", "customers_schema.json"),
            ("accounts", "accounts_schema.json"),
            ("transactions", "transactions_schema.json"),
            ("loans", "loans_schema.json"),
            ("cvm_funds", "cvm_funds_schema.json"),
        )
    )

    return {
        "sources": (
            Command((python, "src/python_ingestion/synthetic_generator.py"), PROJECT_ROOT),
            Command((python, "src/python_ingestion/bcb_extractor.py", "--offline-sample"), PROJECT_ROOT),
            Command((python, "src/python_ingestion/cvm_extractor.py", "--offline-sample"), PROJECT_ROOT),
        ),
        "contracts": validation_commands,
        "lakehouse": (
            Command((python, "src/python_ingestion/publish_bronze.py"), PROJECT_ROOT),
            Command((python, "-m", "src.lakehouse.local_layers"), PROJECT_ROOT),
        ),
        "warehouse": (
            Command((python, "src/python_ingestion/load_to_duckdb.py"), PROJECT_ROOT),
            Command((python, "src/python_ingestion/load_audit_logs.py"), PROJECT_ROOT),
        ),
        "marts": (
            Command((dbt, "build", "--profiles-dir", "."), PROJECT_ROOT / "dbt"),
        ),
        "ai_eval": (
            Command(
                (python, "-m", "src.ai_assistant.eval_runner", "--eval-file", "ai/evals/risk_copilot.yml"),
                PROJECT_ROOT,
            ),
        ),
    }


def orchestration_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    environment.setdefault("DB_TARGET", "duckdb")
    environment.setdefault("DBT_TARGET", "duckdb")
    environment.setdefault("DUCKDB_PATH", str(PROJECT_ROOT / "data/warehouse.duckdb"))
    environment.setdefault("AI_DEMO_MODE", "1")
    environment.setdefault("AI_AUDIT_PATH", str(PROJECT_ROOT / "data/ai_audit/copilot_audit.jsonl"))
    environment.setdefault("DBT_SEND_ANONYMOUS_USAGE_STATS", "false")
    return environment


def run_step(step_name: str) -> list[str]:
    steps = pipeline_steps()
    if step_name not in steps:
        raise ValueError(f"Unknown pipeline step: {step_name}")

    executed: list[str] = []
    environment = orchestration_environment()
    for command in steps[step_name]:
        command.cwd.mkdir(parents=True, exist_ok=True)
        printable = " ".join(command.argv)
        print(f"[{step_name}] {printable}", flush=True)
        subprocess.run(command.argv, cwd=command.cwd, env=environment, check=True)
        executed.append(printable)
    return executed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one reproducible FinBank orchestration step.")
    parser.add_argument("step", choices=STEP_ORDER)
    args = parser.parse_args(argv)
    run_step(args.step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
