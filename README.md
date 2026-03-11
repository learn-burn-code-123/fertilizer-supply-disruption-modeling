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

## Scenarios

- **baseline**: No closure
- **severe_2m**: Severe 2-month closure with price spike and shipping delays
- **partial_6m**: Partial 6-month disruption

Vulnerability scores in `params.yaml` map partner countries to Hormuz exposure (1.0 = fully dependent on Strait, 0.1 = low exposure).
