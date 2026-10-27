# Phase 1 — Decisions closed under API suspension

**MMF1941 Project 1 (A14-03) · 2026-10-26**

Supervisor approved proceeding with current data (2026-10-26). Bloomberg Desktop
API suspended 2026-10-24 pending workflow review; Terminal screens work,
extraction does not.

Every decision below is **decidable now**. Each needs transcribing into
`design_decisions.md` with a supervisor sign-off line and the note *"decided
under API suspension, 2026-10-26."*

None of these may be revisited by looking at a coefficient.

---

## DD-12 · Iron ore instrument — **futures, early contract month**

**Ticker.** `SCO1 Comdty` — SGX TSI / IODEX 62% Fe CFR China front-month
generic. Recovered from returned contract codes (Phase 0.1), not confirmed on
`CTM`.

**The problem, confirmed from the contract spec on 2026-10-24:**

> cash settlement using the arithmetic average of all IODEX 62% Fe iron ore
> reference prices in the expiring month

Settlement is the average of the month's index prints, not a closing value. If
the contract month holds *N* index publications and *k* have occurred, a shock to
today's index enters the realized portion at weight 1/N and the forecast of the
remaining prints at weight (N−k)/N. Under a random walk the pass-through is:

$$w_k = \frac{N-k+1}{N}$$

So *w* ≈ 1 on day 1 and ≈ 1/N by month end. The observed series matches: mean
absolute daily return decays from ~1.3% to ~0.25% through the contract month
while WTI and Brent stay flat at 1–2%.

**Direction of the bias — note carefully.** This *inflates* the slope, it does
not attenuate it. Regressing on $x = wc$ when the truth is $\Delta s = \beta c$
gives $\hat\beta \to \beta\,E[w]/E[w^2] \approx 1.5\beta$, with standard errors
about $\sqrt{3}$ larger and the t-statistic down roughly 13%.

The damage is to **cross-pair comparability**, which is the entire project. CAD,
NOK and CLP carry no such distortion, so an uncorrected AUD coefficient would sit
above the other three for purely mechanical reasons — and whether the betas
differ across pairs is the finding.

**Why not something else.** CME `TIO1` settles on the same monthly-average
mechanism, so switching exchange solves nothing — this is how iron ore trades.
Dalian is CNY-denominated behind capital controls, which would put an exchange
rate inside the commodity regressor. The spot assessments are unobtainable: TSI
and Platts refused on entitlement (`LHSI0006`, `PFAMCFRC`), `ISIX62IU` (Custeel)
untested when the API was suspended, and WRDS carries only the Datastream
Commodities *sample*, with the full product unsubscribed.

**Decision — cutoff revised 2026-10-26 from the empirical decay profile.**

The observed response is flat across days 2–7 (1.2–1.4% mean |return|) and only
then decays, where theory says *w* should already be 0.73 by day 7. The effective
pricing window is shorter than *N*, or basis noise floors the early month. Either
way the first week is one regime.

- **Baseline:** first **8** trading days (*w* 1.00 → 0.68), 1,066 iron ore
  observations pre-join (34.4%).
- **Robustness 1:** first 5 days (*w* 1.00 → 0.82) — the conservative cutoff.
- **Robustness 2:** full sample rescaled by $1/w_k$, trimmed or weighted against
  month-end noise amplification.

**Why not 5.** A 5-day cutoff leaves ~500–550 observations after the joins
against 2,909 for the full sample. The minimum detectable effect widens enough
that the predictive null risks being uninformative, and an under-powered null is
an absent test rather than a finding.

**Not specification shopping:** the cutoff came from the commodity series' own
decay profile, which contains no FX data.
- **Diagnostic, run before the freeze:** estimate β by day-of-contract-month
  bucket. If the mechanism is real, raw β̂ should **rise** through the month
  roughly as 1/w. Flat means the mechanism is not biting and the full sample is
  usable — in which case the baseline changes on *this* evidence, recorded before
  any headline estimate.

$k$ and $N$ come from `FUT_CUR_GEN_TICKER`: the front-month generic for month M
settles against M's average, so *k* is trading days elapsed in the contract month
and *N* the month's total.

---

## DD-13 · Dollar factor — **Fed H.10 broad index, relabelled**

`USD_Index_DXY_Daily.csv` is **not ICE DXY.** It starts 2006-01-02 at 101.4155,
and the Federal Reserve's nominal broad dollar index is based at 100 = January
2006. Level path and US-federal-holiday gaps agree (Phase 0.5).

**Decision.** Use it. It is a legitimate — arguably better — dollar control,
being trade-weighted across a far broader basket than ICE DXY's six currencies.

**Conditions.**
1. Rename the column everywhere. It is `USD_BROAD` or `FED_BROAD`, never `DXY`.
   A variable named `DXY` holding Fed data is the kind of error that survives to
   publication.
2. State the substitution in the paper. The brief specifies DXY; this is a
   documented deviation, not a silent one.
3. **Delete the "CAD is ~9.1% of DXY" claim** from `CLAUDE.md`. It describes a
   different index. The CAD-exclusion question stays open but needs the Fed
   index's own weights, which are published by the Fed.
4. Coverage is 2006-01-02 → 2025-11-14, so it does not bind the sample.

---

## DD-14 · CLP long-span returns — **drop above 5 calendar days, flagged**

