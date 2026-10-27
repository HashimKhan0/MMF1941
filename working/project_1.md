# Commodity-Currency Transmission Beyond a Single Pair: A Multi-Pair Replication

- Student: Khan, Hashim
- Assignment: Project 1
- Proposal ID: A14-03
- Official area: A14 — FX & currencies
- Official category: C4 — Asset classes
- Data not ready: 100.0%
- Estimated data not available locally: 50.0%

## Main research question

Does the contemporaneous-strong / predictively-weak commodity->currency pattern (soybean->BRL, project 12) generalize to AUD-iron ore, CAD-WTI, CLP-copper, NOK-Brent at daily frequency, net of broad-dollar (DXY) and broad-commodity (BCOM)?

## Testable hypothesis

Each pair shows a significant contemporaneous commodity->FX transmission that survives DXY+BCOM controls, while the predictive (lagged) direction is a null.

## Why this project was selected

The project offers a focused, falsifiable question with an interpretable economic mechanism. Its hypothesis is falsifiable and the required market data can be assembled without asking the student to acquire high-frequency data.

## Study design

- Primary assets: AUD, CAD, CLP, NOK vs USD + matched commodity indices.
- Traditional method: Per-pair HAC-OLS with DXY/BCOM controls; pooled panel with pair FE; predictive OOS (Diebold-Mariano) for the null direction.
- ML or robustness method: Walk-forward RF for the predictive direction vs random walk; DSR. Robustness.
- Sample or event window: ~2010-2025 daily.
- Expected result type: positive (contemporaneous) + honest-null (predictive)
- Proposal feasibility: GO-after-pull (daily FX + commodity series)

## Data plan

### Bloomberg acquisition by the student

Daily AUD, CAD, CLP and NOK spot rates; iron ore, WTI, copper and Brent prices; BCOM and DXY.

The Bloomberg extraction must be end-of-day, daily, weekly, monthly, quarterly, annual, document, or event/reference data only. Record terminal function, security or series identifier, field, frequency, date range, currency, adjustment convention and extraction date in a source log.

### Data already available in RiskLab

1. Mixed local/external: daily FX spot (AUD,CAD,CLP,NOK) -> 02_market/fx [not local BBG/Datastream]
2. Mixed local/external: commodity prices (iron ore, WTI, copper, Brent) + BCOM, DXY -> 04_macro/commodities, 02_market [partial coverage or preparation/not local]

### Local data needing preparation

1. commodity prices (iron ore, WTI, copper, Brent) + BCOM, DXY -> 04_macro/commodities, 02_market [partial coverage or preparation/not local]

### Data not currently available locally

1. Mixed local/external: daily FX spot (AUD,CAD,CLP,NOK) -> 02_market/fx [not local BBG/Datastream]
2. Mixed local/external: commodity prices (iron ore, WTI, copper, Brent) + BCOM, DXY -> 04_macro/commodities, 02_market [partial coverage or preparation/not local]

### High-frequency data rule

No high-frequency Bloomberg extraction is authorized. If high-frequency data becomes useful later, check `C:\risklab\data\intraday_data` first and use only the local archive.

## Minimum outputs

1. A source and field dictionary for every Bloomberg series and every local file used.
2. A reproducible cleaning and merge script with point-in-time and adjustment conventions stated explicitly.
3. Descriptive coverage, missingness and identifier-join diagnostics before estimation.
4. The traditional specification, the stated robustness method and economically interpretable effect sizes.
5. A concise paper draft that preserves null or failed results and distinguishes exploratory from confirmatory analysis.
