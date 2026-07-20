import json
from pathlib import Path

from src.ai_assistant.governed_copilot import answer_question


def test_answer_question_can_persist_audit_record(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "risk.md").write_text("Exposure by segment uses mart_customer_exposure.", encoding="utf-8")
    audit_path = tmp_path / "audit" / "copilot.jsonl"

    answer = answer_question(
        "show exposure by segment",
        corpus_paths=[docs],
        audit_path=audit_path,
    )

    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["question"] == "show exposure by segment"
    assert record["guarded_sql"] == answer.guarded_sql
    assert record["citations"] == answer.citations
    assert record["status"] == "answered"


def test_answer_question_uses_default_audit_path(monkeypatch, tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "risk.md").write_text("Exposure uses mart_customer_exposure.", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AI_AUDIT_PATH", raising=False)

    answer_question("show exposure by segment", corpus_paths=[docs])

    default_audit = tmp_path / "data" / "ai_audit" / "copilot_audit.jsonl"
    record = json.loads(default_audit.read_text(encoding="utf-8").strip())
    assert record["question"] == "show exposure by segment"
    assert record["status"] == "answered"
