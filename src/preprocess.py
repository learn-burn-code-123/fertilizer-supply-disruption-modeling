"""Preprocess raw data into clean tables for the scenario model."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def preprocess_comtrade(comtrade_df: pd.DataFrame, vulnerability_scores: dict[str, float]) -> pd.DataFrame:
    """
    Compute partner shares and vulnerability-weighted supply from Comtrade imports.
    """
    if comtrade_df.empty:
        return pd.DataFrame(columns=["partner", "share", "vulnerability", "value_usd", "netweight_kg"])

    # Normalize partner names to match vulnerability_scores
    partner_col = "partnerDesc" if "partnerDesc" in comtrade_df.columns else "partner" if "partner" in comtrade_df.columns else "ptTitle" if "ptTitle" in comtrade_df.columns else None
    value_col = "primaryValue" if "primaryValue" in comtrade_df.columns else "customsVal" if "customsVal" in comtrade_df.columns else "cifvalue" if "cifvalue" in comtrade_df.columns else "TradeValue"
    weight_col = "netWgt" if "netWgt" in comtrade_df.columns else "qty" if "qty" in comtrade_df.columns else None

    if partner_col is None:
        for c in comtrade_df.columns:
            if "partner" in str(c).lower() or "pt" in str(c).lower():
                partner_col = c
                break
    if partner_col is None:
        partner_col = comtrade_df.columns[2] if len(comtrade_df.columns) > 2 else comtrade_df.columns[0]

    # Exclude "World" aggregate row for partner-level shares
    df = comtrade_df[comtrade_df[partner_col].astype(str).str.strip() != "World"].copy()
    df["value_usd"] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)

    agg = df.groupby(partner_col, as_index=False).agg(value_usd=("value_usd", "sum"))
    if weight_col and weight_col in df.columns:
        wagg = df.groupby(partner_col, as_index=False).agg(netweight_kg=(weight_col, "sum"))
        agg = agg.merge(wagg, on=partner_col)
    else:
        agg["netweight_kg"] = pd.NA

    total = float(agg["value_usd"].sum())
    agg["share"] = (agg["value_usd"] / total) if total > 0 else 0
    agg["partner"] = agg[partner_col]
    agg["vulnerability"] = agg["partner"].map(lambda x: vulnerability_scores.get(str(x).strip(), vulnerability_scores.get("Others", 0.1)))
    return agg[["partner", "share", "vulnerability", "value_usd", "netweight_kg"]].copy()


def preprocess_worldbank(wb_df: pd.DataFrame) -> pd.DataFrame:
    """Clean World Bank urea monthly series."""
    if wb_df.empty or "date" not in wb_df.columns:
        return pd.DataFrame(columns=["date", "price_usd"])
    df = wb_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "price_usd"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def preprocess_fpa(fpa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract monthly Philippine urea prices from FPA parse output.
    Uses report_date and raw_text_excerpt; table extraction can be refined after PDF inspection.
    """
    if fpa_df.empty:
        return pd.DataFrame(columns=["date", "price_php_per_50kg", "region"])

    rows = []
    for _, r in fpa_df.iterrows():
        dt = r.get("report_date")
        if pd.isna(dt):
            continue
        text = r.get("raw_text_excerpt", "")
        # Crude price extraction: look for numbers that could be PHP prices (e.g. 1200-2500 range)
        numbers = re.findall(r"\b(1[0-9]{3}|2[0-5][0-9]{2})\b", text)
        if numbers:
            prices = [int(n) for n in numbers if 800 <= int(n) <= 3500]
            if prices:
                rows.append({"date": dt, "price_php_per_50kg": sum(prices) / len(prices), "region": "national"})
    if not rows:
        return pd.DataFrame(columns=["date", "price_php_per_50kg", "region"])
    out = pd.DataFrame(rows)
    out["date"] = pd.to_datetime(out["date"])
    out = out.groupby(out["date"].dt.to_period("M").astype(str)).agg({"price_php_per_50kg": "mean", "region": "first"}).reset_index()
    out["date"] = pd.to_datetime(out["date"].astype(str) + "-01")
    return out


def run_preprocess(
    comtrade_df: pd.DataFrame,
    worldbank_df: pd.DataFrame,
    fpa_df: pd.DataFrame,
    vulnerability_scores: dict[str, float],
    processed_dir: str,
    partner_file: str,
    worldbank_file: str,
    fpa_file: str,
) -> None:
    """Run all preprocessing and save to data_processed/."""
    Path(processed_dir).mkdir(parents=True, exist_ok=True)

    partner_df = preprocess_comtrade(comtrade_df, vulnerability_scores)
    partner_df.to_csv(Path(processed_dir) / Path(partner_file).name, index=False)

    wb_clean = preprocess_worldbank(worldbank_df)
    wb_clean.to_csv(Path(processed_dir) / Path(worldbank_file).name, index=False)

    fpa_clean = preprocess_fpa(fpa_df)
    fpa_clean.to_csv(Path(processed_dir) / Path(fpa_file).name, index=False)
