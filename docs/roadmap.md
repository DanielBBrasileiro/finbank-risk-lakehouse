# Roadmap

## Sprint 1 - Professional local foundation

- [x] Generate synthetic banking data.
- [x] Validate raw files with Rust data contracts.
- [x] Add Python tests, Ruff and CI.
- [x] Add governed AI offline evals.
- [x] Add environment doctor for critical local dependencies.
- [x] Add local Bronze/Silver/Gold lakehouse artifacts.
- [ ] Start Docker Compose and run the full warehouse/dbt path.

## Sprint 2 - Data quality and analytics engineering

- [x] Compile Rust validator.
- [x] Validate CSV schema for customers, accounts, transactions and loans.
- [x] Add dbt mart documentation and exposures.
- [x] Add dbt business tests.
- [x] Add BCB macro context models.
- [ ] Generate and publish dbt docs screenshot.

## Sprint 3 - Public data

- [x] Add BCB extractor with deterministic offline sample.
- [x] Add CVM extractor.
- [x] Create macroeconomic staging tables.
- [x] Join macro features to credit portfolio.

## Sprint 4 - Cloud architecture

- [x] Create AWS S3 bucket blueprint with Terraform.
- [x] Document Bronze/Silver/Gold cloud path.
- [x] Add Snowflake raw and mart DDL.
- [x] Add optional Snowflake dbt profile target.
- [ ] Run Terraform validate on a machine with Terraform installed.

## Sprint 5 - Databricks

- [x] Create Databricks notebook.
- [x] Read Bronze data.
- [x] Create Silver data.
- [x] Create Gold features.

## Sprint 6 - Governed AI Risk Copilot

- [x] Add docs/dbt/schema retrieval corpus.
- [x] Add risk marts metadata to dbt schema docs.
- [x] Create controlled SQL assistant with guardrails.
- [x] Add deterministic AI evals.
- [x] Add audited question/SQL/response persistence.

## Sprint 7 - Recruiter packaging and orchestration

- [x] Add optional Airflow DAG over the same local Make targets.
- [x] Add suspicious-transaction event batch for streaming literacy.
- [x] Add evidence-pack generator.
- [ ] Capture dashboard and dbt docs screenshots for the public README.

## Sprint 8 - Phase 3: Polish and professionalize

- [x] Fix accounts gap: DDL, staging model, dbt tests.
- [x] Add mart_account_health with dbt tests and exposure.
- [x] Add account health to dashboard and copilot.
- [ ] Clean up process artifacts and dev dependencies.
- [ ] Final verification pass.
