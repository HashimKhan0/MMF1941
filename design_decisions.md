# design_decisions.md

**MMF1941 Project 1 · A14-03 · Khan, Hashim**
Commodity-Currency Transmission Beyond a Single Pair

Seven decisions. Each is signed once. Anything touching the estimand was written
before it was run — that is the whole point of this file, and the reason the
predictive null is worth anything.

Guide: *"Do not choose among these alternatives by comparing final significance
or performance."* No entry here may change after the freeze except by a dated
line in §Amendments.

**Status: 7 decided · 1 open · FROZEN 2026-10-26**

> **On supervisor sign-off.** The guide asks for an approving supervisor on each
> decision. None was available before the freeze. The signature lines are
> therefore blank and remain blank — they are **not** to be back-filled.
>
> What actually makes a null credible is that the specification was fixed
> **before any estimate existed**, and that is independently verifiable here:
> `FREEZE.md` records the SHA-256 of every specification file at the moment of
> freezing, and the git history shows the freeze commit precedes the first
> estimation commit. That is a stronger claim than a signature, because it can
> be checked rather than taken on trust.
>
> Every decision below was still made on the stated grounds — mechanism, the
> guide's requirements, or what the data forced — and never by comparing
> results. Where a choice remained genuinely open (D6), the reasoning for the
> option taken is recorded in full alongside the ones rejected.

**Context.** Bloomberg Desktop API suspended 2026-10-24 (`LIMIT`, workflow
review). Terminal screens work; extraction does not. Supervisor approved
proceeding with data in hand, 2026-10-26.

---

## D1 · Specification

**Estimand.** Observational unit: currency-day. Outcome: log spot FX return under
D2. Signal: matched commodity log return. Benchmark: random walk plus dollar and
orthogonalized broad-commodity controls.

$$\Delta s_{t+h} = \alpha + \beta\,\Delta c_t + \gamma\,\Delta \text{DXY}_t + \delta\,\Delta \text{BCOM}^{\perp}_t + \varepsilon_{t+h}$$

**Sample.** 2010-01-01 to 2025-12-31 requested. Realised ends are set by the
binding source, not by choice: AUD and CAD at **2025-09-19** (AT-04 FX file),
CLP and NOK at **2025-09-23** (BCOM). All Bloomberg-pulled series reach year end,
so extending needs exactly two re-pulls.

**Horizons and loss.** *h* = 0 contemporaneous; *h* = 1 primary predictive;
*h* = 5 prespecified secondary. **Squared-error loss**, applied identically to
benchmark and candidate on identical test dates. MAE reported as a descriptive,
never as a second criterion.

*The predictive null is half the contribution. A horizon or loss chosen after
seeing output makes it worthless.*

**Inference.** Newey–West HAC per pair, bandwidth by a stated rule. Pooled panel:
pair fixed effects, errors two-way clustered by date and pair — the dollar
induces cross-sectional dependence, so date clustering is not optional.

**Out-of-sample: Clark–West, not Diebold–Mariano.** The brief specifies DM. The
model **nests** the random walk — β = γ = δ = 0 recovers it — and DM's
asymptotics assume non-nested models, so the statistic is missized here. Guide
hint 9 sanctions the substitution. *This corrects the brief and must be raised
at the checkpoint, not applied silently.*

**Multiple testing.** Holm across the primary tests. Unadjusted p-values
reported alongside. Test count depends on D7 — six if AUD is reported separately,
eight if it enters the comparison.

**Power.** A minimum detectable effect at 80% accompanies every null: *"we could
have detected R² of X% at 80% power; we found Y%."*

**Supervisor** ______________ · **Date** __________

---

## D2 · Conventions

**Sign — convention A.** Every rate is USD per unit of the commodity currency.
An increase means the commodity currency appreciated, so β is expected
**positive** in all four pairs.

| Series | Reads as | Action |
|---|---|---|
| iron ore, WTI, copper, Brent | USD per tonne / barrel | as pulled |
| `AUDUSD` | USD per AUD | as pulled |
| `USDCAD`, `USDCLP`, `USDNOK` | local per USD | negate the log return |

Since log(1/x) = −log(x), the pipeline negates the return rather than inverting
the price, so stored prices stay exactly as pulled.

*Rationale:* comparability with the replicated literature; consistency with the
commodity series, already USD-denominated; and one sign reading across all four
pairs without per-pair bookkeeping. It does **not** fix the shared-USD-numeraire
confound — that is the dollar control's job, not the quoting convention's.

