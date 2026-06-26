from pathlib import Path

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
    assert "requirements-dev.txt" in ci_workflow


def test_test_target_runs_test_files_individually() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    ci_workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "for test_file in tests/test_*.py" in makefile
    assert "$(PYTHON) -m pytest $$test_file -q" in makefile
    assert "make test" in ci_workflow


def test_streaming_demo_uses_local_duckdb() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "DB_TARGET=duckdb DUCKDB_PATH=data/warehouse.duckdb $(PYTHON) -m src.streaming.consumer" in makefile
