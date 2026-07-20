from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _compose(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_main_compose_pins_images_and_defines_healthchecks() -> None:
    compose = _compose("docker-compose.yml")

    for name, service in compose["services"].items():
        image = service["image"]
        assert ":" in image, f"{name} must use an explicit image tag"
        assert not image.endswith(":latest"), f"{name} uses a floating latest tag"
        assert service.get("healthcheck", {}).get("test"), f"{name} must define a healthcheck"


def test_airflow_compose_builds_an_immutable_project_image() -> None:
    compose = _compose("orchestration/airflow/docker-compose.yml")
    service = compose["services"]["airflow-standalone"]

    assert service["image"] == "finbank-airflow:3.1.0-local"
    assert service["build"]["dockerfile"] == "orchestration/airflow/Dockerfile"
    assert service["build"]["args"] == {
        "AIRFLOW_VERSION": "3.1.0",
        "PYTHON_VERSION": "3.12",
        "RUST_VERSION": "1.89.0",
    }
    assert service["healthcheck"]["test"]
    assert service["environment"]["DB_TARGET"] == "duckdb"


def test_airflow_uses_named_volumes_instead_of_host_project_mount() -> None:
    compose = _compose("orchestration/airflow/docker-compose.yml")
    volumes = compose["services"]["airflow-standalone"]["volumes"]

    assert all(not volume.startswith(".") and "${FINBANK_PROJECT_ROOT" not in volume for volume in volumes)
    assert {volume.split(":", 1)[0] for volume in volumes} == {
        "airflow_logs",
        "airflow_metadata",
        "finbank_data",
    }
