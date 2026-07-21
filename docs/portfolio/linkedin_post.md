# LinkedIn Publication Copy

## Recommended English Post

Data projects should not end in a notebook.

I built **FinBank Risk Lakehouse**, a local-first data platform that follows banking data from ingestion to analyst-facing risk products.

The project addresses a practical challenge: keeping definitions of credit exposure, delinquency, account health and suspicious transactions consistent across the entire pipeline.

Some of the engineering decisions behind it:

- Python handles ingestion and deterministic data generation.
- Rust validates source contracts before warehouse loading.
- Parquet supports Bronze, Silver and Gold layers.
- DuckDB, PostgreSQL and dbt produce tested analytical marts.
- Event batches can be replayed without duplicating suspicious-activity results.
- A Streamlit application serves the risk products.
- The analytical copilot is restricted to read-only SQL, allowlisted relations and auditable interactions.

The repository also includes automated checks for Python, Rust, dbt, DuckDB, PostgreSQL, Airflow, Terraform, dependency security and CodeQL.

Final release validation: 80 Python tests passed with 70.68% source coverage, 2 Rust tests passed, and 78 dbt checks completed (62 passed tests, 14 successful resources and 2 no-op exposures).

The default workflow uses synthetic data and runs locally without paid cloud services. AWS, Databricks and Snowflake are documented as evolution paths rather than deployed environments.

Repository and architecture:

https://github.com/DanielBBrasileiro/finbank-risk-lakehouse

Which part would you review first: data contracts, reconciliation, idempotency or analytical access controls?

#DataEngineering #AnalyticsEngineering #dbt #Python #FinancialServices

## Portuguese Version

Projetos de dados não deveriam terminar em um notebook.

Construí o **FinBank Risk Lakehouse**, uma plataforma local-first que acompanha dados bancários desde a ingestão até produtos analíticos de risco usados por analistas.

O projeto trata um problema prático: manter consistentes, ao longo de todo o pipeline, as definições de exposição de crédito, inadimplência, saúde de contas e transações suspeitas.

Algumas decisões de engenharia do projeto:

- Python realiza a ingestão e a geração determinística dos dados.
- Rust valida os contratos de origem antes da carga no warehouse.
- Parquet sustenta as camadas Bronze, Silver e Gold.
- DuckDB, PostgreSQL e dbt produzem marts analíticos testados.
- Lotes de eventos podem ser reprocessados sem duplicar resultados de atividade suspeita.
- Uma aplicação Streamlit apresenta os produtos de risco.
- O copiloto analítico é limitado a SQL somente leitura, relações permitidas e interações auditáveis.

O repositório também inclui verificações automatizadas para Python, Rust, dbt, DuckDB, PostgreSQL, Airflow, Terraform, segurança de dependências e CodeQL.

Validação final da release: 80 testes Python aprovados, cobertura de código-fonte de 70,68%, 2 testes Rust aprovados e 78 verificações dbt concluídas (62 testes aprovados, 14 recursos executados com sucesso e 2 exposições sem operação).

O fluxo padrão usa dados sintéticos e roda localmente sem serviços cloud pagos. AWS, Databricks e Snowflake estão documentados como caminhos de evolução, não como ambientes implantados.

Repositório e arquitetura:

https://github.com/DanielBBrasileiro/finbank-risk-lakehouse

Qual parte você revisaria primeiro: contratos de dados, reconciliação, idempotência ou controles de acesso analítico?

#DataEngineering #AnalyticsEngineering #dbt #Python #FinancialServices

## Short English Version

I built **FinBank Risk Lakehouse**, a local-first project that follows synthetic banking data from Python ingestion and Rust contracts to tested dbt marts, Streamlit risk products and controlled analytical access.

The pipeline checks source contracts before loading, reconciles source and mart totals, and replays suspicious-event batches without duplication. DuckDB is the default local path; PostgreSQL is verified in CI. Cloud assets remain documented blueprints.

Repository: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse

#DataEngineering #dbt #Python #FinancialServices

## Publication Notes

- Repository: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse
- Release: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse/releases/tag/v1.0.1-portfolio
- Release commit: target of `v1.0.1-portfolio`; the exact SHA is included in the attached evidence pack.
- Tag: `v1.0.1-portfolio`
- Validation date (UTC): `2026-07-21`
- Python tests: `80` passed
- Python coverage: `70.68%`
- Rust tests: `2` passed
- dbt checks: `78` (`62 pass`, `14 success`, `2 no-op`)
- Streaming replay: passed
- Streamlit smoke test: passed
- CI: green on the tagged release commit
- CodeQL: green on the tagged release commit
- Preferred language: publish the English version and keep the Portuguese version for a follow-up comment or repost.
- Suggested attachments: architecture overview, dashboard, dbt lineage, copilot controls and GitHub Actions summary.
