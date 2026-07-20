from dagster import AssetExecutionContext, Definitions, asset

from orchestration.local_pipeline import run_step


def _materialize_step(context: AssetExecutionContext, step_name: str) -> list[str]:
    commands = run_step(step_name)
    context.add_output_metadata({"step": step_name, "commands": commands, "command_count": len(commands)})
    return commands


@asset(group_name="sources")
def deterministic_sources(context: AssetExecutionContext) -> list[str]:
    return _materialize_step(context, "sources")


@asset(group_name="quality", deps=[deterministic_sources])
def validated_contracts(context: AssetExecutionContext) -> list[str]:
    return _materialize_step(context, "contracts")


@asset(group_name="lakehouse", deps=[validated_contracts])
def local_lakehouse(context: AssetExecutionContext) -> list[str]:
    return _materialize_step(context, "lakehouse")


@asset(group_name="warehouse", deps=[local_lakehouse])
def duckdb_warehouse(context: AssetExecutionContext) -> list[str]:
    return _materialize_step(context, "warehouse")


@asset(group_name="analytics", deps=[duckdb_warehouse])
def dbt_risk_marts(context: AssetExecutionContext) -> list[str]:
    return _materialize_step(context, "marts")


@asset(group_name="ai", deps=[dbt_risk_marts])
def governed_ai_eval(context: AssetExecutionContext) -> list[str]:
    return _materialize_step(context, "ai_eval")


defs = Definitions(
    assets=[
        deterministic_sources,
        validated_contracts,
        local_lakehouse,
        duckdb_warehouse,
        dbt_risk_marts,
        governed_ai_eval,
    ]
)
