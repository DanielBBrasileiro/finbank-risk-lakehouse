# Pre-LinkedIn Publication Test Plan

Use this checklist before linking the repository in a LinkedIn post.

## 1. Repository Hygiene

Run:

```bash
git fetch --all --prune
git branch -avv
git status --short --branch
git ls-files --others --exclude-standard
```

Expected:

- `main` points to the latest remote commit.
- No broken local refs such as `.git/refs/heads/main 2`.
- No duplicate files with suffix ` 2`.
- No untracked personal files except intentionally ignored local artifacts.

## 2. Environment Bootstrap

Run:

```bash
rm -rf .venv
make bootstrap
make doctor
```

Expected:

- Python 3.12 environment is created.
- Runtime and dev dependencies install from `requirements.txt` and `requirements-dev.txt`.
- `pytest`, `ruff`, `dbt`, `pyarrow`, and `cargo` pass in `make doctor`.
- Terraform can be `WARN` because it is optional for the local demo.

## 3. Core Quality Gates

Run:

```bash
make lint
make test
cargo build --manifest-path src/rust_validator/Cargo.toml --release
make dbt-parse
AI_DEMO_MODE=1 make ai-eval
```

Expected:

- Ruff reports `All checks passed`.
- Every `tests/test_*.py` file passes.
- Rust validator builds in release mode.
- dbt parses with the local profile.
- Governed AI evals pass in deterministic offline mode.

## 4. Local Demo Evidence

Run:

```bash
AI_DEMO_MODE=1 make pipeline-local
make streaming-demo
make evidence-pack
```

Expected:

- Synthetic data is generated.
- Rust contracts validate raw CSV files.
- Bronze/Silver/Gold local lakehouse artifacts are built.
- AI evals pass.
- Streaming fallback writes and consumes local JSONL events.
- `docs/portfolio/evidence.md` shows the current branch and commit.

## 5. Optional Docker Warehouse Path

Run only if Docker Desktop is running:

```bash
make up
make load
make dbt
make run-dashboard
```

Expected:

- PostgreSQL loads raw tables.
- dbt build succeeds.
- Streamlit dashboard opens and matches the screenshots in `docs/portfolio/screenshots/`.

## 6. Publication Gate

Publish only after:

- GitHub Actions is green on the commit linked from LinkedIn.
- `docs/portfolio/evidence.md` was regenerated after the latest commit.
- The README Quick Start still matches the tested commands.
- No generated, sensitive, personal, or duplicate local files are staged.
# Pre-LinkedIn Release Test Plan

Run this plan from a fresh clone of the release candidate, preferably on Ubuntu and once on macOS.

## Automated Release Gates

```bash
cp .env.example .env
make bootstrap
make doctor
make clean-demo
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
make test-all
make evidence-pack
```

Expected results:

- Python tests, 70% full-source coverage and Ruff pass.
- Rust tests and all five input contracts pass.
- DuckDB raw tables and every dbt model/test build successfully.
- Replaying the same event batch leaves suspicious-event totals unchanged.
- Streamlit health endpoint returns `ok`.
- The evidence pack references the release commit and contains SHA-256 hashes.

## PostgreSQL Integration

```bash
make up
DB_TARGET=postgres make generate generate-macro-offline generate-cvm-offline validate
DB_TARGET=postgres make load load-audit dbt
make down
```

Confirm that primary keys remain present after loading and that dbt relationship tests pass.

## Manual Product Review

- Open all four dashboard tabs at desktop and mobile widths.
- Confirm that no raw exception or database stack trace is displayed.
- Reconcile customer count and exposure totals with dbt marts.
- Ask one allowed analytical question and confirm its audit record.
- Submit destructive and multi-statement SQL prompts and confirm rejection.
- Review screenshots for readable labels, no overlap and no sensitive data.
- Confirm the README distinguishes integrated components from blueprints.

## GitHub Release Gate

- Required CI and CodeQL checks are green on the release commit.
- `main` is protected and the working tree is clean.
- Repository description, topics, license and screenshots are visible.
- `v1.0.0-portfolio` points to the verified commit.
- The LinkedIn copy makes no production-scale or deployed-cloud claim.
