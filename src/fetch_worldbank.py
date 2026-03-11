"""Download World Bank monthly commodity Excel and extract urea price series."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests


def fetch_worldbank(
    monthly_xlsx_url: str,
    raw_subdir: str,
    urea_series_name_contains: str = "Urea",
) -> tuple[pd.DataFrame, Path]:
    """
    Download CMO-Historical-Data-Monthly.xlsx and extract urea column(s).
    Returns (DataFrame with date, price), raw_subdir path.
    """
    Path(raw_subdir).mkdir(parents=True, exist_ok=True)
    outpath = Path(raw_subdir) / "CMO-Historical-Data-Monthly.xlsx"

    if not outpath.exists():
        r = requests.get(monthly_xlsx_url, timeout=120)
        r.raise_for_status()
        outpath.write_bytes(r.content)

    xl = pd.ExcelFile(outpath)
    dates, prices = [], []

    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet, header=None)
        # CMO format: row 0 = headers (commodity names), col 0 = dates (YYYYM01, etc.)
        urea_col = None
        if len(df) > 0:
            for c in range(len(df.columns)):
                val = df.iloc[0, c]
                if pd.notna(val) and urea_series_name_contains.lower() in str(val).lower():
                    urea_col = c
                    break
        if urea_col is None:
            for idx, row in df.iterrows():
                for c, val in enumerate(row):
                    if pd.notna(val) and urea_series_name_contains.lower() in str(val).lower():
                        urea_col = c
                        break
                if urea_col is not None:
                    break
        if urea_col is None:
            continue

        for idx in range(1, len(df)):
            row = df.iloc[idx]
            date_val = row.iloc[0] if len(row) > 0 else None
            price_val = row.iloc[urea_col] if urea_col < len(row) else None
            if pd.isna(date_val):
                continue
            if pd.isna(price_val) or str(price_val).strip() in ("..", ""):
                continue
            try:
                s = str(date_val).strip()
                if "M" in s.upper():
                    dt = pd.to_datetime(s.replace("M", "-"), format="%Y-%m", errors="coerce")
                else:
                    dt = pd.to_datetime(date_val, errors="coerce")
                if pd.notna(dt):
                    p = float(str(price_val).replace(",", ""))
                    dates.append(dt)
                    prices.append(p)
            except (ValueError, TypeError):
                continue
        if dates:
            break

    if not dates:
        return pd.DataFrame(columns=["date", "price_usd"]), Path(raw_subdir)

    result = pd.DataFrame({"date": dates, "price_usd": prices}).drop_duplicates(subset=["date"]).sort_values("date")
    return result, Path(raw_subdir)
