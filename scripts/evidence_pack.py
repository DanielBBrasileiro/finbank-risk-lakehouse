from __future__ import annotations

import subprocess
from pathlib import Path


def build_evidence_markdown(*, project_root: Path = Path(".")) -> str:
    dbt_manifest = project_root / "dbt" / "target" / "manifest.json"
    lakehouse_manifest = project_root / "data" / "lakehouse" / "manifest.json"
    branch = _git_output(project_root, ["git", "branch", "--show-current"])

    return "\n".join(
        [
            "# FinBank Portfolio Evidence Pack",
            "",
            "## Local-first demo path",
            "",
            "- Generate synthetic banking data.",
            "- Validate raw CSV contracts with Rust.",
            "- Build local Bronze/Silver/Gold lakehouse layers.",
            "- Load PostgreSQL and run dbt marts when Docker is available.",
            "- Run governed AI evals in deterministic offline mode.",
            "",
            "## Artifact Status",
            "",
            f"- git branch: {branch or 'unknown'}",
            f"- dbt manifest: {'present' if dbt_manifest.exists() else 'missing'}",
            f"- lakehouse manifest: {'present' if lakehouse_manifest.exists() else 'missing'}",
            "",
            "## Recruiter Narrative",
            "",
            "This repository demonstrates a cost-aware data engineering lifecycle: generation, ingestion, "
            "storage, transformation, serving, governance, orchestration and AI controls.",
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
        result = subprocess.run(command, cwd=project_root, check=True, capture_output=True, text=True, timeout=10)
    except Exception:
        return ""
    return result.stdout.strip()


def main() -> None:
    target = write_evidence_pack()
    print(target)


if __name__ == "__main__":
    main()