*Verification:* every convention-A return must correlate **negatively** with the
dollar factor. Passed on all four (ρ −0.32 to −0.70,
`outputs/diagnostics/sign_check.csv`), plus a hand-calculated worked example in
`sign_convention_example.md`.

**Pair mapping (predeclared).**

| Currency | Benchmark | Instrument | BCOM weight | Orthogonalize against |
|---|---|---|---|---|
| AUD | Iron ore 62% Fe CFR China | `SCO1 Comdty` | 0% | — not a constituent |
| CAD | WTI crude | `CL1 Comdty` | 8.85% | `CL1` |
| CLP | Copper Grade A | `LMCADS03 Comdty` | 5.92% (COMEX) | `HG1` |
| NOK | Brent crude | `CO1 Comdty` | 10.58% | `CO1` |

*Declared limitation:* match quality is not uniform. Copper is ~half of Chilean
goods exports — the cleanest. Canadian crude realizes a moving WCS differential
against WTI. Iron ore is Australia's largest single export but coal is
comparable. Norwegian gas revenue became comparable to oil after 2022 and Brent
does not track TTF, making NOK the weakest match late in the sample. A pre-2022
NOK subsample is prespecified.

**Rolls.** Returns computed only where `FUT_CUR_GEN_TICKER` is unchanged between
consecutive own observations. Roll days dropped, not adjusted — a roll-day price
change is a calendar spread, not a return anyone earned.

Verified: CL 189, CO 193, SCO 152, all ≈12/year. `LMCADS03` returns **zero**
contract changes, confirming constant maturity. `HG1` has no retrievable contract
field, so ~190 rolls enter the CLP orthogonalization — **accepted**, since
errors-in-variables in a first-stage regressor attenuates a loading that is
itself only ~6%. Robustness recomputes `BCOM⊥` with LME copper.

**BCOM orthogonalization.** Regress the BCOM return on the pair's own commodity
return; use the residual. BCOM holds the pair commodity directly, so raw BCOM
would partial out part of the effect of interest. The residual makes β the
**total** own-commodity effect, which is the coherent estimand — you cannot hold
an index fixed while moving one of its constituents.

Where the pair commodity is a constituent, orthogonalize against **the instrument
the index actually holds** — COMEX `HG1` for copper, not LME. LME remains the CLP
regressor because that is the price Chile faces. Two instruments, two jobs.

**Supervisor** ______________ · **Date** __________

---

## D3 · Instruments and sources

**Copper — LME, not COMEX.** Chile prices exports off LME. COMEX fell 22% in one
session on 2025-07-31 on a US tariff dislocation absent from London, which would
inject US trade policy into the Chilean regressor. `LMCADS03` is also
constant-maturity, so no roll treatment is needed.

**Iron ore — `SCO1 Comdty`**, recovered from returned contract codes
(`SCOJ13`…`SCOZ5`), not confirmed on `CTM`. Settles on the **arithmetic average**
of the month's IODEX prints (contract spec, 2026-10-24). Consequences and
treatment are D7.

**Dollar — ICE DXY** (`DXY_PX_LAST`), RiskLab catalog **`RL-36290DAB949B`**,
`bloomberg/02_market/em/EM-17_USD_Index_DXY_PX-LAST_Daily.csv`.

*Amended 2026-10-26, same day as the original decision.* The first version
substituted the Fed H.10 broad index on the premise that ICE DXY was
unobtainable with the API suspended. **That premise was false** — it was in the
library under a different filename.

| | EM-17 file | `USD_Index_DXY_Daily.csv` | ICE DXY should be |
|---|---|---|---|
| 2010-01-04 | **77.525** | 92.357 | ~77.5 |
| 2022-09-27 | **114.106** | 128.440 | ~114 |
| 2008 low | **71.329** | — | ~71.3 |

`USD_Index_DXY_Daily.csv` is the **Fed H.10 nominal broad dollar index**, base
Jan 2006 = 100, and is **misnamed**. It is retained as a prespecified robustness
control (`d_dollar_broad`) — a genuine broad-versus-narrow comparison now, not an
apology. ICE DXY also has **zero missing values** in window against the Fed
file's 188.

*The change was made before any β was estimated, and moves the project toward
the brief rather than away from it.*

