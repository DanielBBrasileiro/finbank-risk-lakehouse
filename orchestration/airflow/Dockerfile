ARG RUST_VERSION=1.83.0
ARG AIRFLOW_VERSION=3.1.0
ARG PYTHON_VERSION=3.12
FROM rust:${RUST_VERSION}-bookworm AS validator-builder

WORKDIR /build
COPY src/rust_validator/Cargo.toml src/rust_validator/Cargo.lock ./
COPY src/rust_validator/src ./src
RUN cargo build --locked --release

FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

ARG AIRFLOW_VERSION
COPY orchestration/airflow/requirements.txt /tmp/finbank-requirements.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/finbank-requirements.txt

USER root
RUN mkdir -p /opt/finbank/data /opt/airflow/logs /opt/airflow/metadata \
    && chown -R airflow:0 /opt/finbank /opt/airflow/logs /opt/airflow/metadata \
    && chmod -R g=u /opt/finbank /opt/airflow/logs /opt/airflow/metadata

COPY --chown=airflow:0 ai /opt/finbank/ai
COPY --chown=airflow:0 dbt /opt/finbank/dbt
COPY --chown=airflow:0 docs /opt/finbank/docs
COPY --chown=airflow:0 schemas /opt/finbank/schemas
COPY --chown=airflow:0 orchestration /opt/finbank/orchestration
COPY --chown=airflow:0 src/__init__.py /opt/finbank/src/__init__.py
COPY --chown=airflow:0 src/ai_assistant /opt/finbank/src/ai_assistant
COPY --chown=airflow:0 src/lakehouse /opt/finbank/src/lakehouse
COPY --chown=airflow:0 src/python_ingestion /opt/finbank/src/python_ingestion
COPY --from=validator-builder /build/target/release/finbank-validator /usr/local/bin/finbank-validator

ENV FINBANK_PROJECT_ROOT_IN_CONTAINER=/opt/finbank \
    FINBANK_VALIDATOR_BIN=/usr/local/bin/finbank-validator \
    PYTHONPATH=/opt/finbank \
    DB_TARGET=duckdb \
    DBT_TARGET=duckdb \
    DUCKDB_PATH=/opt/finbank/data/warehouse.duckdb \
    AI_DEMO_MODE=1 \
    AI_AUDIT_PATH=/opt/finbank/data/ai_audit/copilot_audit.jsonl \
    DBT_SEND_ANONYMOUS_USAGE_STATS=false

WORKDIR /opt/finbank
USER airflow
