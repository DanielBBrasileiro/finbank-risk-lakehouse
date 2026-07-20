# Contributing

## Local Setup

```bash
cp .env.example .env
make bootstrap
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
make test-all
```

Create a focused branch, keep generated data and credentials out of Git, and add tests for behavioral changes. Pull requests must explain the business impact, validation performed and any architecture/documentation changes.

## Pull Request Gate

- Python tests, Ruff and Rust tests pass.
- DuckDB E2E and dbt build pass.
- Streaming changes include replay/idempotency coverage.
- Dashboard changes include a smoke test and visual review.
- New claims are supported by executable evidence.
- Cloud-only examples are labelled as blueprints unless deployed and verified.
