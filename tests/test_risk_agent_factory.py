import json
from pathlib import Path

from src.ai_assistant.app import OfflineGovernedRiskAgent, RiskAgent, build_risk_agent


def test_build_risk_agent_uses_offline_agent_in_demo_mode(monkeypatch) -> None:
    monkeypatch.setenv("AI_DEMO_MODE", "1")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    agent = build_risk_agent()

    assert isinstance(agent, OfflineGovernedRiskAgent)


def test_offline_agent_can_use_explicit_corpus_paths(tmp_path: Path) -> None:
    (tmp_path / "context.md").write_text("analytics_marts mart_customer_exposure segment", encoding="utf-8")

    agent = OfflineGovernedRiskAgent(corpus_paths=[tmp_path])

    assert "governed offline mode" in agent.ask("show customer exposure by segment").lower()


def test_offline_agent_uses_audit_path_from_environment(monkeypatch, tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("AI_AUDIT_PATH", str(audit_path))

    agent = OfflineGovernedRiskAgent(corpus_paths=[tmp_path])
    agent.ask("show customer exposure by segment")

    assert audit_path.exists()


def test_build_risk_agent_uses_governed_online_adapter_when_key_exists(monkeypatch) -> None:
    monkeypatch.setenv("AI_DEMO_MODE", "0")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    agent = build_risk_agent()

    assert isinstance(agent, RiskAgent)


def test_online_agent_still_applies_guardrails_and_auditing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_DEMO_MODE", "0")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    audit_path = tmp_path / "online-audit.jsonl"
    agent = RiskAgent(corpus_paths=[tmp_path], audit_path=audit_path)

    response = agent.ask("drop table analytics_marts.mart_customer_exposure")

    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert "cannot run destructive" in response.lower()
    assert record["status"] == "rejected"
    assert record["guarded_sql"] is None
