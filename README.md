# MMF1941 Project 1 — A14-03

**Commodity-Currency Transmission Beyond a Single Pair: A Multi-Pair Replication**
Khan, Hashim · FX & currencies (A14) · Asset classes (C4)

Does the contemporaneous-strong / predictively-weak commodity→currency pattern
generalize from soybean→BRL to **AUD–iron ore, CAD–WTI, CLP–copper, NOK–Brent**
at daily frequency, net of broad-dollar and broad-commodity controls?

**Hypothesis.** Each pair shows significant contemporaneous transmission that
survives the controls, while the predictive (lagged) direction is a null.

Half the contribution is that null. A null is only credible if the specification
was fixed in advance and the test had power — see **THE RULE** below.

---

## Layout

```
MMF1941/
  README.md                     this file
  FREEZE.md                     specification freeze: SHA-256 of every spec file and raw input
  design_decisions.md           frozen specification; the authority for every choice
  CLAUDE.md                     working context for AI assistance; must stay at root
  rqmts.txt                     environment record
  project_1.md                  the proposal
  project_1_details.md          the brief
  config/
    project_config.yaml         every shared constant; import, never repeat
  manifests/
    data_manifest.csv           one row per construct, 18 columns
    bloomberg_source_log.csv    one row per pulled series, 17 columns
    source_inventory.csv        raw files resolved against the RiskLab catalog
    source_inventory_rejected.csv  catalog records considered and rejected
    field_definitions.csv       mnemonic definitions and verification status
    sample_attrition.csv        rows surviving each join stage, per pair
    forecast_origins.csv        information available at each origin
    variable_dictionary.csv
  data/
    raw_bloomberg/              IMMUTABLE source files
      PROVENANCE.md             origin of each raw file; which may be uploaded
    interim/                    cleaned series
    analytic/                   merged estimation panel
  src/
    00_design_freeze            estimand, windows, exclusions, sign conventions
    01_source_inventory
    02_raw_validation           schemas, timestamps, duplicates, missingness
    03_build_events_or_signals  commodity returns, rolls, pass-through weights
    04_build_outcomes           FX returns, convention A
    05_merge_analysis_panel     audited join, emits attrition
    06_descriptive_diagnostics
    07_primary_estimation       frozen baseline only
    08_robustness               prespecified alternatives and placebos
    08b_rf_dsr                  walk-forward random forest, deflated Sharpe
    08c_costs                   transaction costs on the forest strategy
    09_tables_figures
  outputs/
    tables/  figures/  diagnostics/  models/
  paper/
    paper.tex  paper.pdf        the write-up
  working/                      notes and exploration; not part of the archive
    CHECKPOINT.md
    claude_notes.md
    PHASE_0_PROVENANCE.md       what the raw files establish
    PHASE_1_DECISIONS.md        reasoning behind the decisions, long form
    eda_0.ipynb
    eda_1_data_validation.ipynb
    prelim/
  data_compile.py               loader functions — use these, do not re-implement
```

`working/` holds the reasoning trail: superseded plans, exploratory notebooks and
long-form notes. Nothing in the pipeline reads from it. The archive the guide
asks for is everything outside it.

`data/raw_bloomberg/` is **immutable**. Never rewrite, re-sort, clean or re-save
anything in it. Derived data goes to `interim/` or `analytic/`, never beside the
source files.

---

## THE RULE

**Specifications are frozen in `design_decisions.md` before estimation.**

Do not adopt a specification because it fits better, has a higher R², a better
t-statistic, or a nicer out-of-sample result. That includes changing the lag, the
sample window, the controls, the return definition, or winsorizing — if the
reason is "the result improves."

A change on **methodological** grounds is allowed. Say so explicitly, state the
reason, and record it in `design_decisions.md` **before** applying it. Never
silently swap a spec.

---

## Conventions

**Sign (DD-01).** Everything is quoted in USD; USD is always the quote currency.
`AUDUSD` is already USD-per-unit. `USDCAD`, `USDCLP`, `USDNOK` are
local-per-USD and must be inverted (`1/x`) before returns. β is expected
**positive** in all four pairs.

*Automated check:* after inversion every FX return series must correlate
**negatively** with the dollar-factor return. A positive correlation means an
inversion was missed.

**Roll (DD-05).** Compute returns only where `FUT_CUR_GEN_TICKER` is unchanged
day-over-day; mark roll days missing. Verified: CL 192 rolls, CO 193, SCO 152 —
all ≈12/year. `LMCADS03` has **zero** and needs no roll treatment.

**Orthogonalization (DD-03).** WTI, Brent and COMEX copper are BCOM constituents
(8.85%, 10.58%, 5.92%). Regress BCOM on the own-commodity return and use the
residual. Iron ore is not a constituent, so AUD needs no orthogonalization.
Orthogonalize copper against **HG1 (COMEX)**, since that is what the index holds,
while **LME** remains the CLP regressor — two instruments, two jobs, deliberate.

**Dates.** Never infer a date format from a text file. State the format
explicitly per CSV; the formats live in `config/project_config.yaml`. The `.xlsx`
files carry native Excel datetimes and need no format string.

**Calendar.** Inner join on dates where all required series are valid. Emit an
attrition table at every stage.

---

## The dollar control is not DXY

