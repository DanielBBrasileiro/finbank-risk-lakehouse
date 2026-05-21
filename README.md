# FinBank Risk Lakehouse

Banking risk lakehouse and governed AI copilot portfolio project for international Data Engineering roles.

This repo simulates a financial institution data platform that monitors credit exposure, delinquency, suspicious transactions and data quality. It is designed to show practical engineering judgment: reproducible local pipelines, dbt analytics engineering, Rust data contracts, orchestration, cloud-ready infrastructure and responsible AI controls.

## What This Demonstrates

| Signal | Implementation |
| --- | --- |
| Data engineering | Python ingestion, Docker Compose, PostgreSQL, MinIO-style lake paths |
| Lakehouse design | Local Bronze/Silver/Gold layers with CSV and Parquet artifacts |
| Analytics engineering | dbt staging/intermediate/marts, tests, docs, exposures and macro context |
| Data quality | Rust CSV validator plus dbt business tests |
| Orchestration | Dagster asset graph plus optional Airflow DAG over the same Make targets |
| Public data | Offline BCB macro fixture, with live BCB extractor available when network is allowed |
| Streaming literacy | Redpanda service profile plus deterministic suspicious-transaction event batch |
| Cloud readiness | AWS S3 Terraform blueprint, Snowflake DDL, Databricks Bronze/Silver/Gold notebook |
| AI engineering | Governed offline copilot, retrieval, SQL guardrails, JSONL audit records and evals |
| Recruiter packaging | Architecture docs, AI governance notes and a one-page recruiter brief |

## Architecture

```text
Synthetic Banking Data + BCB Macroeconomic Extractor
        |
        v
Python ingestion -> Raw CSV / MinIO-style lake files
        |
        v
Local Bronze/Silver/Gold CSV + Parquet layers
        |
        v
Rust data contracts for schema, uniqueness and required fields
        |
        v
PostgreSQL raw schema
        |
        v
dbt staging -> intermediate -> marts
        |
        +--> Streamlit risk dashboard
        |
        +--> Governed AI Risk Copilot
             - retrieval over docs/dbt/schemas
             - read-only SQL guardrails
             - JSONL audit trail
             - deterministic offline evals
```

Cloud blueprint:

```text
Local raw files -> AWS S3 Bronze -> Databricks/Delta Silver-Gold -> Snowflake marts -> dbt docs/exposures
```

The cloud path is intentionally cost-aware. The public demo runs locally; AWS/Snowflake/Databricks assets are provided as optional blueprints or free-trial runbooks.

## Quick Start

```bash
git clone <your-repo-url>
cd finbank-risk-lakehouse-starter
cp .env.example .env
make bootstrap
make doctor
make generate
make generate-macro-offline
make validate
make publish-bronze
make build-lakehouse
```

If Docker Desktop is running:

```bash
make up
make load
make dbt
make run-dashboard
```

Fast local demo without paid cloud services:

```bash
AI_DEMO_MODE=1 make pipeline-local
make streaming-demo
make evidence-pack
```

For the governed AI demo with no external key:

```bash
AI_DEMO_MODE=1 make ai-eval
AI_DEMO_MODE=1 make run-dashboard
```

## Main Commands

| Command | Purpose |
| --- | --- |
| `make bootstrap` | Create `.venv` with `uv` and install dependencies |
| `make doctor` | Check critical local runtime dependencies and optional cloud tools |
| `make generate` | Generate synthetic customers, accounts, transactions and loans |
| `make generate-macro-offline` | Write a deterministic BCB-style macro fixture to `data/raw/macro_indicators.csv` |
| `make validate` | Build and run the Rust CSV data contracts |
| `make publish-bronze` | Copy validated CSVs into a local bronze batch |
| `make build-lakehouse` | Build local Bronze/Silver/Gold CSV/Parquet layers |
| `make load` | Load raw CSV files into PostgreSQL |
| `make dbt` | Run dbt models and tests |
| `make dbt-parse` | Parse dbt project without requiring a running database |
| `make dbt-docs` | Generate dbt documentation artifacts |
| `make pipeline` | Run generate -> validate -> load -> dbt |
| `make pipeline-local` | Run the no-paid-cloud path: generate -> macro fixture -> validate -> bronze -> lakehouse -> AI eval |
| `make test` | Run Python tests |
| `make lint` | Run Ruff |
| `make ai-eval` | Run deterministic AI copilot evals |
| `make streaming-demo` | Emit suspicious-transaction events as local JSONL |
| `make evidence-pack` | Generate `docs/portfolio/evidence.md` |
| `make airflow-test` | Compile-check the optional Airflow DAG |
| `make dagster` | Open the Dagster asset graph |

