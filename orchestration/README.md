# Local Orchestration

The operational orchestration path in this repository is local and uses deterministic sample data, the Rust
validator, the local lakehouse writer, DuckDB, dbt, and the offline AI evaluation. Airflow and Dagster call the
same step runner in `orchestration/local_pipeline.py`; business logic remains in the application modules.

## Supported modes

- **Airflow container:** reproducible local scheduler and web UI, built from `orchestration/airflow/Dockerfile`.
- **Dagster local process:** asset-oriented view that uses the repository's installed Python environment.
- **AWS:** Terraform blueprint only. It is not required or automatically provisioned by either orchestrator.

The orchestrated path does not claim production scheduling, managed cloud deployment, or resilient event
streaming. Those concerns require external credentials, state storage, monitoring, and deployment controls that
are intentionally outside this local portfolio environment.
