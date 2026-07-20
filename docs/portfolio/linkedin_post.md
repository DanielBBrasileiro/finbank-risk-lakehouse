# LinkedIn Publication Copy

## Recommended Post

Construí o **FinBank Risk Lakehouse**, um projeto de engenharia de dados ponta a ponta para transformar dados bancários sintéticos em produtos confiáveis de monitoramento de risco.

O problema que quis resolver foi direto: como criar uma plataforma reproduzível em que exposição de crédito, inadimplência, saúde de contas e transações suspeitas possam ser analisadas com definições consistentes, linhagem e controles verificáveis?

O fluxo implementado conecta:

- ingestão em Python de dados sintéticos e fontes públicas do BCB/CVM;
- contratos tipados em Rust antes da publicação;
- camadas Bronze, Silver e Gold em Parquet;
- warehouse local em DuckDB e integração testada com PostgreSQL;
- transformações, snapshots, documentação e testes com dbt;
- processamento idempotente de eventos suspeitos;
- dashboard Streamlit com quatro visões analíticas;
- copiloto analítico governado, com SQL somente leitura, allowlist e trilha de auditoria;
- orquestração reutilizável por Make, Dagster e Airflow containerizado.

O principal aprendizado foi que um pipeline não se torna confiável apenas porque executa. Contratos, reconciliação, idempotência, observabilidade, limites de escopo e uma forma simples de reproduzir o ambiente também fazem parte do produto de dados.

O repositório inclui um demo local determinístico, testes Python com cobertura mínima de 70%, testes de contratos em Rust, 76 recursos validados no `dbt build`, integração PostgreSQL e gates de infraestrutura e segurança no GitHub Actions.

AWS, Databricks e Snowflake aparecem como blueprints de evolução. Não apresento esses componentes como ambientes implantados, nem o projeto como sistema bancário de produção. O objetivo é demonstrar decisões de arquitetura e engenharia de forma honesta, executável e auditável.

Código, arquitetura, plano de testes e evidências: [adicione aqui a URL da release]

#DataEngineering #AnalyticsEngineering #Python #Rust #dbt #PostgreSQL #DuckDB #Docker #Airflow #DataQuality

## Short Version

Publiquei o **FinBank Risk Lakehouse**, um projeto local-first de engenharia de dados para monitoramento de risco bancário com dados sintéticos.

Python e Rust cuidam da ingestão e dos contratos; Parquet implementa Bronze/Silver/Gold; DuckDB e PostgreSQL atendem o warehouse; dbt transforma e testa os produtos analíticos; Streamlit serve os achados; e um copiloto governado opera com SQL somente leitura e auditoria.

O repositório inclui demo determinístico, cobertura Python mínima de 70%, contratos Rust, 76 recursos validados no `dbt build`, replay idempotente e CI para DuckDB, PostgreSQL, Airflow, Terraform e segurança.

Os ativos AWS, Databricks e Snowflake são blueprints, não implantações declaradas. Projeto, evidências e plano de testes: [adicione aqui a URL da release]

#DataEngineering #dbt #Python #PostgreSQL #DataQuality

## Suggested Visual Order

1. Dashboard de risco de crédito.
2. Diagrama de arquitetura do README.
3. Linhagem do dbt.
4. Dashboard de governança do copiloto.
5. Resultado verde do GitHub Actions na release.
