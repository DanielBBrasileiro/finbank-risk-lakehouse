from __future__ import annotations

import os
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

from orchestration.local_pipeline import STEP_ORDER

PROJECT_ROOT = os.environ.get("FINBANK_PROJECT_ROOT_IN_CONTAINER", "/opt/finbank")


with DAG(
    dag_id="finbank_local_portfolio_pipeline",
    description="Operational local FinBank batch path using DuckDB and deterministic inputs.",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "finbank-data-platform",
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["finbank", "portfolio", "data-engineering"],
) as dag:
    tasks = {
        step: BashOperator(
            task_id=step,
            bash_command=f"cd {PROJECT_ROOT} && python -m orchestration.local_pipeline {step}",
            execution_timeout=timedelta(minutes=30),
        )
        for step in STEP_ORDER
    }

    for upstream, downstream in zip(STEP_ORDER[:-1], STEP_ORDER[1:], strict=True):
        tasks[upstream] >> tasks[downstream]
