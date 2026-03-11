"""Fetch Philippine urea imports by partner from UN Comtrade API."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

try:
    import comtradeapicall
except ImportError:
    comtradeapicall = None


def fetch_comtrade(
    reporter_code: str | int,
    commodity_code: str,
    flow_code: str,
    start_year: int,
    end_year: int,
    frequency: str,
    raw_subdir: str,
    api_key_env: str = "COMTRADE_API_KEY",
) -> tuple[pd.DataFrame, Path]:
    """
    Fetch Philippine urea imports by partner from Comtrade.
    Saves raw JSON/CSV per year to raw_subdir and returns combined DataFrame.
    """
    if comtradeapicall is None:
        raise ImportError("comtradeapicall is required. Install with: pip install comtradeapicall")

    Path(raw_subdir).mkdir(parents=True, exist_ok=True)
    api_key = os.environ.get(api_key_env)
    freq_code = "A" if frequency.upper() == "A" else "M"

    all_dfs: list[pd.DataFrame] = []

    for year in range(start_year, end_year + 1):
        period = str(year) if freq_code == "A" else ",".join(f"{year}{m:02d}" for m in range(1, 13))
        try:
            if api_key:
                df = comtradeapicall.getFinalData(
                    api_key,
                    typeCode="C",
                    freqCode=freq_code,
                    clCode="HS",
                    period=period,
                    reporterCode=str(reporter_code),
                    cmdCode=commodity_code,
                    flowCode=flow_code,
                    partnerCode=None,
                    partner2Code=None,
                    customsCode=None,
                    motCode=None,
                    maxRecords=25000,
                    format_output="JSON",
                    aggregateBy=None,
                    breakdownMode="classic",
                    countOnly=None,
                    includeDesc=True,
                )
            else:
                df = comtradeapicall.previewFinalData(
                    typeCode="C",
                    freqCode=freq_code,
                    clCode="HS",
                    period=str(year),
                    reporterCode=str(reporter_code),
                    cmdCode=commodity_code,
                    flowCode=flow_code,
                    partnerCode=None,
                    partner2Code=None,
                    customsCode=None,
                    motCode=None,
                    maxRecords=500,
                    format_output="JSON",
                    aggregateBy=None,
                    breakdownMode="classic",
                    countOnly=None,
                    includeDesc=True,
                )
        except Exception as e:
            print(f"Comtrade fetch failed for {year}: {e}")
            continue

        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            continue

        if isinstance(df, dict) and "data" in df:
            df = pd.DataFrame(df["data"])
        elif not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df) if df else pd.DataFrame()

        if not df.empty:
            outpath = Path(raw_subdir) / f"comtrade_phl_urea_{year}.csv"
            df.to_csv(outpath, index=False)
            all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame(), Path(raw_subdir)

    combined = pd.concat(all_dfs, ignore_index=True)
    return combined, Path(raw_subdir)
