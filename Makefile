.PHONY: up down install bootstrap doctor clean-demo generate generate-macro-offline generate-cvm-offline publish-bronze build-lakehouse load load-audit validate dbt dbt-parse dbt-docs pipeline pipeline-local demo-local warehouse-local test coverage test-all lint sql-lint ai-eval dagster run-dashboard dashboard-smoke rust-build rust-test rust-validate streaming-demo streaming-replay-test evidence-pack airflow-test demo

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
	# requirements-dev.txt remains a human-readable mirror; uv uses pyproject.toml + uv.lock.
	uv venv --allow-existing .venv
	uv sync --all-extras --locked

doctor:
	$(PYTHON) scripts/doctor.py

clean-demo:
	rm -rf data/raw data/bronze data/processed data/lakehouse data/streaming data/ai_audit data/qdrant_db
	rm -f data/warehouse.duckdb data/warehouse.duckdb.wal
	rm -rf dbt/target dbt/logs

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

load-audit:
	DB_TARGET=$(DB_TARGET) DBT_TARGET=$(DBT_TARGET) $(PYTHON) src/python_ingestion/load_audit_logs.py

validate: rust-build rust-validate

dbt:
	cd dbt && DBT_SEND_ANONYMOUS_USAGE_STATS=false DBT_TARGET=$$(if [ "$(DB_TARGET)" = "duckdb" ] || [ "$(DBT_TARGET)" = "duckdb" ]; then echo "duckdb"; else echo "$${DBT_TARGET:-dev}"; fi) ../$(DBT) build --profiles-dir .

dbt-parse:
	cd dbt && DBT_SEND_ANONYMOUS_USAGE_STATS=false ../$(DBT) parse --profiles-dir .

dbt-docs:
	cd dbt && DBT_SEND_ANONYMOUS_USAGE_STATS=false ../$(DBT) docs generate --profiles-dir .

pipeline: generate validate publish-bronze load load-audit dbt

pipeline-local: generate generate-macro-offline generate-cvm-offline validate publish-bronze build-lakehouse ai-eval

warehouse-local: load load-audit dbt

demo-local: generate generate-macro-offline generate-cvm-offline validate publish-bronze build-lakehouse
	$(MAKE) AI_DEMO_MODE=1 AI_AUDIT_PATH=data/ai_audit/copilot_audit.jsonl ai-eval
	$(MAKE) DB_TARGET=duckdb load
	$(MAKE) DB_TARGET=duckdb load-audit
	$(MAKE) DB_TARGET=duckdb dbt
	$(MAKE) streaming-demo
	@echo "Local demo ready. Run 'DB_TARGET=duckdb make run-dashboard'."

test:
	@for test_file in tests/test_*.py; do \
		echo "Running $$test_file"; \
		$(PYTHON) -m pytest $$test_file -q || exit $$?; \
	done

coverage:
	$(PYTHON) -m pytest -q --cov=src --cov-report=term --cov-fail-under=70

lint:
	$(RUFF) check src dashboards tests scripts orchestration databricks

sql-lint:
	cd dbt && DBT_SEND_ANONYMOUS_USAGE_STATS=false DBT_TARGET=duckdb ../.venv/bin/sqlfluff lint models tests

test-all: coverage lint sql-lint rust-test
	$(MAKE) DB_TARGET=duckdb dbt
	$(MAKE) streaming-replay-test
	$(MAKE) dashboard-smoke
	$(PYTHON) scripts/evidence_pack.py --record-validation

ai-eval:
	$(PYTHON) -m src.ai_assistant.eval_runner --eval-file ai/evals/risk_copilot.yml

streaming-demo:
	@echo "Running Ingestion Stream Simulation..."
	$(PYTHON) -m src.streaming.producer
	DB_TARGET=duckdb DUCKDB_PATH=data/warehouse.duckdb $(PYTHON) -m src.streaming.consumer --one-shot

streaming-replay-test:
	DB_TARGET=duckdb DUCKDB_PATH=data/warehouse.duckdb $(PYTHON) -m pytest tests/test_real_streaming.py -q

evidence-pack:
	$(PYTHON) scripts/evidence_pack.py

airflow-test:
	$(PYTHON) -m py_compile orchestration/airflow/dags/finbank_local_pipeline.py

dagster:
	$(DAGSTER) dev -f orchestration/dagster_defs.py

demo: demo-local
	@echo "Pipeline ready. Run 'make run-dashboard' to open the Streamlit demo."

run-dashboard:
	PYTHONPATH=. DB_TARGET=$${DB_TARGET:-duckdb} AI_AUDIT_PATH=$${AI_AUDIT_PATH:-data/ai_audit/copilot_audit.jsonl} $(STREAMLIT) run dashboards/streamlit_app.py

dashboard-smoke:
	PYTHONPATH=. DB_TARGET=duckdb AI_DEMO_MODE=1 $(PYTHON) scripts/smoke_dashboard.py

rust-build:
	cd src/rust_validator && cargo build --release

rust-test:
	cd src/rust_validator && cargo test --all-targets

rust-validate:
	$(RUST_VALIDATOR) validate --input data/raw/customers.csv --schema schemas/customers_schema.json
	$(RUST_VALIDATOR) validate --input data/raw/accounts.csv --schema schemas/accounts_schema.json
	$(RUST_VALIDATOR) validate --input data/raw/transactions.csv --schema schemas/transactions_schema.json
	$(RUST_VALIDATOR) validate --input data/raw/loans.csv --schema schemas/loans_schema.json
	@if [ -f data/raw/cvm_funds.csv ]; then $(RUST_VALIDATOR) validate --input data/raw/cvm_funds.csv --schema schemas/cvm_funds_schema.json; fi