**WTI golden source — resolved on evidence.** The adjudicating `CL1` pull was
never executed. The catalog settles it instead: `Crude_Oil_WTI_Spot_Daily.csv`
(`RL-20930E28331E`) is `golden_source = Y`, `validator_status = PASS`, and the
local SHA-256 matches. `AT-03` runs as robustness. A 0.28 difference on one date
in ~4,000 moves nothing.

**Supervisor** ______________ · **Date** __________

---

## D4 · Exclusions

Every one is flagged in the panel, counted in `manifests/sample_attrition.csv`,
and reported with a with/without sensitivity. Nothing is deleted silently.

| Exclusion | Rule | Affects |
|---|---|---|
| **CLP long spans** | drop returns spanning > 5 calendar days, flag `long_span` | 18 obs |
| **AUD sample start** | 2013-04-08 — the `SCO` series does not exist earlier | — |
| **WTI April 2020** | exclude 2020-04-20 and 2020-04-21; a negative print kills the return **into and out of** it | 2 obs, CAD only |
| **NOK 2010-01-01** | New Year's Day; FX does not trade; every other series starts 01-04 | 1 obs |
| **Brent null codes** | 2010-08-30, 2023-01-02 — roll status indeterminate, flag rather than assume | 4 obs |

*Why 5 calendar days:* a weekend spans 3; a weekend plus two public holidays
spans 5. Longer is not a daily return in any economic sense. The threshold comes
from the calendar, not from inspecting results.

*On the AUD start:* no volume field was obtained, so the planned liquidity
diagnostic is unavailable — and unnecessary, since this is absence of data, not
thinness. Caveat recorded: early-contract liquidity cannot be verified. The
price-only zero-return-share diagnostic is available if AUD proves unstable at
the sample start; that trigger is declared now.

*Rejected:* switching the project to simple returns to accommodate two
observations; winsorizing, which would invent a price that never traded.

**Supervisor** ______________ · **Date** __________

---

## D5 · Timing

`DES` unavailable, so settlement times were sourced from the exchanges' own
published methodologies where they could be.

| Series | Settlement | Status |
|---|---|---|
| Brent `CO1` | 19:30 London, 19:28–19:30 weighted average | **exchange spec** (ICE) |
| LME copper | ~17:50 London, 5-minute VWAP window | **exchange spec** (LME) |
| WTI `CL1` | 14:30 ET | *expected* — verify on `DES` |
| Iron ore `SCO1` | ~18:30 Singapore | *expected* — verify on `DES` |
| FX snap | 17:00 ET | *expected* — verify on `DES` |

**Measured gaps** — commodity settles *before* the FX snap:

| Pair | Modal | Range | Days off mode |
|---|---|---|---|
| **AUD** | **10.50 h** | 10.5–11.5 h | **37.8%** |
| CLP | 4.17 h | 3.17–4.17 h | 6.9% |
| CAD | 2.50 h | constant | 0.0% |
| NOK | 2.50 h | 1.5–2.5 h | 6.7% |

AUD's gap is four times the others' and moves on 38% of days, because Singapore
observes no daylight saving while New York does. CAD is constant — both legs
share a timezone.

`timing_gap_hours` and `dst_misaligned` are columns on every pair panel,
computed per date. Guide failure mode 1 requires this be quantified and flagged,
not assumed away.

**Open:** an FX snap closer to the iron ore settlement. None obtainable while the
API is suspended. If none can be had, AUD's contemporaneous coefficient is
reported with the gap in the table note.

**Supervisor** ______________ · **Date** __________

---

## D6 · Prespecified checks

**Date-shift rule — declared before running, and now contested.**

*As declared:* alignment is sound if |β₀| ≥ 2|β_shift| on both sides **and**
each shifted coefficient is insignificant at 5%.

*Result:*

| Pair | β lag 0 | β −1 (t) | β +1 (t) | Verdict |
|---|---|---|---|---|
| AUD | 0.0166 | **0.0227 (2.51)** | 0.0081 (0.90) | REVIEW |
| CAD | 0.0613 | 0.0004 (0.17) | −0.0083 (−3.18) | REVIEW |
| CLP | 0.1800 | 0.0196 (2.17) | 0.0209 (2.32) | REVIEW |
| NOK | 0.0984 | 0.0032 (0.81) | 0.0006 (0.14) | PASS |

