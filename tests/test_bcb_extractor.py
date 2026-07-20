import sys
from pathlib import Path

import pandas as pd

from src.python_ingestion import bcb_extractor
from src.python_ingestion.bcb_extractor import (
    fetch_bcb_series,
    normalize_bcb_series,
    write_bcb_macro_indicators,
    write_offline_macro_sample,
)


def test_normalize_bcb_series_adds_business_metadata() -> None:
    frame = pd.DataFrame([{"data": "02/01/2024", "valor": "10.50"}])

    result = normalize_bcb_series(frame, series_id=11, indicator_name="selic")

    assert list(result.columns) == ["observation_date", "indicator_name", "series_id", "value"]
    assert result.iloc[0]["observation_date"] == "2024-01-02"
    assert result.iloc[0]["indicator_name"] == "selic"
    assert result.iloc[0]["series_id"] == 11
    assert result.iloc[0]["value"] == 10.5


def test_write_offline_macro_sample_creates_single_macro_file(tmp_path: Path) -> None:
    output = write_offline_macro_sample(raw_dir=tmp_path)

    assert output == tmp_path / "macro_indicators.csv"
    data = pd.read_csv(output)
    assert {"selic", "credit_free_total"}.issubset(set(data["indicator_name"]))
    assert set(data.columns) == {"observation_date", "indicator_name", "series_id", "value"}


def test_fetch_bcb_series_uses_official_api_shape(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return [{"data": "03/01/2024", "valor": "9.75"}]

    observed = {}

    def fake_get(url: str, timeout: int):
        observed.update({"url": url, "timeout": timeout})
        return Response()

    monkeypatch.setattr(bcb_extractor.requests, "get", fake_get)

    result = fetch_bcb_series(11, "01/01/2024", "31/01/2024")

    assert "bcdata.sgs.11" in observed["url"]
    assert observed["timeout"] == 30
    assert result.iloc[0]["series_id"] == 11
    assert result.iloc[0]["valor"] == 9.75


def test_write_bcb_macro_indicators_combines_configured_series(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        bcb_extractor,
        "fetch_bcb_series",
        lambda series_id, _start, _end: pd.DataFrame(
            [{"data": "01/01/2024", "valor": float(series_id)}]
        ),
    )

    output = write_bcb_macro_indicators(raw_dir=tmp_path)

    result = pd.read_csv(output)
    assert set(result["indicator_name"]) == set(bcb_extractor.SERIES)


def test_bcb_cli_writes_offline_fixture(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["bcb_extractor", "--offline-sample", "--raw-dir", str(tmp_path)],
    )

    bcb_extractor.main()

    assert (tmp_path / "macro_indicators.csv").exists()
    assert "Saved macro indicators" in capsys.readouterr().out
