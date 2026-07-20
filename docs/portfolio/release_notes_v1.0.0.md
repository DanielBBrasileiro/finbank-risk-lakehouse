# FinBank Risk Lakehouse v1.0.0 Portfolio Release

This release establishes a reproducible, local-first banking risk data platform built exclusively with synthetic and public fixture data.

## Highlights

- Typed Rust contracts protect five source datasets before publication.
- Python materializes Bronze, Silver and Gold Parquet layers from standardized data.
- DuckDB and PostgreSQL warehouse paths feed tested dbt data products.
- Suspicious-event consumption is idempotent under batch replay.
- Streamlit serves credit, transaction, account and AI governance views.
- The analytical copilot enforces retrieval, schema and read-only SQL boundaries.
- Make, Dagster and containerized Airflow reuse the same executable pipeline.
- CI verifies quality, full DuckDB E2E, PostgreSQL integration, Terraform, the Airflow image and dependency security.

## Verification

The release gate requires the full local demo, at least 70% Python source coverage, Rust unit and data-contract tests, a complete dbt build, replay idempotency, dashboard health, PostgreSQL integration and green GitHub Actions checks.

## Scope

AWS, Databricks and Snowflake assets are architecture blueprints. This release does not claim managed-cloud deployment, real banking data, production scale, SLAs, regulated-model validation or causal credit-risk modeling.
