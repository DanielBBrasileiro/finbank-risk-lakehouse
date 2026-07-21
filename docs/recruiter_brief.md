# FinBank Risk Lakehouse - Project Brief

## Summary

FinBank follows banking data from ingestion to risk reporting. It covers credit exposure, delinquency, account health, suspicious transactions and analyst questions over the resulting marts.

The complete demo runs locally with synthetic data. PostgreSQL and the containerized Airflow path are checked in CI, while AWS, Snowflake and Databricks remain documented blueprints.

## Engineering Decisions

- Local path: synthetic banking data -> Rust validation -> DuckDB -> dbt marts -> dashboard -> AI evals.
- Local lakehouse path: raw CSV -> Bronze CSV/Parquet -> Silver standardized Parquet -> Gold risk feature artifacts.
- dbt owns transformations, tests, documentation, lineage and downstream exposures.
- Data contracts are enforced before warehouse loading through a Rust CLI.
- Dagster assets and a containerized Airflow DAG call the same pipeline commands instead of reimplementing business logic.
- The copilot uses local metadata, read-only SQL rules, JSONL audit records and deterministic evaluation cases.
- Cloud examples are isolated from the free local demo.

## Technical Stack

- Python, pandas, SQLAlchemy, requests
- Rust, clap, csv, serde
- Docker Compose, PostgreSQL, MinIO, Qdrant
- dbt Core and dbt-postgres
- Dagster OSS
- Apache Airflow optional local DAG
- Streamlit and Plotly
- Parquet/pyarrow local lakehouse artifacts
- AWS S3 Terraform blueprint
- Snowflake DDL
- Databricks/Spark/Delta notebook
- Analytical copilot with retrieval and SQL guardrails

## Discussion Notes

1. Why validation happens before warehouse loading.
2. How source-to-mart reconciliation catches incomplete or duplicated batches.
3. Why DuckDB is the default demo path and PostgreSQL remains part of CI.
4. How idempotency is maintained when suspicious-event batches are replayed.
5. Where the copilot is allowed to query and how rejected requests are audited.
6. Which changes would be required before operating the design in a managed cloud environment.

## Current Scope

The repository does not process real customer data and has not been validated for production scale, SLAs or regulated credit decisions. AWS, Snowflake and Databricks are design examples, not deployed environments.
