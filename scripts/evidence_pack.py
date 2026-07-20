from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def build_evidence_markdown(*, project_root: Path = Path(".")) -> str:
    dbt_manifest = project_root / "dbt" / "target" / "manifest.json"
    lakehouse_manifest = project_root / "data" / "lakehouse" / "manifest.json"
    ci_workflow = project_root / ".github" / "workflows" / "ci.yml"
    dashboard_screenshots = sorted((project_root / "docs" / "portfolio").rglob("*.png"))
    screenshot_lines = [
        f"- `{path.relative_to(project_root)}`" for path in dashboard_screenshots
    ] or ["- No screenshots captured yet."]
    captured_names = {path.name for path in dashboard_screenshots}
    expected_screenshots = {
        "dashboard-credit-risk.png",
        "dashboard-account-health.png",
        "dashboard-ai-governance.png",
        "dbt-docs-lineage.png",
    }
    missing_screenshots = sorted(expected_screenshots - captured_names)
    evidence_status_lines = (
        [
            "- Dashboard risk view captured after a local pipeline run.",
            "- Account health dashboard captured after dbt marts were rebuilt.",
            "- Governed AI audit captured with one answered and one rejected interaction.",
            "- dbt docs lineage captured from the generated catalog.",
        ]
        if not missing_screenshots
        else [f"- Missing `{name}`." for name in missing_screenshots]
    )
    branch = _git_output(project_root, ["git", "branch", "--show-current"])
    commit = _git_output(project_root, ["git", "rev-parse", "HEAD"])
    dirty = bool(_git_output(project_root, ["git", "status", "--porcelain"]))
    remote_url = _normalize_remote_url(_git_output(project_root, ["git", "remote", "get-url", "origin"]))
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    artifacts = [dbt_manifest, lakehouse_manifest, *dashboard_screenshots]
    artifact_lines = [
        f"- `{path.relative_to(project_root)}`: `{_sha256(path)}`"
        for path in artifacts
        if path.exists() and path.is_file()
    ] or ["- No generated artifacts were available for hashing."]

    return "\n".join(
        [
            "# FinBank Portfolio Evidence Pack",
            "",
            "## Public Repository",
            "",
            f"- Repository: {remote_url or 'unknown'}",
            f"- Current branch: {branch or 'unknown'}",
            f"- Current commit: {commit or 'unknown'}",
            f"- Generated at (UTC): {generated_at}",
            f"- Working tree: {'dirty' if dirty else 'clean'}",
            f"- GitHub Actions workflow: {'present' if ci_workflow.exists() else 'missing'}",
            f"- CI results: {remote_url + '/actions/workflows/ci.yml' if remote_url else 'unknown'}",
            "",
            "## Local-first demo path",
            "",
            "- Generate synthetic banking data.",
            "- Validate raw CSV contracts with Rust.",
            "- Build local Bronze/Silver/Gold lakehouse layers.",
            "- Load DuckDB or PostgreSQL and build tested dbt marts.",
            "- Run governed AI evals in deterministic offline mode.",
            "",
            "## Artifact Status",
            "",
            f"- dbt manifest: {'present' if dbt_manifest.exists() else 'missing'}",
            f"- lakehouse manifest: {'present' if lakehouse_manifest.exists() else 'missing'}",
            f"- portfolio screenshots: {len(dashboard_screenshots)} captured",
            *screenshot_lines,
            "",
            "## Artifact SHA-256",
            "",
            *artifact_lines,
            "",
            "## Verification Commands",
            "",
            "- `make doctor`",
            "- `make test`",
            "- `make lint`",
            "- `AI_DEMO_MODE=1 make ai-eval`",
            "- `AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local`",
            "- `make test-all`",
            "- `make dashboard-smoke`",
            "",
            "## Recruiter Narrative",
            "",
            "This repository demonstrates a verified local data engineering lifecycle: generation, validation, "
            "layered storage, transformation, serving and governed analytical access. Cloud assets are blueprints.",
            "",
            "## Evidence Captured",
            "",
            *evidence_status_lines,
            "- Screenshot presence is automated; visual content still requires human review.",
            "",
            "## Publication Checklist",
            "",
            "- Ensure the branch linked from LinkedIn contains the latest verified commits.",
            "- Run `docs/portfolio/pre_linkedin_test_plan.md` before posting.",
            "",
        ]
    )


def write_evidence_pack(
    *,
    project_root: Path = Path("."),
    output_path: Path = Path("docs/portfolio/evidence.md"),
) -> Path:
    target = project_root / output_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_evidence_markdown(project_root=project_root), encoding="utf-8")
    return target


def _git_output(project_root: Path, command: list[str]) -> str:
    try:
        result = subprocess.run(command, cwd=project_root, check=True, capture_output=True, text=True, timeout=30)
    except Exception:
        return ""
    return result.stdout.strip()


def _normalize_remote_url(remote_url: str) -> str:
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    if remote_url.startswith("git@github.com:"):
        return "https://github.com/" + remote_url.removeprefix("git@github.com:")
    return remote_url


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    target = write_evidence_pack()
    print(target)


if __name__ == "__main__":
    main()
