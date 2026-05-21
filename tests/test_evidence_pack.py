from pathlib import Path

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
