# FinBank Recruiter Demo Script

## Local-first path

```bash
make doctor
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
make test-all
make evidence-pack
DB_TARGET=duckdb make run-dashboard
```

Talk track:

1. The platform starts with a banking risk problem, not a generic data stack.
2. The pipeline follows the data engineering lifecycle from source generation through serving.
3. Rust contracts reject invalid input before publication; dbt relationships, domains and reconciliations protect analytical outputs.
4. The event replay is idempotent, so rerunning a batch does not inflate suspicious-activity totals.
5. The copilot uses trusted context, read-only SQL policy and an auditable decision trail.
6. Cloud vendors are represented through IaC, DDL and runbooks while the public demo remains free.

## Docker warehouse path

```bash
make up
make load
make dbt
make run-dashboard
```

Use this path when Docker is running and the reviewer wants to inspect the PostgreSQL integration. The default reviewer path remains DuckDB because it has no service dependency.
