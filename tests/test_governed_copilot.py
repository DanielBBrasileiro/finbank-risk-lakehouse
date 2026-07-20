from pathlib import Path

from src.ai_assistant.governed_copilot import answer_question


def test_answer_question_returns_citations_and_guarded_sql(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "dictionary.md").write_text(
        "mart_customer_exposure exposes total_outstanding_balance, segment and portfolio_status.",
        encoding="utf-8",
    )

    answer = answer_question("show customer exposure by segment", corpus_paths=[docs])

    assert "analytics_marts.mart_customer_exposure" in answer.guarded_sql
    assert answer.guarded_sql.endswith("limit 100")
    assert answer.citations == [str(docs / "dictionary.md")]
    assert "governed offline mode" in answer.response.lower()


def test_answer_question_refuses_out_of_scope_questions(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "quality.md").write_text("dbt tests validate risk mart quality.", encoding="utf-8")

    answer = answer_question("delete all raw customers", corpus_paths=[docs])

    assert answer.guarded_sql is None
    assert "cannot run destructive" in answer.response.lower()


def test_answer_question_covers_supported_mart_intents(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "marts.md").write_text(
        "mart_daily_transactions mart_customer_exposure mart_account_health",
        encoding="utf-8",
    )

    suspicious = answer_question("show suspicious transactions", corpus_paths=[docs])
    high_risk = answer_question("show high risk customers", corpus_paths=[docs])
    account_health = answer_question("show blocked account health", corpus_paths=[docs])
    documentation_only = answer_question("explain data quality", corpus_paths=[docs])

    assert "mart_daily_transactions" in suspicious.guarded_sql
    assert "mart_customer_exposure" in high_risk.guarded_sql
    assert "mart_account_health" in account_health.guarded_sql
    assert documentation_only.guarded_sql is None
