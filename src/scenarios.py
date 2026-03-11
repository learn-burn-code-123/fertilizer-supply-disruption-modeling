"""Scenario definitions: closure path, price shock, shipping delay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ScenarioParams:
    name: str
    closure_path: List[float]  # month index: 0=open, 1=fully closed
    global_price_shock_multiplier: List[float]
    shipping_delay_factor: List[float]


def load_scenarios(params: dict) -> dict[str, ScenarioParams]:
    """Load scenario definitions from params."""

    scenarios = params.get("scenarios", {})
    out = {}
    for name, cfg in scenarios.items():
        out[name] = ScenarioParams(
            name=name,
            closure_path=cfg.get("closure_path", []),
            global_price_shock_multiplier=cfg.get("global_price_shock_multiplier", []),
            shipping_delay_factor=cfg.get("shipping_delay_factor", []),
        )
    return out
