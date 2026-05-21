from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_ROOT = os.environ.get("FINBANK_PROJECT_ROOT_IN_CONTAINER", "/opt/finbank")


with DAG(
    dag_id="finbank_local_portfolio_pipeline",
    description="Local-first FinBank Data Engineering portfolio pipeline.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["finbank", "portfolio", "data-engineering"],
) as dag:
    doctor = BashOperator(
        task_id="doctor",
        bash_command=f"cd {PROJECT_ROOT} && make doctor",
    )
    pipeline_local = BashOperator(
        task_id="pipeline_local",
        bash_command=f"cd {PROJECT_ROOT} && make pipeline-local",
    )
    dbt_parse = BashOperator(
        task_id="dbt_parse",
        bash_command=f"cd {PROJECT_ROOT} && make dbt-parse",
    )
    streaming_demo = BashOperator(
        task_id="streaming_demo",
        bash_command=f"cd {PROJECT_ROOT} && make streaming-demo",
    )
    evidence_pack = BashOperator(
        task_id="evidence_pack",
        bash_command=f"cd {PROJECT_ROOT} && make evidence-pack",
    )

    doctor >> pipeline_local >> dbt_parse >> streaming_demo >> evidence_pack
