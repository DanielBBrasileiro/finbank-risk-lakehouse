# FinBank Architecture

The local demo has one verified entry point: `AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local`.

```mermaid
flowchart LR
    S["Synthetic banking data"] --> R["Raw CSV"]
    B["BCB offline fixture"] --> R
    C["CVM offline fixture"] --> R
    R --> V["Rust data contracts"]
    V --> BR["Bronze immutable batch"]
    BR --> SI["Silver standardized Parquet"]
    SI --> GO["Gold analytical features"]
    V --> W["DuckDB or PostgreSQL raw schema"]
    W --> ST["dbt staging"]
    ST --> IN["dbt intermediate"]
    IN --> MA["Tested dbt marts"]
    MA --> DA["Streamlit risk dashboard"]
    MA --> AI["Analytical copilot"]
    E["Suspicious-event batch or Redpanda"] --> CO["Idempotent consumer"]
    CO --> W
    D["Docs, schemas and dbt metadata"] --> AI
    AI --> AU["Auditable decisions and SQL"]
    AU --> W
```

## Deployment Boundaries

| Component | Status | Evidence |
| --- | --- | --- |
| Python, Rust, local lakehouse, DuckDB, dbt, Streamlit | Integrated | `make demo-local` and CI |
| PostgreSQL | Integrated | CI service-container build |
| JSONL event replay | Integrated | Idempotency tests |
| Redpanda | Optional local integration | Docker Compose profile |
| Airflow | Optional local orchestration | Reproducible container and DAG smoke test |
| Dagster | Optional local orchestration | Importable asset definitions |
| AWS, Databricks, Snowflake | Blueprint | IaC, notebooks and DDL; no deployed-service claim |

Gold lakehouse artifacts and warehouse marts are two serving paths over the same validated source batch. They are not presented as a hidden cloud deployment.
