.PHONY: up down install bootstrap doctor generate generate-macro-offline publish-bronze build-lakehouse load validate dbt dbt-parse dbt-docs pipeline pipeline-local warehouse-local test lint ai-eval dagster run-dashboard rust-build rust-validate streaming-demo evidence-pack airflow-test demo

PYTHON ?= .venv/bin/python
DBT ?= .venv/bin/dbt
RUFF ?= .venv/bin/ruff
STREAMLIT ?= .venv/bin/streamlit
DAGSTER ?= .venv/bin/dagster
RUST_VALIDATOR ?= src/rust_validator/target/release/finbank-validator

up:
	docker compose up -d

down:
	docker compose down

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

bootstrap:
	uv venv --allow-existing .venv
	uv pip install -r requirements.txt
	uv pip install -r requirements-dev.txt

doctor:
	$(PYTHON) scripts/doctor.py

generate:
	$(PYTHON) src/python_ingestion/synthetic_generator.py

generate-macro-offline:
	$(PYTHON) src/python_ingestion/bcb_extractor.py --offline-sample

generate-cvm-offline:
	$(PYTHON) src/python_ingestion/cvm_extractor.py --offline-sample

publish-bronze:
	$(PYTHON) src/python_ingestion/publish_bronze.py

build-lakehouse:
	$(PYTHON) -m src.lakehouse.local_layers

load:
	@if [ "$(DB_TARGET)" = "duckdb" ] || [ "$(DBT_TARGET)" = "duckdb" ]; then \
		$(PYTHON) src/python_ingestion/load_to_duckdb.py; \
	else \
		$(PYTHON) src/python_ingestion/load_to_postgres.py; \
	fi

validate: rust-build rust-validate

dbt:
	cd dbt && DBT_SEND_ANONYMOUS_USAGE_STATS=false DBT_TARGET=$$(if [ "$(DB_TARGET)" = "duckdb" ] || [ "$(DBT_TARGET)" = "duckdb" ]; then echo "duckdb"; else echo "$${DBT_TARGET:-dev}"; fi) ../$(DBT) build --profiles-dir .

dbt-parse:
	cd dbt && DBT_SEND_ANONYMOUS_USAGE_STATS=false ../$(DBT) parse --profiles-dir .

dbt-docs:
	cd dbt && DBT_SEND_ANONYMOUS_USAGE_STATS=false ../$(DBT) docs generate --profiles-dir .

pipeline: generate validate publish-bronze load dbt

pipeline-local: generate generate-macro-offline generate-cvm-offline validate publish-bronze build-lakehouse ai-eval

warehouse-local: load dbt

test:
	@for test_file in tests/test_*.py; do \
		echo "Running $$test_file"; \
		$(PYTHON) -m pytest $$test_file -q || exit $$?; \
	done

lint:
	$(RUFF) check src dashboards tests

ai-eval:
	$(PYTHON) -m src.ai_assistant.eval_runner --eval-file ai/evals/risk_copilot.yml

streaming-demo:
	@echo "Running Ingestion Stream Simulation..."
	$(PYTHON) -m src.streaming.producer
	DB_TARGET=duckdb DUCKDB_PATH=data/warehouse.duckdb $(PYTHON) -m src.streaming.consumer --one-shot

evidence-pack:
	$(PYTHON) scripts/evidence_pack.py

airflow-test:
	$(PYTHON) -m py_compile orchestration/airflow/dags/finbank_local_pipeline.py

dagster:
	$(DAGSTER) dev -f orchestration/dagster_defs.py

demo: pipeline
	@echo "Pipeline ready. Run 'make run-dashboard' to open the Streamlit demo."

run-dashboard:
	$(STREAMLIT) run dashboards/streamlit_app.py

rust-build:
	cd src/rust_validator && cargo build --release

rust-validate:
	$(RUST_VALIDATOR) validate --input data/raw/customers.csv --schema schemas/customers_schema.json
	$(RUST_VALIDATOR) validate --input data/raw/accounts.csv --schema schemas/accounts_schema.json
	$(RUST_VALIDATOR) validate --input data/raw/transactions.csv --schema schemas/transactions_schema.json
	$(RUST_VALIDATOR) validate --input data/raw/loans.csv --schema schemas/loans_schema.json
	@if [ -f data/raw/cvm_funds.csv ]; then $(RUST_VALIDATOR) validate --input data/raw/cvm_funds.csv --schema schemas/cvm_funds_schema.json; fi
