# Airflow Local Orchestration

This folder provides an operational local Apache Airflow view of the deterministic FinBank batch workflow.

The image contains the required Python packages, dbt adapters, project source, and a compiled Rust validator. It
does not depend on a host `.venv`, Cargo installation, or project bind mount. Airflow and Dagster both call
`orchestration/local_pipeline.py`, so their execution order stays aligned.

## Run

```bash
cp orchestration/airflow/.env.example orchestration/airflow/.env
docker compose --env-file orchestration/airflow/.env -f orchestration/airflow/docker-compose.yml up
```

Open `http://localhost:8080` and trigger `finbank_local_portfolio_pipeline`.

The DAG runs deterministic sources, Rust contracts, Bronze/Silver/Gold materialization, DuckDB loading, `dbt
build`, and offline AI evaluation. Generated data and Airflow metadata use named Docker volumes.

This is a single-container local demonstration. It does not represent a production Airflow deployment: there is
no distributed executor, external metadata database, remote log store, secrets backend, or cloud deployment.

To rebuild after source changes:

```bash
docker compose -f orchestration/airflow/docker-compose.yml up --build
```
