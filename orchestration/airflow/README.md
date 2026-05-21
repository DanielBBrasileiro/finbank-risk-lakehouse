# Airflow Local Orchestration

This folder adds an optional Apache Airflow view of the same local-first FinBank workflow.

Airflow is included for recruiter familiarity and scheduler/DAG literacy. Dagster remains in the repo as the asset-oriented orchestration view. Both call the same Make targets so the project does not fork its business logic.

## Run

```bash
cp orchestration/airflow/.env.example orchestration/airflow/.env
docker compose --env-file orchestration/airflow/.env -f orchestration/airflow/docker-compose.yml up
```

Open `http://localhost:8080` and trigger `finbank_local_portfolio_pipeline`.

If Docker bind mounts from `Documents` fail on macOS File Provider paths, set `FINBANK_PROJECT_ROOT` in `.env` to a materialized copy outside `Documents`.
