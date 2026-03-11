# Hormuz–Philippine Urea Scenario Model

A monthly scenario simulation of how a closure of the Strait of Hormuz affects Philippine urea supply and price over time. This is a **scenario model**, not a forecasting model.

## Data Sources (Open-Source)

| Source | Data | Method |
|--------|------|--------|
| **UN Comtrade** | Philippine urea imports by partner country (HS 310210) | API via `comtradeapicall` |
| **World Bank** | Monthly global urea benchmark price (Pink Sheet) | Direct Excel download |
| **FPA** | Weekly Philippine fertilizer retail prices | Scrape index → download PDFs → parse |

## Setup

```bash
cd hormuz-ph-urea
pip install -r requirements.txt
```

**Optional:** For full Comtrade data (>500 records), set `COMTRADE_API_KEY` (free registration at [comtradedeveloper.un.org](https://comtradedeveloper.un.org)).

## Usage

```bash
python main.py
```

This will:
1. Fetch Philippine urea imports by partner from Comtrade
2. Download World Bank monthly urea price Excel
3. Scrape FPA weekly-prices page, download PDFs, parse urea prices
4. Preprocess into clean tables in `data_processed/`
5. Run baseline and closure scenarios
6. Write outputs and figures to `outputs/`

## Project Structure

```
hormuz-ph-urea/
├── README.md
├── requirements.txt
├── main.py
├── params.yaml
├── data_raw/           # Auto-downloaded by pipeline (do not add hand-made CSVs)
│   ├── comtrade/
│   ├── worldbank/
│   └── fpa/
├── data_processed/     # Cleaned CSVs created by code
├── outputs/
│   └── figures/
└── src/
    ├── config.py
    ├── fetch_comtrade.py
    ├── fetch_worldbank.py
    ├── fetch_fpa.py
    ├── preprocess.py
    ├── scenarios.py
    ├── model.py
    ├── runner.py
    └── plots.py
```

## Model Logic

### Monthly Supply Index

The supply index measures available urea supply relative to normal (1.0 = normal, lower = disrupted). For each month:

```
supply_index = max(0.15, min(1.0, 1.0 - vuln_weighted_share × closure - delay))
```

- **vuln_weighted_share**: Sum of (partner import share × vulnerability score) across all Philippine urea import partners. Uses Comtrade data; partners like Qatar and Saudi Arabia (Hormuz-dependent) have vulnerability 1.0; Indonesia, Malaysia, China have 0.1.
- **closure**: Scenario-specific value 0–1 per month (0 = Strait open, 1 = fully closed). The share of imports from Hormuz-dependent partners is effectively lost when closure = 1.
- **delay**: Scenario-specific shipping delay factor (0–0.2) that further reduces effective supply during and after closure.
- **0.15**: Minimum floor so supply never goes to zero.

### Philippine Urea Retail Price (PHP per 50 kg bag)

Retail prices respond to global price shocks and local supply pressure:

```
world_price = base_world × global_price_shock_multiplier
pass_through = world_price / base_world
supply_pressure = 1 / supply_index
ph_price = base_ph × (1 + β × (pass_through - 1) × scale) × (1 + β × (supply_pressure - 1) × 0.5)
```

- **base_world**: Latest World Bank urea price (USD). **base_ph**: Latest FPA Philippine retail price (PHP/50 kg).
- **global_price_shock_multiplier**: Scenario-specific multiplier (e.g. 1.25 = 25% spike) reflecting global market reaction to closure.
- **β (beta)**: Price pass-through elasticity (default 0.6). Controls how much global and supply shocks translate into retail prices.

### Scenario Drivers

Each scenario defines three 12-month series in `params.yaml`:

| Parameter | Role |
|-----------|------|
| **closure_path** | 0–1 per month: severity of Strait closure (1 = full closure) |
| **global_price_shock_multiplier** | Multiplier on world urea price (e.g. 1.25 = 25% spike) |
| **shipping_delay_factor** | Extra supply reduction from delays (0–0.2) |

**Severe** scenarios use closure = 1.0 during the disruption, larger price spikes (up to 1.25×), and higher delay factors. **Partial** scenarios use closure = 0.6 and gentler shocks.

## Scenarios

- **baseline**: No closure
- **severe_1m**: Severe 1-month closure with price spike and shipping delays
- **severe_2m**: Severe 2-month closure with price spike and shipping delays
- **severe_3m**: Severe 3-month closure with price spike and shipping delays
- **severe_6m**: Severe 6-month closure with price spike and shipping delays
- **partial_1m**: Partial 1-month disruption
- **partial_2m**: Partial 2-month disruption
- **partial_3m**: Partial 3-month disruption
- **partial_6m**: Partial 6-month disruption

Vulnerability scores in `params.yaml` map partner countries to Hormuz exposure (1.0 = fully dependent on Strait, 0.1 = low exposure).
