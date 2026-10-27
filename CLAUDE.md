# MMF1941 Project 1 — A14-03

Commodity-currency transmission across four pairs. Replication-and-generalization
of a soybean→BRL finding: commodity returns explain *same-day* FX returns, but
lagged commodity returns do **not** forecast next-day FX returns.

Daily, 2010–2025. Student: Hashim Khan.

**Authority.** `design_decisions.md` is the specification. This file summarizes
it for working context; where the two disagree, `design_decisions.md` wins.
Background reasoning is in `PHASE_0_PROVENANCE.md` and `PHASE_1_DECISIONS.md`.
Checkpoint status is in `CHECKPOINT.md`.

**Status, 2026-10-26.** Bloomberg Desktop API suspended 2026-10-24 pending
workflow review (`code = -4002`, `category = "LIMIT"`). Terminal screens work;
extraction does not. Supervisor approved proceeding with data in hand. **No pull
is possible — do not propose one as a solution to anything.**

## Pairs

| Currency | Commodity | Instrument | Sample |
|---|---|---|---|
| AUD | Iron ore 62% Fe CFR China | `SCO1 Comdty` (SGX, front-month generic) | 2013-04-09 → 2025-09-19 |
| CAD | WTI | `CL1 Comdty` | 2010-01-05 → 2025-09-19 |
| CLP | Copper | `LMCADS03 Comdty` (LME 3-month) | 2010-01-05 → 2025-09-23 |
| NOK | Brent | `CO1 Comdty` | 2010-01-05 → 2025-09-23 |

Controls: **Fed H.10 broad dollar index** (see below — *not* DXY), `BCOM Index`.

The iron ore ticker was **recovered from returned contract codes** (`SCOJ13` …
`SCOZ5`), not confirmed on `CTM` — `BBG.xlsx` holds values with no surviving
formulas.

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

**Sign (DD-01).** `AUDUSD` is already USD-per-unit. `USDCAD`, `USDCLP`, `USDNOK`
are local-per-USD and must be inverted (`1/x`) before returns, so a positive
return means the commodity currency appreciated in all four pairs.

Automated check: after inversion, every FX return series must correlate
**negatively** with the dollar-factor return. A positive correlation means an
inversion was missed.

**Roll (DD-05).** `CL1`, `CO1` and `SCO1` are front-month pointers, not
contracts. Compute returns only where `FUT_CUR_GEN_TICKER` is unchanged
day-over-day; mark roll days missing.

Verified against the data 2026-10-26: **CL 192 rolls, CO 193, SCO 152** — all
≈12/year over their own windows. `LMCADS03` returns **zero** contract changes,
confirming constant maturity and no roll.

**Horizons and loss (DD-08).** *h* = 1 primary, *h* = 5 prespecified secondary,
**squared-error loss**. Declared 2026-10-26, before any lagged regression. Do not
introduce another horizon or a second loss criterion.

**Orthogonalization (DD-03).** WTI, Brent and COMEX copper are BCOM constituents
(8.85%, 10.58%, 5.92% — MEMB, 2026-09-27). Regress BCOM on the own-commodity
return and use the residual, so it means "broad commodity moves not attributable
to this commodity."

Iron ore is **not** a BCOM constituent, so AUD needs no orthogonalization.
**That does not make AUD the clean pair.** As of D7, AUD is excluded from the
pooled panel and the cross-pair comparison, and reported separately as a
methodological case study — average-price settlement on a smoothed index. See
`design_decisions.md` D7.

Use **HG1 (COMEX)** to orthogonalize BCOM, since COMEX copper is what the index
actually holds. Use **LME** as the CLP regressor. Two different instruments,
two different jobs — this is deliberate.

**Calendar.** Inner join on dates where all required series are valid. Emit an
attrition table at every join stage.

**Dates.** Never let pandas infer a date format from a text file. Formats are
declared per source in `config/project_config.yaml` and in
`data_compile.DATE_FORMATS`; `_finish()` requires one for every CSV read. The
`.xlsx` files carry native Excel datetimes and take no format string.

## Two dollar files. Use the right one.