*The significance half of the rule is broken, and foreseeably so.* A t-statistic
scales with √n. At n ≈ 3,700, CLP's shift coefficient of 0.0196 — a ninth of its
lag-0 effect, economically nothing — still clears 1.96. The criterion measures
sample size, not alignment. Worse, "is the shift exactly zero?" is the wrong
null: both series have mild serial correlation, so a small nonzero shift is
*expected* under perfect alignment.

**Resolved 2026-10-26, before any primary estimate — option 3.**

Three options were on the table:

1. Keep as declared — three REVIEW verdicts, explained in text.
2. Magnitude only — CAD, CLP, NOK pass; AUD fails.
3. **Test the difference** β₀ − β_shift = 0 by Wald with the right covariance.

**Option 3 is frozen.** It is the only one that tests the question actually
being asked: whether lag 0 *dominates* the shifts. Option 1 tests sample size.
Option 2 drops inference entirely and keeps an arbitrary factor of 2.

Alignment **fails** if the difference β₀ − β_shift is not significantly positive
at 5%, or if |β_shift| ≥ |β₀| on either side.

*This is a change to a rule declared earlier the same day, so it needs to be
unambiguous that it was not made to rescue a result:* AUD fails under all three
options, and CAD and CLP pass the magnitude test under all three. The ranking of
pairs is identical whichever is used. What changes is only whether CAD and CLP
carry a flag generated by sample size rather than by misalignment. The fix was
available a priori and should have been in the original rule.

**Placebo.** `USDCHF` against each commodity. Switzerland exports none of them,
so β should be indistinguishable from zero once the dollar is controlled. A
significant β there means the dollar control is not working. Series already built.

**Forecast-origin table.** One row per origin per pair: origin date, training
window end, what was observable at that moment, target date. With settlement
times unverified, this is where the timing assumption is stated rather than
assumed. `manifests/forecast_origins.csv`.

**Bug detector — replaces the old sanity band.** The previous band (β 0.10–0.25,
R² 5–25%) had no basis and risked anchoring. It is replaced by two separate
things:

- *A catastrophe gate, non-negotiable:* |β| > 0.5 or R² > 0.40 at daily frequency
  would mean commodity moves explain most daily FX variation, which no one has
  found. That indicates a sign or alignment bug and gets said, not reported.
- *A literature prior, cited and non-binding:* read Chen, Rogoff & Rossi (2010)
  and Ferraro, Rogoff & Rossi (2015), record the daily elasticities they report,
  and compare in the discussion. **Context, not a gate** — a gate you can fail
  quietly becomes a reason to adjust the spec.

**Also prespecified:** duplicate-key and many-to-many join audit (passed);
influence check dropping 2020 H1 and the largest move per pair; common-sample
comparison for every horse-race; results with and without each consequential
exclusion; five randomly reproduced observations, seed 20261026 (4/4 exact).

**Supervisor** ______________ · **Date** __________

---

## D7 · AUD as a methodological case study

**Decision.** AUD is removed from the pooled panel and the cross-pair
comparison, and reported separately as a demonstration of what an average-settled
contract on a smoothed index does to a transmission estimate.

**Why.** Two instrument properties, not two unrelated faults:

*Average-price settlement.* With *N* index prints in the contract month and *k*
elapsed, pass-through is $w_k = (N-k+1)/N$. Observed mean |daily return| falls
from 1.36% (day 2) to 0.17% (day 21) while WTI and Brent stay flat at 1–2%. The
regressor shrinks through the month, so the fitted slope is inflated by a factor
that varies with the calendar.

*A smoothed underlying.* The IODEX assessment is sticky — agencies carry values
forward when physical liquidity is thin. Iron ore returns are the only ones in
the project with **positive** first-order autocorrelation:

| Series | AC(1) | t | Zero-return days |
|---|---|---|---|
| **IRON** | **+0.046** | **+2.57** | **2.12%** |
| WTI | −0.033 | −2.03 | 0.42% |
| BRENT | −0.006 | −0.39 | 0.25% |
| COPPER | −0.031 | −1.99 | 0.89% |

Crude and copper show the normal slight negative autocorrelation of bid-ask
bounce. A positively autocorrelated regressor manufactures exactly the lead-lag
artifact seen in D6: AUD's −1 shift coefficient exceeds lag 0.

So the attenuation and the date-shift failure share one cause. The 10.5-hour
timing gap (D5) is separate, and compounds both.

