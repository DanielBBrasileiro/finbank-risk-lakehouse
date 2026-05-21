from pathlib import Path

import pandas as pd

from src.python_ingestion.bcb_extractor import normalize_bcb_series, write_offline_macro_sample


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