| File | What it actually is | Role |
|---|---|---|
| `EM-17_USD_Index_DXY_PX-LAST_Daily.csv` | **ICE DXY** — catalog `RL-36290DAB949B` | **primary control**, column `DXY_PX_LAST` |
| `USD_Index_DXY_Daily.csv` | **Fed H.10 broad index**, base Jan 2006 = 100 — MISNAMED, catalog `RL-B4C76E222224` | robustness only, column `USD_BROAD_PX_LAST` |

ICE DXY verified: 77.525 on 2010-01-04, 114.106 on 2022-09-27, 71.329 low 2008,
and **zero missing values** in the study window. The Fed file reads 92.36 and
128.44 on those dates and has 188 missing.

DD-13 was amended 2026-10-26: the earlier substitution assumed ICE DXY was
unobtainable, but it was in the RiskLab library under a different filename.

Because CAD **is** an ICE DXY constituent, the dollar control now partly contains
the dependent variable for that pair. DD-21 (a CAD-excluded dollar factor) is
live again — it was moot under the Fed broad index.

## Known data traps

- **Iron ore is average-settled.** `SCO1` settles on the arithmetic average of
  all IODEX 62% Fe prints in the expiring month — confirmed from the contract
  spec 2026-10-24. With *N* prints in the month and *k* elapsed, pass-through is
  **w = (N−k+1)/N**, so the futures return is a shrinking fraction of the real
  move as the month progresses (observed: mean |return| 1.3% → 0.25%, while WTI
  and Brent stay flat at 1–2%).
  This **inflates** β by roughly 1.5×, not attenuates it, and the real damage is
  to cross-pair comparability — which is the project. **Baseline restricts AUD to
  the first 8 trading days of each contract month** (DD-12, *w* 1.00 → 0.68);
  5 days and the rescaled full sample are robustness. The cutoff comes from the
  empirical decay profile — flat across days 2–7, then falling — which uses the
  commodity series alone, so no FX information entered the choice. A
  day-of-contract-month bucket test runs before the freeze and may legitimately
  move the baseline *on that evidence*.
- **WTI settled at −$37.63 on 2020-04-20.** The log return is undefined **into
  and out of** the print — **two** observations, not one. Excluded and flagged
  (DD-16). Affects CAD only.
- **Three raw files are stored newest-first** — `Crude_Oil_WTI_Spot_Daily.csv`,
  `Commodity_Index_BCOM_Price_Daily.csv`, `Copper_Price_Daily.xlsx`.
  `data_compile._finish()` sorts ascending, so the loaders are safe. Any script
  reading a raw file directly gets **sign-flipped returns**. Use the loaders.
- **Brent `FUT_CUR_GEN_TICKER` is null on 2010-08-30 and 2023-01-02.** Roll
  status is indeterminate, so four observations carry an `indeterminate_roll`
  flag.
- **`USDNOK` has a 2010-01-01 observation.** New Year's Day; FX does not trade;
  every other series starts 2010-01-04. Dropped (DD-20).
- **The copper file's `HG1_Comdty_PX_BID` is unusable** — stale repeating values
  (445 for ~12 consecutive sessions), implied spreads above 5%, scattered
  `#N/A N/A`. Dropped on load. Do not use for transaction costs.
- **HG1 has no `FUT_CUR_GEN_TICKER` column**, so its ~190 monthly contract
  switches cannot be detected and will enter the BCOM orthogonalization for the
  CLP pair. ACCEPTED, not fixed — the effect is second-order (errors-in-variables
  in the first-stage regressor attenuates a loading that is itself only ~6%, so
  `BCOM⊥` under-corrects slightly). Required robustness check: recompute `BCOM⊥`
  using LME copper, which has no roll, and report whether the CLP coefficient
  moves.
- **Two local WTI files disagree** — `Crude_Oil_WTI_Spot_Daily.csv` gives 63.41
  on 2025-09-23, `AT-03` gives 63.69. The adjudicating CL1 pull was never
  executed, but the RiskLab catalog settles it: `RL-20930E28331E` is
  `golden_source = Y`, `validator_status = PASS`, and the local sha256 matches.
  Use the repo file; run `AT-03` as robustness (DD-17).
- **COMEX copper fell 22% on 2025-07-31** (558.60 → 435.45) on a US market
  dislocation absent from LME. This is why LME is the regressor.
