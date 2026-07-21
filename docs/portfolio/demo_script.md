# FinBank Demo Script

## Local-first path

```bash
make doctor
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
make test-all
make evidence-pack
DB_TARGET=duckdb make run-dashboard
```

Points to cover:

1. The pipeline starts from the reporting needs in `docs/business_context.md`.
2. The local command runs source generation, validation, storage, transformation and serving.
3. Rust contracts reject invalid input before publication; dbt relationships, domains and reconciliations protect analytical outputs.
4. The event replay is idempotent, so rerunning a batch does not inflate suspicious-activity totals.
5. The copilot uses repository metadata, read-only SQL rules and an audit trail.
6. Cloud examples are kept outside the local execution path.

Close by stating the boundary: all customer and transaction records are synthetic; the project has no banking-scale validation, production SLA, regulated credit-decision claim or deployed managed-cloud environment.

## Docker warehouse path

```bash
make up
make load
make dbt
make run-dashboard
```

Use this path when Docker is running and PostgreSQL is part of the demonstration. DuckDB remains the default because it has no service dependency.
