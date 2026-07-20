import pytest

from src.ai_assistant.sql_guardrails import SqlGuardrailError, build_guarded_query


def test_appends_default_limit_to_allowed_select() -> None:
    sql = "select customer_id, total_outstanding_balance from analytics_marts.mart_customer_exposure"

    guarded = build_guarded_query(sql, allowed_schemas=("analytics_marts",), default_limit=100)

    assert guarded == (
        "select customer_id, total_outstanding_balance "
        "from analytics_marts.mart_customer_exposure limit 100"
    )


def test_preserves_existing_limit_when_it_is_more_restrictive() -> None:
    sql = "select * from analytics_marts.mart_daily_transactions limit 25"

    guarded = build_guarded_query(sql, allowed_schemas=("analytics_marts",), default_limit=100)

    assert guarded == "select * from analytics_marts.mart_daily_transactions limit 25"


def test_caps_existing_limit_when_it_is_too_large() -> None:
    sql = "select * from analytics_marts.mart_daily_transactions limit 10000"

    guarded = build_guarded_query(sql, allowed_schemas=("analytics_marts",), default_limit=500)

    assert guarded == "select * from analytics_marts.mart_daily_transactions limit 500"


@pytest.mark.parametrize(
    "sql",
    [
        "delete from analytics_marts.mart_customer_exposure",
        "select * from analytics_marts.mart_customer_exposure; drop table raw.customers",
        "insert into analytics_marts.mart_customer_exposure values (1)",
        "select * from raw.customers",
    ],
)
def test_rejects_unsafe_or_out_of_scope_sql(sql: str) -> None:
    with pytest.raises(SqlGuardrailError):
        build_guarded_query(sql, allowed_schemas=("analytics_marts",), default_limit=100)


def test_allows_cte_that_reads_only_from_allowlisted_schema() -> None:
    sql = (
        "with exposure as ("
        "select segment from analytics_marts.mart_customer_exposure"
        ") select * from exposure"
    )

    guarded = build_guarded_query(sql, allowed_schemas=("analytics_marts",), default_limit=50)

    assert guarded.endswith("limit 50")


@pytest.mark.parametrize(
    "sql",
    [
        "select * from analytics_marts.mart_customer_exposure -- trusted query",
        "select * into temporary_table from analytics_marts.mart_customer_exposure",
        (
            "select * from analytics_marts.mart_customer_exposure e "
            "join customers c on c.customer_id = e.customer_id"
        ),
        "select pg_sleep(10)",
        "select * from analytics_marts.mart_customer_exposure limit all",
        (
            "select * from analytics_marts.mart_customer_exposure; "
            "select * from analytics_marts.mart_daily_transactions"
        ),
    ],
)
def test_parser_rejects_read_only_bypass_attempts(sql: str) -> None:
    with pytest.raises(SqlGuardrailError):
        build_guarded_query(sql, allowed_schemas=("analytics_marts",), default_limit=100)


def test_blocked_words_inside_string_literals_do_not_trigger_false_positive() -> None:
    sql = (
        "select 'drop update delete' as description "
        "from analytics_marts.mart_customer_exposure"
    )

    guarded = build_guarded_query(sql, allowed_schemas=("analytics_marts",), default_limit=10)

    assert guarded.endswith("limit 10")
