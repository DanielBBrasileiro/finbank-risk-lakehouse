from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

from orchestration import local_pipeline

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_step_order_covers_the_operational_local_path() -> None:
    assert local_pipeline.STEP_ORDER == (
        "sources",
        "contracts",
        "lakehouse",
        "warehouse",
        "marts",
        "ai_eval",
    )
    assert tuple(local_pipeline.pipeline_steps()) == local_pipeline.STEP_ORDER


def test_pipeline_runner_uses_duckdb_defaults_and_checked_subprocesses(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []

    def fake_run(argv, *, cwd, env, check):
        calls.append({"argv": argv, "cwd": cwd, "env": env, "check": check})

    monkeypatch.delenv("DB_TARGET", raising=False)
    monkeypatch.delenv("DBT_TARGET", raising=False)
    monkeypatch.setattr(local_pipeline.subprocess, "run", fake_run)

    executed = local_pipeline.run_step("warehouse")

    assert len(executed) == 2
    assert all(call["check"] is True for call in calls)
    assert all(call["env"]["DB_TARGET"] == "duckdb" for call in calls)
    assert all(call["env"]["DBT_TARGET"] == "duckdb" for call in calls)
    assert calls[0]["argv"][-1] == "src/python_ingestion/load_to_duckdb.py"
    assert calls[1]["argv"][-1] == "src/python_ingestion/load_audit_logs.py"


def test_pipeline_runner_rejects_unknown_steps() -> None:
    with pytest.raises(ValueError, match="Unknown pipeline step"):
        local_pipeline.run_step("unknown")


def test_airflow_and_dagster_definitions_share_the_step_runner() -> None:
    airflow_dag = (ROOT / "orchestration/airflow/dags/finbank_local_pipeline.py").read_text(encoding="utf-8")
    dagster_defs = (ROOT / "orchestration/dagster_defs.py").read_text(encoding="utf-8")

    assert "python -m orchestration.local_pipeline" in airflow_dag
    assert "from orchestration.local_pipeline import STEP_ORDER" in airflow_dag
    assert "from orchestration.local_pipeline import run_step" in dagster_defs
    assert "make " not in airflow_dag


def test_orchestration_python_files_compile() -> None:
    for path in (
        ROOT / "orchestration/local_pipeline.py",
        ROOT / "orchestration/dagster_defs.py",
        ROOT / "orchestration/airflow/dags/finbank_local_pipeline.py",
    ):
        py_compile.compile(str(path), doraise=True)


def test_airflow_image_contains_runtime_and_compiled_validator() -> None:
    dockerfile = (ROOT / "orchestration/airflow/Dockerfile").read_text(encoding="utf-8")
    requirements = (ROOT / "orchestration/airflow/requirements.txt").read_text(encoding="utf-8")

    assert "FROM rust:${RUST_VERSION}-bookworm AS validator-builder" in dockerfile
    assert "FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}" in dockerfile
    assert "cargo build --locked --release" in dockerfile
    assert "COPY --from=validator-builder" in dockerfile
    assert all("==" in line for line in requirements.splitlines() if line.strip())