**What is claimed, and what is not.** The *variance* evidence is strong and
unambiguous: the decay profile and the autocorrelation contrast. The *coefficient*
evidence is weak — raw β rises 0.0145 → 0.0377 across the contract month,
directionally as 1/w predicts but only 2.6× against a theoretical 5.7×, and
insignificant in every bucket. The implied constant β·w runs 0.0132, 0.013,
−0.0065, 0.0155, 0.006: consistent with a constant, and equally consistent with
zero.

**The case study leads with variance and reports the coefficient evidence as
weakly consistent, not confirmatory.** Overclaiming there is the one thing that
would undermine the section.

**Alternatives rejected.** CME `TIO1` settles on the same monthly-average
mechanism — changing exchange solves nothing, which is itself evidence that this
is how iron ore trades. Dalian is CNY-denominated behind capital controls, which
would put an exchange rate inside the commodity regressor. Spot assessments are
unobtainable: TSI and Platts refused on entitlement, WRDS carries only the
Datastream Commodities *sample*.

**Reported for AUD:** full sample, the (N−k+1)/N rescaling, and the first-8-day
and first-5-day restrictions, side by side — the point is the pattern across
them, not any single number. Labelled throughout as a case study, never as a
fourth comparison point.

**Headline becomes:** three pairs, plus a demonstration of what instrument
choice does to this literature.

**Supervisor** ______________ · **Date** __________

---

## Open

**O1 · CAD-excluded dollar factor.** Now that the control is genuine ICE DXY,
**CAD is a 9.1% constituent of it**, so the control partly contains the CAD
dependent variable. (The earlier "~9.1%" note was correct for DXY; it was wrong
only because it had been attached to the Fed file.) Affects CAD alone — AUD, CLP
and NOK are not constituents.

*Proposed fix, buildable from data in hand.* DXY is geometric:

```
DXY = 50.14348112 × EURUSD^-0.576 × USDJPY^0.136 × GBPUSD^-0.119
                  × USDCAD^0.091 × USDSEK^0.042 × USDCHF^0.036
```

`AT-04` carries EURUSD, USDJPY, GBPUSD and USDCHF. Drop CAD, renormalise the
four available weights (they sum to 0.867), and the result covers 86.7% of the
non-CAD basket. Only SEK is missing, at 4.2%. Report as a documented
approximation alongside the full-DXY result.

---

## Amendments

| Date | ID | Change | Reason |
|---|---|---|---|
| 2026-10-26 | D3 | Fed H.10 broad index → **ICE DXY** as primary control; Fed retained as robustness | Original premise — that ICE DXY was unobtainable — was false. Verified 77.525 / 114.106 / 71.329. Zero missing vs 188. Changed before any β was estimated. |
| 2026-10-26 | D3 | WTI source: decision → **evidence** | Catalog marks `RL-20930E28331E` golden source, PASS, hash matches. |
| 2026-10-26 | D6 | Sanity band (β 0.10–0.25) **removed** | No basis; risked anchoring. Replaced by a wide catastrophe gate plus a cited, non-binding literature prior. |
| 2026-10-26 | D7 | AUD → methodological case study | Average settlement plus a smoothed underlying explain both the attenuation and the date-shift failure. Reporting it as a fourth comparison point would contaminate the comparison that is the contribution. |
| 2026-10-26 | — | 23 numbered decisions consolidated to 7 | Four were named by the guide, seven implied by it, seven forced by the data, four were over-formalised elaborations. Same content and auditability, one signature per group. |
| 2026-10-26 | D1 | Predictive target `ds_lead{h}` taken on the **currency's own trading calendar**, not by shifting the filtered panel; long-span targets masked (D4). `05` amended; it also writes `panel_AUD_full.csv` for the D7 full-sample and 1/w treatments, and `panel_pooled.csv` now excludes AUD as D7 requires. | **Alignment bug, found before any predictive estimate.** Shifting the filtered panel skipped every dropped row (rolls, long spans, AUD days 9+), so 5.0–16.1% of h=1 targets and 23.4–74.8% of h=5 targets were the wrong day (AUD up to 18 trading days off). Mis-targeting biases toward the very null that is half the contribution. Contemporaneous samples unchanged. |
| 2026-10-26 | D1 | Holm family = **6**: {CAD, CLP, NOK} × {h=0, h=1}, the in-sample HAC tests of β = 0. `n_primary_tests` 8 → 6 in the config and `00`. | D1 sets the count at six when AUD is reported separately, and D7 does exactly that. The config's 8 predates D7. |
| 2026-10-26 | D1, D6 | Estimation rules D1 required but never stated — fixed below, before `07` first ran. | D1 asks for "a stated rule"; none was written down. |

