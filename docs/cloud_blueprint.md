# Cloud Blueprint

## Principle

The public portfolio demo is local-first and cost-free. Cloud artifacts show that the project can be moved to a modern stack without requiring paid infrastructure for every reviewer.

This follows the FinOps emphasis in Reis and Housley: cost is an architecture concern, not a cleanup task after the platform is already running.

## AWS

`infra/aws` defines a private S3 bucket intended for lakehouse object storage:

- bronze raw files;
- silver cleaned files;
- gold analytical features;
- encryption, versioning and public access block;
- lifecycle cleanup for short-lived demos.

Validation path:

```bash
cd infra/aws
terraform init
terraform fmt
terraform validate
terraform plan -var="bucket_name=<globally-unique-demo-bucket>"
```

`terraform apply` is optional and should only be used with a deliberate budget.

## Snowflake

`snowflake/ddl/create_raw_tables.sql` creates the `FINBANK` database, raw schemas and mart table definitions. The dbt local profile uses PostgreSQL by default; `dbt/profiles.yml` also includes an optional Snowflake target controlled by environment variables when a trial account is available.

## Databricks

`databricks/notebooks/bronze_to_silver.py` demonstrates the Bronze-to-Silver path with Spark and Delta. For the two-week portfolio version, this remains a blueprint unless a free trial workspace is available.

## Cost Guardrails

- Keep local demo as the default path.
- Prefer `terraform plan` over `apply` in public walkthroughs.
- Use lifecycle cleanup for demo S3 data.
- Do not store credentials in the repo.
- Document optional cloud execution honestly in README and LinkedIn posts.
- Treat AWS, Snowflake and Databricks as optional proof-of-readiness paths, not requirements for a reviewer to run the portfolio.
