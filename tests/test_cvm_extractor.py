from pathlib import Path

import pandas as pd

from src.python_ingestion import cvm_extractor
from src.python_ingestion.cvm_extractor import (
    fetch_cvm_funds,
    normalize_cvm_funds,
    write_cvm_funds,
    write_offline_cvm_sample,
)


def test_normalize_cvm_funds_maps_columns_correctly() -> None:
    frame = pd.DataFrame(
        [
            {
                "CNPJ_FUNDO": "12.345.678/0001-90",
                "DENOM_SOCIAL": "TEST FUND",
                "TP_FUNDO": "FI",
                "SITUACAO": "NORMAL",
                "CLASSE": "Renda Fixa",
                "VL_PATRIM_LIQ": 100000.00,
            }
        ]
    )

    result = normalize_cvm_funds(frame)

    assert list(result.columns) == ["cnpj", "fund_name", "fund_type", "status", "class_type", "net_worth"]
    assert result.iloc[0]["cnpj"] == "12.345.678/0001-90"
    assert result.iloc[0]["fund_name"] == "TEST FUND"
    assert result.iloc[0]["fund_type"] == "FI"
    assert result.iloc[0]["status"] == "NORMAL"
    assert result.iloc[0]["class_type"] == "Renda Fixa"
    assert result.iloc[0]["net_worth"] == 100000.00


def test_write_offline_cvm_sample_creates_funds_file(tmp_path: Path) -> None:
    output = write_offline_cvm_sample(raw_dir=tmp_path)

    assert output == tmp_path / "cvm_funds.csv"
    data = pd.read_csv(output)
    assert len(data) == 3
    assert set(data.columns) == {"cnpj", "fund_name", "fund_type", "status", "class_type", "net_worth"}


def test_normalize_cvm_funds_supplies_missing_optional_columns() -> None:
    result = normalize_cvm_funds(pd.DataFrame([{"CNPJ_FUNDO": "1", "DENOM_SOCIAL": "Fund"}]))

    assert list(result.columns) == ["cnpj", "fund_name", "fund_type", "status", "class_type", "net_worth"]
    assert pd.isna(result.iloc[0]["net_worth"])


def test_fetch_cvm_funds_parses_semicolon_payload(monkeypatch) -> None:
    class Response:
        text = "CNPJ_FUNDO;DENOM_SOCIAL\n1;Fund"

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(cvm_extractor.requests, "get", lambda _url, timeout: Response())

    result = fetch_cvm_funds()

    assert result.iloc[0]["DENOM_SOCIAL"] == "Fund"


def test_write_cvm_funds_normalizes_download(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        cvm_extractor,
        "fetch_cvm_funds",
        lambda: pd.DataFrame([{"CNPJ_FUNDO": "1", "DENOM_SOCIAL": "Fund"}]),
    )

    output = write_cvm_funds(raw_dir=tmp_path)

    assert pd.read_csv(output).iloc[0]["fund_name"] == "Fund"
