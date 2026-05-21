# References

## Core Book

- Joe Reis and Matt Housley, *Fundamentals of Data Engineering*, O'Reilly, 2022.

How this repo uses it:

- Lifecycle: generation, ingestion, storage, transformation and serving are represented by synthetic/BCB ingestion, local lakehouse layers, dbt marts, dashboard and AI copilot.
- Undercurrents: security, governance, DataOps, architecture, orchestration and software engineering are represented by SQL guardrails, audit records, tests, doctor checks, Dagster/Airflow and CI.
- Batch versus streaming: the default path stays batch because the portfolio risk use case does not require millisecond decisions; suspicious-transaction events provide a small streaming-literacy demo.
- FinOps: AWS, Snowflake and Databricks are optional readiness paths while the reviewer demo stays local and free.

## Official Tool References

- dbt Core: https://github.com/dbt-labs/dbt-core
- Apache Airflow Docker Compose quick start: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
- AWS Free Tier: https://aws.amazon.com/free/
- Snowflake trial accounts: https://docs.snowflake.com/en/user-guide/admin-trial-account
- Databricks Free Edition: https://docs.databricks.com/aws/en/getting-started/ce-migration
- Redpanda quick start: https://docs.redpanda.com/current/get-started/quick-start/