`USD_Index_DXY_Daily.csv` is the **Federal Reserve H.10 nominal broad dollar
index**, base January 2006 = 100 — not ICE DXY. It reads 101.4155 on 2006-01-02,
92.36 on 2010-01-04 (DXY: ~77.5) and peaks at 128.45 in 2022 (DXY: ~114), with
gaps on US federal holidays.

**Superseded 2026-10-26.** Genuine ICE DXY was in the library under a different
filename (`EM-17_USD_Index_DXY_PX-LAST_Daily.csv`, catalogue `RL-36290DAB949B`)
and is now the primary control, column `DXY_PX_LAST`. The Fed H.10 broad index
above is retained as a robustness control under `USD_BROAD_PX_LAST` — still
misnamed on disk, so never call that file DXY. See D3.

---

## Known data traps

| | |
|---|---|
| **WTI 2020-04-20 = −37.63** | Log return undefined **into and out of** the print — two observations. CAD only. DD-16 |
| **Iron ore is average-settled** | Settles on the arithmetic average of the month's IODEX prints. Pass-through is (N−k+1)/N, so the futures return is a shrinking fraction of the real move as the month progresses. **Inflates** β ~1.5×, breaks cross-pair comparability. DD-12 |
| **`HG1_Comdty_PX_BID` is unusable** | Stale repeats (445 for ~12 sessions), implied spreads >5%, scattered `#N/A N/A`. Dropped on load |
| **`HG1` has no contract field** | ~190 rolls undetectable; enters the CLP BCOM orthogonalization. Accepted, second-order. Robustness recomputes `BCOM⊥` with LME |
| **Three raw files are stored descending** | WTI, BCOM and HG1 are newest-first. `data_compile._finish()` sorts, but a script reading a raw file directly gets sign-flipped returns. Use the loaders |
| **Brent null contract codes** | 2010-08-30 and 2023-01-02 — roll status indeterminate on four observations |
| **NOK 2010-01-01** | New Year's Day; FX does not trade. Dropped |
| **Two WTI files disagree** | 63.41 vs 63.69 on 2025-09-23. Unadjudicated — the pull was never executed. DD-17 |
| **COMEX copper −22% on 2025-07-31** | A US tariff dislocation absent from LME. This is why LME is the regressor |
| **`AT-03` volume is unreliable** | CL1 at 18,654 then 248,092; silver at 400. Do not use |

---

## Sample

| Pair | Start | End | Binding constraint | Final N (contemp.) |
|---|---|---|---|---|
| AUD | 2013-04-09 | 2025-09-19 | AT-04 FX | 2,909 |
| CAD | 2010-01-05 | 2025-09-19 | AT-04 FX | 3,706 |
| CLP | 2010-01-05 | 2025-09-23 | BCOM | 3,598 |
| NOK | 2010-01-05 | 2025-09-23 | BCOM | 3,708 |

AUD starts 2013-04-08 because the `SCO` contract has no earlier history.
Extending the window to 2025-12-31 needs exactly two re-pulls — AT-04 FX and
BCOM — once Bloomberg API access is restored. Every Bloomberg-pulled series
already reaches year end.

---

## Estimation

$$\Delta s_{t+h} = \alpha + \beta\,\Delta c_t + \gamma\,\Delta \text{USD}^{\text{broad}}_t + \delta\,\Delta \text{BCOM}^{\perp}_t + \varepsilon_{t+h}$$

Contemporaneous (*h*=0, expect to reject H₀: β=0) and predictive (*h*=1 primary,
*h*=5 secondary; expect to fail to reject).

Per-pair OLS with Newey–West HAC errors. Pooled panel with pair fixed effects and
errors from **Driscoll–Kraay** (D1, amended 2026-10-26). Two-way clustering was
the frozen choice but needs the cluster count to grow in both dimensions and the
panel has three pairs; a Monte Carlo put its size at 0.5% against a nominal 5%.
The frozen two-way result is still reported on every pooled row. AUD is excluded
from the pooled panel (D7).

Out-of-sample: expanding window against a random walk, **Clark–West not
Diebold–Mariano** (the model nests the benchmark; DM assumes non-nested). This
deviates from the brief and is flagged in DD-11.

Multiple testing: **6 tests** — {CAD, CLP, NOK} × {h=0, h=1} — Holm-adjusted and
unadjusted both reported. Six rather than eight because AUD is reported
separately as a case study (D7).

Report a **minimum detectable effect** alongside the null: *"we could have
detected R² of X% at 80% power; we found Y%."*

**Sanity band.** Daily contemporaneous elasticities should land ~0.10–0.25 with
R² ~5–25%. If β ≈ 0.9 or R² ≈ 60%, there is a sign or alignment bug — say so
rather than reporting it.

---

## Status

Bloomberg Desktop API **suspended 2026-10-24** pending workflow review
(`category = "LIMIT"`). Terminal screens work; extraction does not. Supervisor
approved proceeding with data in hand on 2026-10-26.

Open items are listed in `design_decisions.md` §4. The largest is **DD-18**
(settlement times and the timing gap), which is blocked on exchange published
specifications rather than on Bloomberg.

---

## Style

Effect sizes in economic units, not stars. *"A one-standard-deviation daily
copper move corresponds to a 0.4% same-day CLP appreciation"* is a result.
*"β is significant at 1%"* is not.

Nulls and failed checks stay in the output. Do not quietly drop a diagnostic that
came out badly.
