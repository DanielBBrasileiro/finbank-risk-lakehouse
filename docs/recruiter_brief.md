# FinBank Risk Lakehouse - Recruiter Brief

## Positioning

This is a Data Engineering portfolio case built around a realistic banking risk problem: creating a trusted platform for credit exposure, delinquency monitoring, suspicious transaction analysis and AI-assisted risk questions.

The project is intentionally recruiter-friendly: it can run locally, includes tests and CI, and also shows how the same design maps to AWS, Snowflake and Databricks.

## What Makes It Professional

- End-to-end local path: synthetic banking data -> Rust validation -> DuckDB/PostgreSQL -> dbt marts -> dashboard -> AI evals.
- Local lakehouse path: raw CSV -> Bronze CSV/Parquet -> Silver standardized Parquet -> Gold risk feature artifacts.
- dbt is used for more than transformations: tests, documentation, lineage and downstream exposures are included.
- Data contracts are enforced before warehouse loading through a Rust CLI.
- Dagster assets and an optional containerized Airflow DAG demonstrate orchestration without changing pipeline business logic.
- AI is governed: offline mode, retrieval over trusted metadata, SQL guardrails, audit JSONL and deterministic evaluation cases.
- Cloud is cost-aware: Terraform and DDL are present, but the public demo does not require paid resources.

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
- Governed AI copilot with retrieval and SQL guardrails

## Interview Talking Points

1. The business problem is not generic analytics; it connects data engineering to credit risk and portfolio monitoring.
2. The pipeline separates raw ingestion, validation, warehouse loading, transformation and consumption.
3. The local-first design keeps the demo reproducible while cloud artifacts show production thinking.
4. The AI layer is a controlled analyst copilot, not an unrestricted chatbot.
5. The repo shows engineering discipline: automated tests, linting, CI, Makefile commands and documented tradeoffs.
6. The architecture follows Reis and Housley's lifecycle framing: generation, ingestion, storage, transformation and serving, with governance/DataOps undercurrents made explicit.

## Current Scope

The repo is a verified local-first portfolio system. It does not claim to be a production bank platform. AWS, Snowflake and Databricks remain explicit blueprints, and production scale, SLAs and regulated-model validation are outside this public demonstration.