- **`AT-03` volume column is unreliable** — CL1 at 18,654 one day and 248,092 the
  next; silver at 400. Do not use.
- **No volume or open-interest field was obtained.** `PX_VOLUME` returned nothing
  on iron ore; `VOLUME` was attempted; unresolved at suspension. Not
  load-bearing — the AUD start is 2013-04-08 because `SCO` has no earlier
  history (absence, not thinness).

## Estimation

Contemporaneous (expect to reject H₀: β=0) and predictive (expect to fail to
reject), same regression, dependent variable led:

```
Δs_{t+h} = α + β·Δc_t + γ·ΔUSD_BROAD_t + δ·ΔBCOM⊥_t + ε
```

Per-pair OLS with Newey–West HAC standard errors. Pooled panel with pair fixed
effects and standard errors **two-way clustered by date and pair** — date
clustering matters because the dollar induces cross-sectional dependence.

Out-of-sample: expanding window against a random walk. Use **Clark–West**, not
Diebold–Mariano — the model nests the random walk and DM's asymptotics assume
non-nested models. **This deviates from the brief, which specifies DM** (DD-11);
it is flagged for the supervisor, not applied silently.

Multiple testing: 4 pairs × 2 directions = 8 tests. Report unadjusted and
Holm-adjusted p-values.

Report a minimum detectable effect alongside the null: "we could have detected
R² of X% at 80% power; we found Y%."

**Bug detector (D6).** The old sanity band (β 0.10–0.25) was removed 2026-10-26:
it had no basis. What remains is a catastrophe gate — **|β| > 0.5 or R² > 0.40**
at daily frequency would mean commodity moves explain most daily FX variation,
which no one has found. That is a sign or alignment bug: say so rather than
reporting it. Do **not** treat any narrower range as an expectation; the
literature prior goes in the discussion, not in the code.

## Layout

```
README.md  design_decisions.md  CLAUDE.md  CHECKPOINT.md
PHASE_0_PROVENANCE.md  PHASE_1_DECISIONS.md
config/project_config.yaml
manifests/   data_manifest.csv  bloomberg_source_log.csv
             field_definitions.csv  sample_attrition.csv
data/        raw_bloomberg/  interim/  analytic/
src/         00_design_freeze … 09_tables_figures
outputs/     tables/  figures/  diagnostics/  models/
data_compile.py
```

`src/` modules are numbered, so their names are not importable identifiers. Load
siblings through `src/_common.load("00_design_freeze")`, never `import`.

Run order: `00_design_freeze` (asserts the spec) -> `01_source_inventory`
(catalog IDs and hashes) -> `03_build_events_or_signals` -> `04_build_outcomes`
-> `05_merge_analysis_panel`.

Aligned to the implementation guide's recommended structure on 2026-10-26
(previously `raw_data/` at the root).

**`data/raw_bloomberg/` is immutable** — never rewrite, re-sort, clean or
re-save anything in it. Derived data goes in `interim/` or `analytic/`, never
beside the source files. SHA-256 hashes for all seven raw files are recorded in
`manifests/bloomberg_source_log.csv`; recompute and compare before the final run.

**Configuration lives in `config/project_config.yaml`.** Import shared constants
from there rather than repeating them in scripts or notebooks.

**`data_compile.py` holds the loader functions.** Use them. Do not re-implement
file reading. They outer-join on date, drop nothing, fill nothing, and return a
parallel status frame (`ok` / `src_na` / `no_row` / `uncovered`) saying *why*
each cell is what it is — the data was pulled with `Fill=#N/A` specifically so
gaps stay visible, and the coverage diagnostics depend on that distinction.

The loaders deliberately **do not** apply the known exclusions above; they load,
they do not clean. Exclusions live in `config/project_config.yaml` under
`frozen.exclusions` and are applied in `src/03_build_events_or_signals` and
`src/04_build_outcomes`.

## Style

Effect sizes in economic units, not stars. "A one-standard-deviation daily
copper move corresponds to a 0.4% same-day CLP appreciation" is a result.
"β is significant at 1%" is not.

Nulls and failed checks stay in the output. Do not quietly drop a diagnostic
that came out badly.
