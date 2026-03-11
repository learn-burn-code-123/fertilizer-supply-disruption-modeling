"""Monthly scenario simulation: supply impact and price pass-through."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .scenarios import ScenarioParams


def run_scenario(
    partner_shares: pd.DataFrame,
    world_price: pd.DataFrame,
    ph_price: pd.DataFrame,
    scenario: ScenarioParams,
    baseline_params: dict,
    n_months: int = 12,
) -> pd.DataFrame:
    """
    Simulate monthly supply and price for one scenario.
    Returns DataFrame with columns: month, supply_index, world_price, ph_price, scenario.
    """
    beta = baseline_params.get("price_pass_through_beta", 0.6)
    scale = baseline_params.get("pass_through_scale", 1.0)
    min_arrivals = baseline_params.get("minimum_arrivals_index", 0.15)

    if partner_shares.empty:
        vuln_weighted_share = 0.5  # default if no data
    else:
        vuln_weighted_share = (partner_shares["share"] * partner_shares["vulnerability"]).sum()

    results = []
    base_world = world_price["price_usd"].iloc[-1] if not world_price.empty else 400.0
    base_ph = ph_price["price_php_per_50kg"].iloc[-1] if not ph_price.empty and "price_php_per_50kg" in ph_price.columns else 1500.0

    for m in range(n_months):
        closure = scenario.closure_path[m] if m < len(scenario.closure_path) else 0
        shock = scenario.global_price_shock_multiplier[m] if m < len(scenario.global_price_shock_multiplier) else 1.0
        delay = scenario.shipping_delay_factor[m] if m < len(scenario.shipping_delay_factor) else 0

        # Supply: vulnerable share is disrupted by closure
        supply_index = max(min_arrivals, 1.0 - vuln_weighted_share * closure + (1 - vuln_weighted_share))
        supply_index = max(min_arrivals, min(1.0, supply_index - delay))

        # World price with shock
        world_p = base_world * shock

        # Philippine price: pass-through from world + local supply effect
        pass_through = world_p / base_world if base_world > 0 else 1.0
        supply_pressure = 1.0 / supply_index if supply_index > 0 else 1.0
        ph_p = base_ph * (1 + beta * (pass_through - 1) * scale) * (1 + beta * (supply_pressure - 1) * 0.5)

        results.append({
            "month": m + 1,
            "supply_index": supply_index,
            "world_price_usd": world_p,
            "ph_price_php": ph_p,
            "closure": closure,
            "scenario": scenario.name,
        })

    return pd.DataFrame(results)
