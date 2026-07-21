from pathlib import Path
from subprocess import CompletedProcess

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
    assert "Local Demo Path" in markdown


def test_build_evidence_markdown_includes_public_release_proof_points(tmp_path: Path, monkeypatch) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci\n", encoding="utf-8")

    def fake_git_output(_project_root: Path, command: list[str]) -> str:
        if command == ["git", "branch", "--show-current"]:
            return "professional-data-engineering-case"
        if command == ["git", "rev-parse", "HEAD"]:
            return "abc1234567890"
        if command == ["git", "status", "--porcelain"]:
            return ""
        if command == ["git", "remote", "get-url", "origin"]:
            return "https://github.com/DanielBBrasileiro/finbank-risk-lakehouse.git"
        return ""

    monkeypatch.setattr(evidence_pack, "_git_output", fake_git_output)

    markdown = build_evidence_markdown(project_root=tmp_path)

    assert "Repository: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse" in markdown
    assert "Current commit: abc1234567890" in markdown
    assert "GitHub Actions workflow: present" in markdown
    assert "Working tree: clean" in markdown
    assert "Verification Commands" in markdown
    assert "`make test`" in markdown
    assert "`make lint`" in markdown
    assert "`AI_DEMO_MODE=1 make ai-eval`" in markdown
    assert "Evidence Captured" in markdown
    assert "Publication Checklist" in markdown
    assert "`docs/portfolio/pre_linkedin_test_plan.md`" in markdown


def test_build_evidence_markdown_counts_nested_screenshots(tmp_path: Path) -> None:
    screenshots = tmp_path / "docs" / "portfolio" / "screenshots"
    screenshots.mkdir(parents=True)
    (screenshots / "dashboard-credit-risk.png").write_bytes(b"fake")
    (screenshots / "architecture-overview.svg").write_bytes(b"fake")
    (screenshots / "copilot-governance.png").write_bytes(b"fake")
    (screenshots / "dbt-lineage.png").write_bytes(b"fake")
    (screenshots / "github-actions-release.png").write_bytes(b"fake")

    markdown = build_evidence_markdown(project_root=tmp_path)

    assert "portfolio visuals: 5 captured" in markdown
    assert "`docs/portfolio/screenshots/dbt-lineage.png`" in markdown
    assert "Artifact SHA-256" in markdown
    assert "Copilot controls captured" in markdown


def test_git_output_allows_slow_local_git(monkeypatch, tmp_path: Path) -> None:
    observed: dict[str, int] = {}

    def fake_run(command, **kwargs):
        observed["timeout"] = kwargs["timeout"]
        return CompletedProcess(command, 0, stdout="main\n", stderr="")

    monkeypatch.setattr(evidence_pack.subprocess, "run", fake_run)

    assert evidence_pack._git_output(tmp_path, ["git", "branch", "--show-current"]) == "main"
    assert observed["timeout"] >= 30


def test_validation_markdown_marks_matching_commit() -> None:
    validation = {
        "validated_at_utc": "2026-07-21T12:00:00+00:00",
        "commit": "abc123",
        "python_tests_passed": 77,
        "python_coverage_percent": 70.68,
        "rust_tests_passed": 2,
        "dbt_checks_total": 78,
        "dbt_statuses": {"pass": 76, "no-op": 2},
        "streaming_replay": "passed",
        "dashboard_smoke": "passed",
    }

    markdown = "\n".join(evidence_pack._validation_markdown(validation, current_commit="abc123"))

    assert "Validation matches current commit: yes" in markdown
    assert "Python tests: 77 passed" in markdown
    assert "dbt checks: 78" in markdown
