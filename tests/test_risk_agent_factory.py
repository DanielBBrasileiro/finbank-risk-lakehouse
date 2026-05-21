from src.ai_assistant.app import OfflineGovernedRiskAgent, build_risk_agent


def test_build_risk_agent_uses_offline_agent_in_demo_mode(monkeypatch) -> None:
    monkeypatch.setenv("AI_DEMO_MODE", "1")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    agent = build_risk_agent()

    assert isinstance(agent, OfflineGovernedRiskAgent)
    assert "governed offline mode" in agent.ask("show customer exposure by segment").lower()


def test_offline_agent_uses_audit_path_from_environment(monkeypatch, tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("AI_AUDIT_PATH", str(audit_path))

    agent = OfflineGovernedRiskAgent()
    agent.ask("show customer exposure by segment")

    assert audit_path.exists()
