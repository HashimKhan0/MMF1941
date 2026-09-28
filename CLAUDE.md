# MMF1941 Project 1 — A14-03

Commodity-currency transmission across four pairs. Replication-and-generalization
of a soybean→BRL finding: commodity returns explain *same-day* FX returns, but
lagged commodity returns do **not** forecast next-day FX returns.

Daily, 2010–2025. Student: Hashim Khan.

## Pairs

| Currency | Commodity | Instrument |
|---|---|---|
| AUD | Iron ore | SGX TSI 62% Fe front-month generic |
| CAD | WTI | `CL1 Comdty` |
| CLP | Copper | `LMCADS03 Comdty` (LME 3-month) |
| NOK | Brent | `CO1 Comdty` |

Controls: `DXY Curncy`, `BCOM Index`.

## THE RULE — read this before suggesting any modelling change

**Specifications are frozen in `design_decisions.md` before estimation.**

Do not propose or adopt a specification because it fits better, has a higher
R², a better t-stat, or a nicer out-of-sample result. That includes: changing
the lag, changing the sample window, adding or dropping a control, switching
the return definition, or winsorizing — if the reason is "the result improves."

If a change seems warranted on *methodological* grounds, say so explicitly,
state the reason, and flag that it needs recording in `design_decisions.md`
before it is applied. Never silently swap a spec.

Half this project's contribution is a **null result** on the predictive side.
A null is only credible if the specification was fixed in advance and the test
had power. Spec-shopping destroys both.

## Conventions — non-negotiable

**Sign.** `AUDUSD` is already USD-per-unit. `USDCAD`, `USDCLP`, `USDNOK` are
local-per-USD and must be inverted (`1/x`) before returns, so a positive return
means the commodity currency appreciated in all four pairs.

Automated check: after inversion, every FX return series must correlate
**negatively** with the DXY return. A positive correlation means an inversion
was missed.

**Roll.** `CL1`, `CO1` and the iron ore generic are front-month pointers, not
contracts. Compute returns only where `FUT_CUR_GEN_TICKER` is unchanged
day-over-day; mark roll days missing. Expect ~190 roll days over the sample
(~12/year). `LMCADS03` is constant-maturity and has **no** roll.

**Orthogonalization.** WTI, Brent and COMEX copper are BCOM constituents
(10.58%, 8.85%, 5.92% — MEMB, 2026-09-27). Regress BCOM on the own-commodity
return and use the residual as the control, so it means "broad commodity moves
not attributable to this commodity."

Iron ore is **not** a BCOM constituent — AUD needs no orthogonalization and is
the clean pair.

Use **HG1 (COMEX)** to orthogonalize BCOM, since COMEX copper is what the index
actually holds. Use **LME** as the CLP regressor. Two different instruments,
two different jobs — this is deliberate.

**Calendar.** Inner join on dates where all required series trade. Emit an
attrition table at every join stage.

**Dates.** Never let pandas infer a date format from a text file. Formats differ
per source, so state the format explicitly for every CSV read.

The copper file is **`.xlsx` with native Excel dates**, so it needs no format
string — openpyxl/pandas return real datetimes. Do not add a `format=` argument
there. `EM-27_CLP` (CSV) is `YYYY-MM-DD`. Fresh Bloomberg pulls were saved as
`YYYY-MM-DD`.

## Known data traps

- **WTI settled at −$37.63 on 2020-04-20.** Log returns are undefined on a
  negative price. Decide explicitly (simple returns / exclude / winsorize) and
  record it. This affects CAD and no other pair.
- **The copper file's `HG1_Comdty_PX_BID` is unusable** — stale repeating values
  (445 for ~12 consecutive sessions), implied spreads above 5%, scattered
  `#N/A N/A`. Drop it on load. Do not use for transaction costs.
- **HG1 has no `FUT_CUR_GEN_TICKER` column**, so its ~190 monthly contract
  switches cannot be detected and will enter the BCOM orthogonalization for the
  CLP pair. ACCEPTED, not fixed — the effect is second-order (errors-in-variables
  in the first-stage regressor attenuates a loading that is itself only ~6%, so
  `BCOM⊥` under-corrects slightly). Required robustness check: recompute `BCOM⊥`
  using LME copper, which has no roll, and report whether the CLP coefficient
  moves. Record the acceptance in `design_decisions.md`.
- **Two local WTI files disagree** — `CrudeOil_WTI_Price_Daily.csv` gives 63.41
  on 2025-09-23, `AT-03` gives 63.69. Golden source resolved by a fresh CL1 pull;
  see `raw_data/bloomberg_source_log.csv`.
- **COMEX copper fell 22% on 2025-07-31** (558.60 → 435.45) on a US market
  dislocation absent from LME. This is why LME is the regressor.
- **`AT-03` volume column is unreliable** — CL1 at 18,654 one day and 248,092 the
  next; silver at 400. Do not use.
- **CAD is ~9.1% of DXY.** The dollar control partly contains the dependent
  variable for that pair. Build a CAD-excluded dollar factor, or flag it.

## Estimation

Contemporaneous (expect to reject H₀: β=0) and predictive (expect to fail to
reject), same regression, dependent variable led one day:

```
Δs_{t+h} = α + β·Δc_t + γ·ΔDXY_t + δ·ΔBCOM⊥_t + ε
```

Per-pair OLS with Newey–West HAC standard errors. Pooled panel with pair fixed
effects and standard errors **two-way clustered by date and pair** — date
clustering matters because the dollar induces cross-sectional dependence.

Out-of-sample: expanding window against a random walk. Use **Clark–West**, not
Diebold–Mariano — the model nests the random walk and DM's asymptotics assume
non-nested models.

Multiple testing: 4 pairs × 2 directions = 8 tests. Report unadjusted and
Holm-adjusted p-values.

Report a minimum detectable effect alongside the null: "we could have detected
R² of X% at 80% power; we found Y%."

**Sanity band:** daily contemporaneous elasticities should land ~0.1–0.25 with
R² ~5–25%. If β ≈ 0.9 or R² ≈ 60%, there is a sign or alignment bug — say so
rather than reporting it.

## Layout

Actual layout in this repo:

```
raw_data/        source CSVs + bloomberg_source_log.csv
data_compile.py  loader functions
CLAUDE.md
design_decisions.md
```

**The raw CSVs in `raw_data/` are immutable** — never rewrite, re-sort, clean or
re-save them. `bloomberg_source_log.csv` lives in the same folder and *is*
editable; it's the one exception. Everything else written there is a mistake.

Derived data (cleaned series, merged panel, attrition tables, figures) goes in
its own directory, never beside the source CSVs.

Note: the project implementation guide recommends `data/raw_bloomberg/`,
`manifests/` and `src/00_design_freeze … 09_tables_figures`. This repo diverges.
That's fine as a working choice, but either align the paths before submission or
record the deviation — the guide's completion checklist refers to those
manifest paths by name.

**`data_compile.py` already holds loader functions** that read the raw CSVs into
DataFrames. Use them. Do not re-implement file reading in new scripts. If a
loader does date inference, forward-fill, `dropna`, or silent dtype coercion,
say so before building on it — the data was pulled with `Fill=#N/A` specifically
so gaps stay visible, and a loader that fills them defeats every coverage
diagnostic downstream.

## Style

Effect sizes in economic units, not stars. "A one-standard-deviation daily
copper move corresponds to a 0.4% same-day CLP appreciation" is a result.
"β is significant at 1%" is not.

Nulls and failed checks stay in the output. Do not quietly drop a diagnostic
that came out badly.