121 missing weekdays in 2012, 22 consecutive. A re-pull would have settled
whether this is the source or the file; it is not available.

**Decision.** Compute returns across the gaps, then **exclude any return spanning
more than 5 calendar days** and carry a `long_span` flag on every excluded
observation.

**Why 5 and not something else.** A normal weekend spans 3 calendar days;
a weekend plus two public holidays spans 5. Anything longer is not a daily
return in any economic sense. The threshold comes from the calendar, not from
inspecting results.

**Required robustness:** re-run retaining the long-span returns with a span
control. Report both. Approximately 28 observations are affected.

---

## DD-15 · AUD sample start — **2013-04-08, no diagnostic needed**

No volume or open-interest field was obtained, so the planned liquidity
diagnostic is unavailable.

It is also unnecessary. The `SCO` series simply **does not exist before
2013-04-08** — 3,312 rows, first contract `SCOJ13`. This is not thin data to be
screened; it is no data.

**Decision.** AUD starts 2013-04-08. No threshold rule required.

**Caveat to record:** without volume we cannot verify that early contracts were
liquid enough to price efficiently. The price-only zero-return-share diagnostic
stays available as a robustness check on the first 6–12 months; run it only if
the AUD result looks unstable at the sample start, and declare that trigger now.

---

## DD-16 · WTI April 2020 — **exclude two returns, flagged**

Confirmed present:

```
2020-04-17    18.27
2020-04-20   -37.63
2020-04-21    10.01
```

The log return is undefined **both into and out of** the negative print — two
observations, not one.

**Decision.** Exclude both, flag as `negative_price`, and report the CAD results
with and without. Affects CAD only.

**Rejected:** switching the whole project to simple returns to accommodate two
observations, and winsorizing, which would invent a price that never traded.

---

## T9 · WTI golden source — **use the repo file, cannot adjudicate**

`CLAUDE.md` says this was "resolved by a fresh CL1 pull." **It was not** — the
API was suspended before that pull. Correct that line.

The conflict: `Crude_Oil_WTI_Spot_Daily.csv` gives 63.41 on 2025-09-23; `AT-03`
gives 63.69.

**Decision.** Use `Crude_Oil_WTI_Spot_Daily.csv`, the file already in `raw_data/`
and already wired into `data_compile.load_comm()`. Grounds: it is the series the
validated pipeline was built and checked against, and switching now would
invalidate the existing validation run for no demonstrated gain.

A 0.28 difference on one date out of ~4,000 will not move a coefficient. State
that rather than leaving it hanging.

**Robustness:** re-run CAD on `AT-03` and report whether anything moves.

**Also correct the source log**, which names `CrudeOil_WTI_Price_Daily.csv` — a
file that does not exist. Note too that the actual file is labelled "Spot" while
containing `CL1` front-month futures.

---

## DD-08 · Predictive horizon — **h = 1, with h = 5 secondary**

Unspecified anywhere in the project until now, and listed in the implementation
guide as a decision to confirm before estimation.

**Decision.** *h* = 1 trading day primary; *h* = 5 prespecified secondary. Both
declared now; neither chosen after seeing output.

This is load-bearing. The predictive null is half the contribution, and a horizon
selected after estimation makes it worthless.

---

## DD-11 · Clark–West, not Diebold–Mariano — **deviation, flag to supervisor**

The brief specifies *"predictive OOS (Diebold-Mariano)."* The candidate model
nests the random walk — set β = γ = δ = 0 and it collapses to the benchmark — and
DM's asymptotics assume non-nested models, so the statistic is missized here.

**Decision.** Clark–West for the predictive out-of-sample comparison; DM only
where a genuinely non-nested comparison exists.

The guide sanctions this: *"Use Diebold-Mariano or Clark-West only where its
nesting assumptions fit."*

**Raise it explicitly at the checkpoint.** It is a correction to the brief, not a
preference. Flagged it reads as rigour; discovered it reads as carelessness.

---

## Carried forward from Phase 0

Small, but they change the data and belong in the same freeze:

- **Drop the NOK 2010-01-01 observation.** New Year's Day; FX does not trade;
  every other series starts 2010-01-04.
- **Flag the four Brent observations** around the two null contract codes
  (2010-08-30, 2023-01-02) where roll status is indeterminate.
- **Add explicit date formats** to every CSV read in `data_compile.py`. Inference
  currently works and violates this project's own stated rule.

---

## Sample end — not a decision, a constraint

| Pair | Binding series | Ends |
|---|---|---|
| AUD, CAD | AT-04 FX | 2025-09-19 |
| CLP, NOK | BCOM | 2025-09-23 |

All Bloomberg-pulled series reach 2025-12-31. Extending the window needs exactly
two re-pulls — AT-04 FX and BCOM — once API access returns. Record it as a
pending request, not an open decision.

---

## Still open after Phase 1

| | Blocked on |
|---|---|
| **DD-18** · snap times and timing-gap treatment | Exchange published specs (Phase 0, outstanding) — not Bloomberg |
| **DD-19** · date-shift decision rule | Nothing. Must be written **before** the test runs |
| CAD-excluded dollar factor | Fed broad index weights, published by the Fed |

DD-19 is the one to watch. It touches the estimand, so running it first and
deciding after is specification shopping on the test most likely to be examined.
