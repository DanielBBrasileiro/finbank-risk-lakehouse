from pathlib import Path

import scripts.evidence_pack as evidence_pack
from scripts.evidence_pack import build_evidence_markdown


def test_build_evidence_markdown_includes_portfolio_sections(tmp_path: Path) -> None:
    (tmp_path / "dbt").mkdir()
    (tmp_path / "dbt" / "target").mkdir()
    (tmp_path / "dbt" / "target" / "manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "lakehouse").mkdir()
    (tmp_path / "data" / "lakehouse" / "manifest.json").write_text("{}", encoding="utf-8")

    markdown = build_evidence_markdown(project_root=tmp_path)

    assert "# FinBank Portfolio Evidence Pack" in markdown
    assert "dbt manifest: present" in markdown
    assert "lakehouse manifest: present" in markdown
    assert "Local-first demo path" in markdown


def test_build_evidence_markdown_includes_recruiter_ready_proof_points(tmp_path: Path, monkeypatch) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci\n", encoding="utf-8")

    def fake_git_output(_project_root: Path, command: list[str]) -> str:
        if command == ["git", "branch", "--show-current"]:
            return "professional-data-engineering-case"
        if command == ["git", "rev-parse", "--short", "HEAD"]:
            return "abc1234"
        if command == ["git", "remote", "get-url", "origin"]:
            return "https://github.com/DanielBBrasileiro/finbank-risk-lakehouse-starter.git"
        return ""

    monkeypatch.setattr(evidence_pack, "_git_output", fake_git_output)

    markdown = build_evidence_markdown(project_root=tmp_path)

    assert "Repository: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse-starter" in markdown
    assert "Current commit: abc1234" in markdown
    assert "GitHub Actions CI: configured" in markdown
    assert "Verification Commands" in markdown
    assert "`make test`" in markdown
    assert "`make lint`" in markdown
    assert "`AI_DEMO_MODE=1 make ai-eval`" in markdown
    assert "Evidence Captured" in markdown
    assert "Publication Checklist" in markdown


def test_build_evidence_markdown_counts_nested_screenshots(tmp_path: Path) -> None:
    screenshots = tmp_path / "docs" / "portfolio" / "screenshots"
    screenshots.mkdir(parents=True)
    (screenshots / "dashboard-credit-risk.png").write_bytes(b"fake")
    (screenshots / "dashboard-account-health.png").write_bytes(b"fake")
    (screenshots / "dashboard-ai-governance.png").write_bytes(b"fake")
    (screenshots / "dbt-docs-lineage.png").write_bytes(b"fake")

    markdown = build_evidence_markdown(project_root=tmp_path)

    assert "portfolio screenshots: 4 captured" in markdown
    assert "`docs/portfolio/screenshots/dbt-docs-lineage.png`" in markdown
    assert "Governed AI audit captured" in markdown
