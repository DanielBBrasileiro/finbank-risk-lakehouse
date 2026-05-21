# FinBank Recruiter Demo Script

## Local-first path

```bash
make doctor
AI_DEMO_MODE=1 make pipeline-local
make streaming-demo
make dbt-parse
make evidence-pack
```

Talk track:

1. The platform starts with a banking risk problem, not a generic data stack.
2. The pipeline follows the data engineering lifecycle from source generation through serving.
3. Rust contracts and dbt tests catch quality issues before data reaches the dashboard or copilot.
4. Airflow and Dagster are both present, but they call the same commands to avoid duplicated logic.
5. Cloud vendors are represented through IaC, DDL and runbooks while the public demo remains free.

## Docker warehouse path

```bash
make up
make load
make dbt
make run-dashboard
```

Use this path when Docker Desktop is running and the reviewer wants to inspect the PostgreSQL/dbt/Streamlit experience.
