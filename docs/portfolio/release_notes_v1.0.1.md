# FinBank Risk Lakehouse v1.0.1 - Portfolio Release

## Highlights

- Aligns package metadata, public documentation and publication materials around the verified local-first scope.
- Uses one reusable Mermaid source for the main architecture diagram.
- Adds a reproducible validation record for release metrics.
- Standardizes visual assets for the README, LinkedIn carousel and release evidence.

## Verified Local Workflow

The default path generates synthetic banking records and offline BCB/CVM fixtures, validates source contracts with Rust, materializes Bronze/Silver/Gold Parquet layers, loads DuckDB, builds dbt marts, evaluates controlled analytical access and processes suspicious-event batches.

```bash
make clean-demo
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
make test-all
make evidence-pack
```

## Data Quality and Reliability

- Source contracts run before warehouse loading.
- Source-to-mart tests reconcile accounts, loans and transactions.
- Domain, relationship, uniqueness and business-rule checks run in dbt.
- Suspicious-event replay uses transaction identifiers to prevent duplicate aggregates.

## Analytical Products

The release includes customer exposure, daily transactions, account health, macro context and copilot-audit marts. Streamlit serves credit-risk, transaction-monitoring, account-health and analytical-access views.

## Controlled Analytical Access

The copilot is limited to documented context, allowlisted relations and one read-only SQL statement. Decisions, citations, SQL and responses are recorded. It is an analyst aid, not a regulated credit-decision model.

## CI and Security

GitHub Actions verifies Python, Rust, dbt, DuckDB, PostgreSQL, the Airflow image, Terraform formatting/validation and dependency security. CodeQL runs for Python changes and on `main`.

## Scope and Limitations

All customer and transaction records are synthetic. The project has not been validated at banking scale and does not claim production SLAs, real-customer processing, regulated-model validation or a deployed AWS, Databricks or Snowflake environment. Cloud assets remain blueprints.

## How to Run

```bash
git clone https://github.com/DanielBBrasileiro/finbank-risk-lakehouse.git
cd finbank-risk-lakehouse
cp .env.example .env
make bootstrap
make doctor
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
DB_TARGET=duckdb make run-dashboard
```

## Validation Evidence

- Release tag: `v1.0.1-portfolio`
- Release commit: target of the annotated tag; the exact SHA is recorded in the attached `evidence.md`.
- Validation date (UTC): `{{VALIDATION_DATE_UTC}}`
- Python tests: `{{PYTHON_TESTS_PASSED}}` passed
- Python coverage: `{{PYTHON_COVERAGE_PERCENT}}%`
- Rust tests: `{{RUST_TESTS_PASSED}}` passed
- dbt checks: `{{DBT_CHECKS_TOTAL}}` (`{{DBT_STATUS_SUMMARY}}`)
- Streaming replay: `{{STREAMING_REPLAY_STATUS}}`
- Streamlit smoke test: `{{DASHBOARD_SMOKE_STATUS}}`
- CI: `{{CI_STATUS}}`
- CodeQL: `{{CODEQL_STATUS}}`

