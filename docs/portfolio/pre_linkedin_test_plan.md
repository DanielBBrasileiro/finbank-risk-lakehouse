# Pre-LinkedIn Release Test Plan

Run this plan from a fresh clone of the release candidate. The CI repeats the critical gates on Linux; the local pass verifies the reviewer experience on macOS or Linux.

## 1. Repository Hygiene

```bash
git fetch --all --prune
git status --short --branch
git branch -avv
git ls-files --others --exclude-standard
```

Pass criteria:

- `main` matches `origin/main` and the working tree is clean.
- No broken refs, duplicate files, secrets or generated data are tracked.
- The release tag points to the same commit displayed by GitHub Actions.

## 2. Clean Bootstrap

```bash
rm -rf .venv
cp .env.example .env
make bootstrap
make doctor
```

Pass criteria:

- The locked Python environment installs successfully.
- Python, dbt, Ruff, pytest, Cargo and required local tooling are detected.
- Terraform may be reported as optional for the default DuckDB demo.

## 3. Full Local Demo

```bash
make clean-demo
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
make test-all
make evidence-pack
```

Pass criteria:

- All five source contracts pass before publication.
- Bronze, Silver and Gold outputs are rebuilt from the current batch.
- All dbt models, snapshots and tests pass.
- Replaying the same event batch does not change suspicious-event totals.
- Python coverage remains at or above 70%.
- Ruff, SQLFluff, Rust tests and the Streamlit health check pass.
- The evidence artifact contains the release commit and SHA-256 hashes.

## 4. PostgreSQL Integration

Run when Docker is available:

```bash
make up
DB_TARGET=postgres make generate generate-macro-offline generate-cvm-offline validate
DB_TARGET=postgres make load load-audit dbt
make down
```

Confirm that primary keys survive loading, relationship tests pass and the read-only copilot role cannot mutate data. GitHub Actions runs this path with a PostgreSQL service container.

## 5. Manual Product Review

- Open all four dashboard tabs at desktop and mobile widths.
- Reconcile customer, account, exposure and suspicious-event totals with dbt marts.
- Confirm that missing optional data never exposes a stack trace.
- Ask one allowed analytical question and inspect its audit record.
- Submit destructive and multi-statement SQL and confirm rejection.
- Review screenshots for readable labels, no overlap and no sensitive data.
- Confirm that the README distinguishes integrated components from blueprints.

## 6. Publication Gate

Publish only when:

- CI and CodeQL are green on `main`.
- The protected `main` branch is clean and tagged `v1.0.0-portfolio`.
- The repository description, topics, license, screenshots and release are visible.
- The LinkedIn text makes no production-scale, real-data or deployed-cloud claim.