**Estimation rules, fixed 2026-10-26 before `07_primary_estimation` existed.**

1. *Newey–West.* Bartlett kernel, L = ⌊4(T/100)^(2/9)⌋ (Newey & West 1994), no
   small-sample factor. The same rule serves Clark–West and the D6 Wald test.
2. *Pooled two-way clustering.* Cameron, Gelbach & Miller (2011):
   V = V_date + V_pair − V_obs, each one-way part scaled by G/(G−1); negative
   eigenvalues, if any, set to zero. Critical values from t(G−1) with
   G = min(G_date, G_pair) = **3, so t(2)**. Three clusters cannot support
   reliable pair-clustered inference; D1 requires the pair dimension, so it is
   kept and paired with the conservative small-G reference distribution.
3. *Minimum detectable effect.* β_MDE = (q₀.₉₇₅ + q₀.₈₀)·SE(β̂), quantiles from
   that row's reference distribution. The "R²" in D1's sentence is the
   **partial R² of Δc**: b²Σ(Δc⊥)² / (b²Σ(Δc⊥)² + Σε̂²), with Δc⊥ the commodity
   return net of the controls. At b = β̂ this is exactly the partial R² found.
4. *Bug gate (D6).* |β̂| > 0.5 or **partial R² of Δc** > 0.40. The gate is about
   commodity moves; total R² includes the dollar control, so it is reported but
   not gated — the pre-freeze `sign_check.csv` gives ρ(NOK, DXY) = −0.70, a
   total R² near 0.49 from the control alone. A tripped gate stops `07`/`08`
   before any results table is written.
5. *Clark–West.* Expanding window; the first forecast origin is the midpoint of
   each sample's predictive observations; OLS re-estimated at every origin on
   rows whose target date is on or before the origin; benchmark forecast 0
   (driftless random walk); f = e²_RW − e²_M + ŷ²_M; one-sided at 5% with the
   Newey–West SE. Not Holm-adjusted — it complements the six in-sample tests.
   Out-of-sample R² and the MAE ratio are descriptive only.
6. *Horizon.* h = 5 is the one-day return five trading days ahead, Δs_{t+5}, as
   D1's equation and `05` define it — not the cumulative five-day return.
7. *Economic units.* β̂·SD(Δc), in percent: the FX move that goes with a
   one-standard-deviation commodity move on the estimation sample.
8. *D6 date shift (option 3).* The signal is shifted on the commodity's own
   trading calendar, not by panel row; Cov(β₀, β_shift) from stacked influence
   functions under rule 1; one common sample for all three regressions.
9. *D6 influence.* "The largest move" is the observation with the largest |Δc|
   in each pair.

*Recorded, not changed:* `06`'s date-shift test implements the superseded
option-1 rule and shifts panel rows (for AUD's 8-day panel that pairs day 2 with
day 8 of the previous month); its output stays on record and option 3 runs in
`08`. The USDCHF placebo was never built — `load_curncy()` omits USDCHF, so
`04`'s guard skipped it; `08` builds it from AT-04 through `data_compile`. The
BCOM⊥ loading is full-sample: CAD and NOK forecasts are invariant to it
(span{1, Δc, BCOM⊥} = span{1, Δc, BCOM}); for CLP, orthogonalized on HG1 but
regressed on LME, it is a one-scalar look-ahead. `AT-03` (D3 WTI robustness) is
not on this machine and cannot be pulled; that check is reported as not run.

*Finding on the frozen pooled estimator, synthetic data only, before any pooled
estimate.* Monte Carlo with 3 pairs, regressors correlated across pairs and a
common date shock, β = 0 true, 400 replications: the frozen two-way estimator
with the t(2) reference of rule 2 rejects **0.5%** of the time at nominal 5%
(with a normal reference, 11%); date-only clustering 5.2%, Driscoll–Kraay 4.5%,
heteroskedasticity-robust 10%. The frozen pooled test is therefore valid but
conservative, and a pooled null carries little weight. **Raised for the
supervisor, not applied** — the frozen estimator is what is reported.