## Data Model

Core synthetic entities:

- `customers`: customer segment, state and internal credit score.
- `accounts`: account type, status and customer relationship.
- `transactions`: date, channel, type, amount and suspicious flag.
- `loans`: product, principal, outstanding balance, interest rate and days past due.

dbt marts:

- `analytics_marts.mart_customer_exposure`: customer-level credit exposure and derived portfolio status.
- `analytics_marts.mart_daily_transactions`: daily transaction monitoring by channel and type.
- `analytics_marts.mart_credit_macro_context`: latest macroeconomic context joined to portfolio exposure by status.

## Governed AI Copilot

The AI layer is intentionally constrained:

- offline deterministic mode works without API keys;
- retrieval reads local docs, dbt models and schema files;
- generated SQL is restricted to `SELECT` or `WITH`;
- only allowlisted schemas are accepted;
- destructive keywords and multi-statement SQL are blocked;
- row limits are enforced;
- optional audit JSONL can persist question, citations, guarded SQL and response through `AI_AUDIT_PATH`;
- evals run from `ai/evals/risk_copilot.yml`.

This lets the project show responsible AI usage rather than a generic chatbot.

## Cloud Blueprint

The repo includes cloud-ready artifacts without requiring paid usage:

- `infra/aws`: private S3 bucket with encryption, versioning, public-access block and lifecycle cleanup.
- `snowflake/ddl`: raw and mart DDL with governance comments.
- `databricks/notebooks`: Bronze-to-Silver Delta transformation pattern.
- `dbt/profiles.yml`: local Postgres target and extension point for Snowflake credentials.

## Reference Architecture Lens

The project uses the lifecycle framing from Joe Reis and Matt Housley, *Fundamentals of Data Engineering* (2022): source generation, ingestion, storage, transformation and serving, supported by undercurrents such as security, governance, DataOps, architecture, orchestration and software engineering.

That lens is visible in the repo rather than only in the prose: raw data is generated and ingested, local lakehouse storage is materialized, dbt transforms and tests the marts, Streamlit/AI serve downstream consumers, and the audit/doctor/evidence commands make DataOps and governance reviewable.

## Verification

Recently verified locally:

```text
make bootstrap
make test
make lint
make ai-eval
cargo build --manifest-path src/rust_validator/Cargo.toml --release
make generate
make generate-macro-offline
make validate
make publish-bronze
make build-lakehouse
cd dbt && ../.venv/bin/dbt parse --profiles-dir .
.venv/bin/python -c "from orchestration.dagster_defs import defs; print(type(defs).__name__)"
```

Docker was not running in the current environment, so `make load`, `make dbt` full build and dashboard verification require starting Docker Desktop first.

## Portfolio Narrative

This project is positioned for Data Engineering roles. The intended interview story is:

1. I translated a banking risk problem into a reproducible data platform.
2. I used dbt to make trusted marts, tests, documentation and downstream exposures explicit.
3. I added Rust data contracts for fast validation before loading raw data.
4. I built a local Bronze/Silver/Gold path so the lakehouse story is executable without paid cloud.
5. I designed the cloud path with AWS, Snowflake and Databricks while keeping the demo cost-free.
6. I used AI as a governed analytical assistant with retrieval, SQL safety, audits and evals.

See:

- `docs/recruiter_brief.md`
- `docs/ai_governance.md`
- `docs/cloud_blueprint.md`
- `docs/ai_engineering_log.md`
- `docs/references.md`
