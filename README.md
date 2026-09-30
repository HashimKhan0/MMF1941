# Commodity-Currency Transmission Beyond a Single Pair

**MMF1941 · Project 1 · University of Toronto, Master of Mathematical Finance** — *in progress*

A replication-and-generalization study. Earlier work on soybeans → BRL found a clear asymmetry: same-day commodity returns explain currency returns well, but lagged commodity returns do not forecast next-day currency returns. This project asks whether that pattern is a general property of commodity currencies or an artifact of one pair.

## Research question

Does the *contemporaneous-strong / predictively-weak* commodity → currency pattern hold across four more pairs at daily frequency (~2010–2025), net of broad-dollar and broad-commodity moves?

| Currency | Commodity |
|---|---|
| AUD | Iron ore |
| CAD | WTI crude |
| CLP | Copper |
| NOK | Brent crude |

## Hypotheses

- **H1 — Contemporaneous (expect to reject β = 0):**
  `Δs_t = α + β·Δc_t + γ·ΔDXY_t + δ·ΔBCOM⊥_t + ε_t`, estimated with Newey–West (HAC) standard errors. β is read as an elasticity.
- **H2 — Predictive (expect to fail to reject):** the same specification with `Δs_{t+1}` on the left-hand side.

A null on H2 is treated as a legitimate result, so the design is built to make it credible:

- report a minimum detectable effect (power analysis);
- move the predictive test out-of-sample (expanding window vs. a random walk, Clark–West test — the model nests the random walk, so Diebold–Mariano does not apply — plus Campbell–Thompson OOS R²);
- report unadjusted and Holm-adjusted p-values across 4 pairs × 2 directions.

## Methodology notes

- **Controls:** DXY for the dollar; BCOM *orthogonalized* against each pair's own commodity (`BCOM⊥`), since WTI, Brent and copper are BCOM constituents.
- **Robustness:** walk-forward random forest for the predictive direction, a pooled panel with pair fixed effects (standard errors two-way clustered by date and pair), and a CLP central-bank-intervention subsample.
- **Futures rolls:** returns are computed only when the generic contract is unchanged between days (`FUT_CUR_GEN_TICKER`); roll days are marked missing rather than back-adjusted.
- **Snap-time alignment:** FX fixing times vs. commodity settlement times are documented explicitly, since a mismatch can manufacture spurious predictability.

## Repository layout

```
data_compile.py              # loads raw Bloomberg / local extracts into date-indexed frames
                             #   + per-cell status frames (ok / src_na / no_row / uncovered)
src/02_raw_validation.py     # per-series integrity checks and >5σ return flags
eda_0.ipynb                  # first look at the data
eda_1_data_validation.ipynb  # shape, levels/returns, quality flags, roll detection, missingness
outputs/diagnostics/         # CSV outputs from the validation stage
project_1.md                 # project proposal and data plan
claude_notes.md              # working notes: design decisions, data status, extraction plan
```

## Data

Daily FX spot, commodity futures (generic front month), BCOM and DXY, pulled from Bloomberg (end-of-day only) plus local RiskLab files. **Raw data is not included** in this repository (`raw_data/` is git-ignored) due to licensing.

## Setup

```bash
pip install -r rqmts.txt
# place raw extracts in ./raw_data/ then:
python src/02_raw_validation.py
```

## Status

- [x] Data loading and provenance tracking
- [x] Raw-data validation and diagnostics
- [ ] Return construction and convention lock-in (sign, snap times, calendar)
- [ ] Contemporaneous and predictive estimation
- [ ] Robustness and paper draft
