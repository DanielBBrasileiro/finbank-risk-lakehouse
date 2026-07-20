from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_installs_shared_dev_requirements() -> None:
    requirements_dev = PROJECT_ROOT / "requirements-dev.txt"
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    ci_workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert requirements_dev.exists()
    dev_requirements = requirements_dev.read_text(encoding="utf-8")

    assert "pytest==9.0.2" in dev_requirements
    assert "ruff==0.14.6" in dev_requirements
    assert "requirements-dev.txt" in makefile
    assert "run: make bootstrap" in ci_workflow
    assert "run: make lint" in ci_workflow
    assert "run: make dbt-parse" in ci_workflow


def test_test_target_runs_test_files_individually() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    ci_workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "for test_file in tests/test_*.py" in makefile
    assert "$(PYTHON) -m pytest $$test_file -q" in makefile
    assert "make test" in ci_workflow


def test_streaming_demo_uses_local_duckdb() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "DB_TARGET=duckdb DUCKDB_PATH=data/warehouse.duckdb $(PYTHON) -m src.streaming.consumer" in makefile


def test_duckdb_dbt_target_is_serial_for_stable_ci() -> None:
    profiles = yaml.safe_load((PROJECT_ROOT / "dbt" / "profiles.yml").read_text(encoding="utf-8"))

    duckdb = profiles["finbank_postgres"]["outputs"]["duckdb"]
    assert duckdb["threads"] == 1
