"""Generate scenario comparison figures."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def plot_scenarios(results_df: pd.DataFrame, figures_dir: str) -> None:
    """Plot supply index and Philippine price by scenario."""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        return

    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    sns.set_style("whitegrid")

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    for scenario in results_df["scenario"].unique():
        sub = results_df[results_df["scenario"] == scenario]
        axes[0].plot(sub["month"], sub["supply_index"], marker="o", label=scenario, markersize=4)
        axes[1].plot(sub["month"], sub["ph_price_php"], marker="o", label=scenario, markersize=4)

    axes[0].set_ylabel("Supply index")
    axes[0].set_title("Monthly supply index (1 = normal)")
    axes[0].legend()
    axes[0].set_ylim(0, 1.1)

    axes[1].set_ylabel("Philippine price (PHP/kg)")
    axes[1].set_xlabel("Month")
    axes[1].set_title("Philippine urea retail price (PHP per 50 kg bag)")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(Path(figures_dir) / "scenario_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
