# LinkedIn Publication Copy

## Recommended Post

Concluí uma primeira versão do **FinBank Risk Lakehouse**, projeto em que acompanho dados bancários desde a ingestão até o dashboard de risco.

Usei dados sintéticos para trabalhar um problema concreto: manter exposição de crédito, inadimplência, saúde de contas e transações suspeitas com definições consistentes ao longo de todo o pipeline.

O fluxo principal ficou assim:

**Python e Rust** para ingestão e validação dos contratos; **Parquet** nas camadas Bronze, Silver e Gold; **DuckDB/PostgreSQL e dbt** no warehouse; e **Streamlit** na apresentação dos dados. Também implementei replay idempotente de eventos e um copiloto analítico limitado a SQL somente leitura, com allowlist e registro das interações.

Uma parte importante do trabalho foi testar as fronteiras entre essas etapas. O pipeline rejeita lotes inválidos antes da carga, reconcilia os totais entre origem e marts e evita duplicação quando um lote de eventos é reprocessado.

O repositório pode ser executado localmente sem serviços pagos. A release passou por 77 testes Python, 70,68% de cobertura, testes Rust e 78 verificações do dbt, além dos jobs de DuckDB, PostgreSQL, Airflow, Terraform e segurança no GitHub Actions.

AWS, Databricks e Snowflake estão no projeto como caminhos de evolução, não como ambientes já implantados.

Código, arquitetura e instruções para executar: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse

#DataEngineering #AnalyticsEngineering #Python #dbt #DuckDB #PostgreSQL

## Short Version

Concluí a primeira versão do **FinBank Risk Lakehouse**, um projeto de engenharia de dados para monitoramento de risco bancário com dados sintéticos.

Python e Rust cuidam da ingestão e dos contratos; Parquet implementa Bronze/Silver/Gold; DuckDB, PostgreSQL e dbt atendem o warehouse; e Streamlit apresenta os resultados. O projeto também inclui replay idempotente de eventos e um copiloto limitado a SQL somente leitura.

O fluxo pode ser reproduzido localmente e passou por 77 testes Python, testes Rust e 78 verificações do dbt, além do CI para DuckDB, PostgreSQL, Airflow, Terraform e segurança.

Projeto e instruções: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse

#DataEngineering #dbt #Python #PostgreSQL #DataQuality

## Suggested Visual Order

1. Dashboard de risco de crédito.
2. Diagrama de arquitetura do README.
3. Linhagem do dbt.
4. Dashboard de governança do copiloto.
5. Resultado verde do GitHub Actions na release.
