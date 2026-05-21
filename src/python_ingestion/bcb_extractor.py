from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path("data/raw/bcb")
RAW_DIR.mkdir(parents=True, exist_ok=True)

SERIES = {
    "selic": 11,
    "credit_free_total": 20542,
}

OFFLINE_SAMPLE = {
    "selic": [
        {"data": "01/01/2024", "valor": "11.75"},
        {"data": "01/02/2024", "valor": "11.25"},
        {"data": "01/03/2024", "valor": "10.75"},
    ],
    "credit_free_total": [
        {"data": "01/01/2024", "valor": "5654321.10"},
        {"data": "01/02/2024", "valor": "5712345.20"},
        {"data": "01/03/2024", "valor": "5789012.30"},
    ],
}


def fetch_bcb_series(series_id: int, start_date: str, end_date: str) -> pd.DataFrame:
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"
        f"?formato=json&dataInicial={start_date}&dataFinal={end_date}"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    df = pd.DataFrame(response.json())
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["series_id"] = series_id
    return df


def normalize_bcb_series(frame: pd.DataFrame, *, series_id: int, indicator_name: str) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["observation_date"] = pd.to_datetime(normalized["data"], dayfirst=True).dt.strftime("%Y-%m-%d")
    normalized["value"] = pd.to_numeric(normalized["valor"], errors="coerce")
    normalized["indicator_name"] = indicator_name
    normalized["series_id"] = series_id
    return normalized[["observation_date", "indicator_name", "series_id", "value"]]


def write_offline_macro_sample(*, raw_dir: Path = RAW_DIR.parent) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames = [
        normalize_bcb_series(pd.DataFrame(rows), series_id=SERIES[name], indicator_name=name)
        for name, rows in OFFLINE_SAMPLE.items()
    ]
    output = raw_dir / "macro_indicators.csv"
    pd.concat(frames, ignore_index=True).to_csv(output, index=False)
    return output


def write_bcb_macro_indicators(
    *,
    raw_dir: Path = RAW_DIR.parent,
    start_date: str = "01/01/2020",
    end_date: str = "31/12/2026",
) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for name, series_id in SERIES.items():
        frame = fetch_bcb_series(series_id, start_date, end_date)
        frames.append(normalize_bcb_series(frame, series_id=series_id, indicator_name=name))

    output = raw_dir / "macro_indicators.csv"
    pd.concat(frames, ignore_index=True).to_csv(output, index=False)
    return output


def main() -> None:
    parser = ArgumentParser(description="Extract BCB macroeconomic series for the FinBank demo.")
    parser.add_argument("--offline-sample", action="store_true", help="Write a deterministic local sample.")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--start-date", default="01/01/2020")
    parser.add_argument("--end-date", default="31/12/2026")
    args = parser.parse_args()

    if args.offline_sample:
        output = write_offline_macro_sample(raw_dir=Path(args.raw_dir))
    else:
        output = write_bcb_macro_indicators(
            raw_dir=Path(args.raw_dir),
            start_date=args.start_date,
            end_date=args.end_date,
        )
    print(f"Saved macro indicators: {output}")


if __name__ == "__main__":
    main()
