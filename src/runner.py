"""Orchestrate fetch → preprocess → scenarios → outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import get_project_root, load_config
from .fetch_comtrade import fetch_comtrade
from .fetch_fpa import FPAFetcher
from .fetch_worldbank import fetch_worldbank
from .model import run_scenario
from .plots import plot_scenarios
from .preprocess import run_preprocess
from .scenarios import load_scenarios


def run_pipeline(config_path: str | Path | None = None) -> dict:
    """
    Full pipeline:
    1. Fetch from Comtrade, World Bank, FPA
    2. Preprocess into clean tables
    3. Run all scenarios
    4. Save outputs and figures
    """
    root = get_project_root()
    cfg = load_config(config_path)
    paths = cfg["paths"]
    raw_dir = Path(root) / paths["raw_dir"]
    processed_dir = Path(root) / paths["processed_dir"]
    output_dir = Path(root) / cfg["project"]["output_dir"]
    figures_dir = Path(root) / cfg["project"]["figures_dir"]
    figures_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Fetch ---
    comtrade_df = pd.DataFrame()
    worldbank_df = pd.DataFrame()
    fpa_df = pd.DataFrame()

    if cfg.get("comtrade", {}).get("enabled", True):
        c = cfg["comtrade"]
        comtrade_df, _ = fetch_comtrade(
            reporter_code=c.get("reporter_code", 608),
            commodity_code=c["commodity_code"],
            flow_code=c["flow"],
            start_year=c["start_year"],
            end_year=c["end_year"],
            frequency=c["frequency"],
            raw_subdir=str(raw_dir / Path(c["raw_subdir"]).name),
            api_key_env=c.get("api_key_env", "COMTRADE_API_KEY"),
        )
        print(f"Comtrade: fetched {len(comtrade_df)} records")

    if cfg.get("worldbank", {}).get("enabled", True):
        w = cfg["worldbank"]
        worldbank_df, _ = fetch_worldbank(
            monthly_xlsx_url=w["monthly_xlsx_url"],
            raw_subdir=str(raw_dir / Path(w["raw_subdir"]).name),
            urea_series_name_contains=w.get("urea_series_name_contains", "Urea"),
        )
        print(f"World Bank: fetched {len(worldbank_df)} monthly rows")

    if cfg.get("fpa", {}).get("enabled", True):
        f = cfg["fpa"]
        fetcher = FPAFetcher(
            weekly_index_url=f["weekly_index_url"],
            raw_subdir=str(raw_dir / Path(f["raw_subdir"]).name),
            product_keywords=f.get("product_keywords", ["UREA (PRILLED)", "UREA (GRANULAR)"]),
            max_reports=f.get("max_reports", 80),
        )
        links = fetcher.discover_pdf_links()
        pdf_paths = fetcher.download_pdfs(links)
        fpa_df = fetcher.parse_urea_prices(pdf_paths)
        print(f"FPA: discovered {len(links)} PDFs, parsed {len(fpa_df)} urea rows")

    # --- Preprocess ---
    processed_path = root / paths["processed_dir"]
    run_preprocess(
        comtrade_df=comtrade_df,
        worldbank_df=worldbank_df,
        fpa_df=fpa_df,
        vulnerability_scores=cfg.get("vulnerability_scores", {}),
        processed_dir=str(processed_path),
        partner_file=cfg["comtrade"]["processed_partner_file"],
        worldbank_file=cfg["worldbank"]["processed_price_file"],
        fpa_file=cfg["fpa"]["processed_price_file"],
    )
    print("Preprocess: saved clean tables to data_processed/")

    # --- Load processed ---
    partner_df = pd.read_csv(processed_path / Path(cfg["comtrade"]["processed_partner_file"]).name) if (processed_path / Path(cfg["comtrade"]["processed_partner_file"]).name).exists() else pd.DataFrame()
    wb_df = pd.read_csv(processed_path / Path(cfg["worldbank"]["processed_price_file"]).name) if (processed_path / Path(cfg["worldbank"]["processed_price_file"]).name).exists() else pd.DataFrame()
    wb_df["date"] = pd.to_datetime(wb_df["date"], errors="coerce") if "date" in wb_df.columns else pd.Series()
    ph_df = pd.read_csv(processed_path / Path(cfg["fpa"]["processed_price_file"]).name) if (processed_path / Path(cfg["fpa"]["processed_price_file"]).name).exists() else pd.DataFrame()
    ph_df["date"] = pd.to_datetime(ph_df["date"], errors="coerce") if "date" in ph_df.columns else pd.Series()

    # --- Scenarios ---
    scenarios = load_scenarios(cfg)
    baseline_params = cfg.get("baseline", {})
    n_months = baseline_params.get("simulation_months", 12)

    all_results = []
    for name, scenario in scenarios.items():
        df = run_scenario(
            partner_shares=partner_df,
            world_price=wb_df,
            ph_price=ph_df,
            scenario=scenario,
            baseline_params=baseline_params,
            n_months=n_months,
        )
        all_results.append(df)

    results_df = pd.concat(all_results, ignore_index=True)
    out_csv = output_dir / "scenario_results.csv"
    results_df.to_csv(out_csv, index=False)
    print(f"Scenarios: saved to {out_csv}")

    # --- Plots ---
    plot_scenarios(results_df, str(figures_dir))
    print(f"Figures: saved to {figures_dir}")

    return {"results": results_df, "config": cfg}
