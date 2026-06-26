from pathlib import Path

from src.ai_assistant.app import OfflineGovernedRiskAgent, build_risk_agent


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
