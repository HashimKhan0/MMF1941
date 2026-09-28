# Project 1 — Working Notes

**Student:** Hashim Khan · **Proposal ID:** A14-03 · **Course:** MMF1941
**Title:** Commodity-Currency Transmission Beyond a Single Pair: A Multi-Pair Replication
**Last updated:** 2026-09-20

---

## 1. Scope and purpose

This is a **replication-and-generalization** study, not a discovery study. Project 12 found a specific asymmetry in soybeans → BRL: commodity returns explain *same-day* currency returns well, but *lagged* commodity returns do not forecast next-day currency returns. The question here is whether that asymmetry is a general property of commodity currencies or an artifact of one pair.

Four pairs, daily frequency, ~2010–2025, controlling for broad dollar (DXY) and broad commodity (BCOM) moves.

**Why the framing matters:** a clean, well-identified *null* on the predictive side is a legitimate result in this project, not a failure. The design must be built so that a null is credible rather than merely under-powered.

### Problem statement

Commodity currencies are thought to move with their export commodity. If that link is real and exploitable, commodity prices should forecast currency returns. If the link is real but purely informational — both assets repricing simultaneously to the same news — then it is contemporaneous only and forecastability is zero. These two worlds look identical in a correlation table and are separable only with a lead-lag design.

### Prior literature to read before writing

- Chen, Rogoff & Rossi (2010) — commodity currencies and forecastability
- Ferraro, Rogoff & Rossi (2015) — oil and CAD; found essentially this project's hypothesis (strong daily contemporaneous link, no robust out-of-sample predictability)

The contribution here is **breadth across four pairs**, not novelty of the finding. Say so explicitly in the paper.

---

## 2. Hypotheses

Two hypotheses, tested asymmetrically.

### H1 — Contemporaneous (expect to reject the null)

For each pair *i*:

```
Δs_{i,t} = α + β·Δc_{i,t} + γ·ΔDXY_t + δ·ΔBCOM⊥_t + ε_t
```

- **H₀: β = 0** — expect rejection with HAC (Newey–West) standard errors.
- β is an elasticity: a 1% rise in the commodity associates with a β% appreciation of the currency.

### H2 — Predictive (expect to FAIL to reject)

Same specification with `Δs_{i,t+1}` on the left-hand side.

- **H₀: β = 0** — expect no rejection.

### Making the null credible

A null cannot be *proven*. Failing to reject is only evidence of absence if the test had power to detect an economically meaningful effect. Three requirements:

1. **Report a minimum detectable effect.** With ~3,900 daily observations, quite small R² is detectable. State it: "we could have detected R² of X% at 80% power; we found Y%."
2. **Move the predictive claim out-of-sample.** Diebold–Mariano vs a random walk, plus Campbell–Thompson out-of-sample R². H₀ there is *equal expected forecast loss* — a far more defensible basis for "no predictability" than an in-sample t-stat near zero.
3. **Multiple testing.** 4 pairs × 2 directions = 8 tests. Apply Holm or Bonferroni, or at minimum report unadjusted *and* adjusted p-values.

---

## 3. The four pairs

| Currency | Commodity | Instrument to use | Bloomberg ticker |
|---|---|---|---|
| AUD | Iron ore | SGX TSI 62% Fe front-month futures | verify via `CTM <GO>` |
| CAD | WTI | NYMEX front-month, roll-adjusted | `CL1 Comdty` |
| CLP | Copper | LME 3-month **or** COMEX front | `LMCADS03 Comdty` / `HG1 Comdty` |
| NOK | Brent | ICE Brent front-month | `CO1 Comdty` |

### Pair-specific quirks — name these in the paper rather than let a reader find them

- **CAD sits inside DXY** at roughly 9% weight. Regressing CAD on DXY is partly mechanical. Either build a dollar factor excluding the pair's own currency, or accept it and flag it prominently.
- **WTI, Brent and copper sit inside BCOM.** The "broad commodity" control partially contains the regressor. **Fix:** regress BCOM on the own-commodity return and use the residual (`BCOM⊥`) as the control, so it genuinely means "broad commodity moves *not* attributable to this commodity." Iron ore is **not** a BCOM component, so AUD is clean here.
  - Pull BCOM constituent weights via `MEMB <GO>` and put them in an appendix table — that's the evidence for why this orthogonalization is needed for three pairs and not the fourth.
- **CLP has central-bank intervention episodes** (notably 2019 and 2022). Run a subsample or dummy robustness check.
- **SGX iron ore only became liquid around 2011–2013.** Pull `PX_VOLUME` and `OPEN_INT` alongside price and plot them before committing to a 2010 start. Shortening the sample for this pair is defensible *if* the liquidity chart is shown.

---

## 4. Data status

The proposal's "50% not available locally" estimate is exactly right: **five of ten series are present, five must be pulled.** The split is clean — the commodity side and controls are largely present; the FX side is almost entirely absent.

### 4.1 Already in the shared RiskLab Drive

| Series | File | Location |
|---|---|---|
| WTI | `CrudeOil_WTI_Price_Daily.csv` | `02_market/em` |
| Copper | `Copper_Price_Daily.csv` | `02_market/em` |
| BCOM | `BCOM_Daily.csv` | `04_macro` |
| DXY | `USD_Index_DXY_Daily.csv` (+3 further copies) | `04_macro`, `02_market/em` |
| CLP spot | `EM-27_CLP-Curncy_PX-LAST_2009-2025.csv` | `02_market/em` |

**Useful extras nearby:** `Oil_Volatility_OVX_Index_Daily.csv`, `EM_FX_Volatility_Index_JPMVXYEM_Daily.csv`, `VIX_Index_Daily.csv`, `CAN_Policy_Rates.csv`, `US_Policy_Rates.csv`. The vol indices support a conditioning robustness check — does contemporaneous β strengthen in high-vol regimes?

### 4.2 Must be pulled from Bloomberg

Five series: **AUD spot, CAD spot, NOK spot, Brent, iron ore.**

**`bloomberg/02_market/fx` is confirmed empty** (checked visually, 2026-09-20). There is no local FX spot data for this project except CLP, and that sits in `02_market/em`, not in `fx`. Note this in the source dictionary: the absence is a verified finding, not an unchecked assumption. Worth one cross-check against `_catalog/catalog.csv` in case FX series are filed under a different provider folder, but do not expect to find any.

### 4.3 Three warnings about the local data

1. **The AUD / NOK / IRON files in Drive are decoys.** Those hits are First Rate Data 1-minute bars and quarterly option chains — *intraday*, which this proposal explicitly bars. `IRON_full_1min` is almost certainly an equity ticker, not iron ore. Do not treat AUD or NOK as covered.
2. **DXY exists four times** at four different file sizes (105KB / 141KB / 141KB / 149KB) across `04_macro` and `02_market/em` — different vintages or coverage windows. Pick one, record which, and note the duplicates in the source dictionary. This *is* the identifier-join diagnostic Minimum Output #3 asks for.
3. **CLP runs 2009–2025**, slightly short of the 2010–2025 window at the back end. Decide whether to extend from Bloomberg or shorten the sample.

### 4.4 What the data-root README implies

The README states that a file being present locally does **not** establish point-in-time validity, adjustment conventions, or construct validity. Concretely: **none of the local CSVs states its snap time.** `Copper_Price_Daily.csv` does not say whether it is LME 3M at London close or COMEX settlement — and that distinction decides whether the CAD and CLP regressions are contemporaneous or accidentally predictive.

Local files are a head start on *coverage*, not on *provenance*.

**Recommendation:** pull WTI, copper, BCOM and DXY from Bloomberg anyway (the source dictionary needs documented tickers and fields regardless), then use the local copies as a cross-check. A scatter of local-vs-Bloomberg returns sitting on the 45° line is a free validation exhibit. With FX confirmed absent, the terminal session has to cover eight of the ten series in any case, so adding the remaining two costs almost nothing.

---

## 5. Bloomberg extraction plan

### Pull list

| Series | Ticker | Field | Note |
|---|---|---|---|
| AUD spot | `AUDUSD Curncy` | `PX_LAST` | USD per AUD — already correct direction |
| CAD spot | `USDCAD Curncy` | `PX_LAST` | invert |
| CLP spot | `USDCLP Curncy` | `PX_LAST` | invert; market spot, **not** dólar observado |
| NOK spot | `USDNOK Curncy` | `PX_LAST` | invert |
| WTI | `CL1 Comdty` | `PX_SETTLE` | |
| Brent | `CO1 Comdty` | `PX_SETTLE` | |
| Copper | `LMCADS03` or `HG1 Comdty` | `PX_LAST` / `PX_SETTLE` | pick one, justify |
| Iron ore | SGX 62% Fe front-month | `PX_SETTLE` | verify via `CTM <GO>` |
| BCOM | `BCOM Index` | `PX_LAST` | price index, **not** `BCOMTR` |
| DXY | `DXY Curncy` | `PX_LAST` | |

Use `PX_SETTLE` rather than `PX_LAST` for futures — settlement is the exchange's official mark and the literature standard; `PX_LAST` can pick up thin post-settlement prints.

### Roll adjustment — sidestep it

Bloomberg generic futures series show a price gap on roll days that is not a return. Rather than defending a back-adjustment convention:

- Pull the generic price series **and** `FUT_CUR_GEN_TICKER` (which underlying contract the generic points to each date).
- Compute `r_t` only when contract(t) == contract(t−1); mark roll days missing.
- Cost: ~12 obs/year per commodity out of ~250. Immaterial.
- Record this as the adjustment method in the source log.

If back-adjusted series are preferred instead, use **ratio** adjustment, not difference adjustment, since the work is in returns.

### Terminal hygiene

- Bloomberg meters data downloads on a monthly quota; `BDH` pulls burn it fast on notebook re-runs. Pull **once** to CSV/parquet, keep raw extracts immutable in `data/raw/`, do all cleaning downstream. Re-pull only to extend the sample.
- Capture `DES` and `FLDS` screenshots for at least the iron ore contract — the identifier choice there is least obvious.

---

## 6. Two conventions that must be locked before any estimation

### 6.1 Sign convention

`AUDUSD` quotes USD-per-AUD; `USDCAD`, `USDCLP`, `USDNOK` quote local-per-USD. **Invert the latter three** so a positive return means the commodity currency appreciated, in all four pairs. Otherwise signs flip across pairs and the panel is meaningless.

### 6.2 Snap times — the item that can invalidate the whole contemporaneous result

Four commodities settle on four exchanges across three time zones; FX spot is continuous and snapped at a chosen fix.

Approximate settlement times (**confirm on each contract's `DES <GO>` page**):

| Contract | Settlement | ≈ ET |
|---|---|---|
| WTI (NYMEX) | 2:30 pm ET | 2:30 pm |
| Brent (ICE) | 7:30 pm London | ≈ 2:30 pm |
| Copper (LME 3M) | London afternoon | ≈ 12 pm |
| Iron ore (SGX) | Singapore evening | ≈ early am |

**The failure mode:** with a WM/Reuters 4pm London fix (11:00 am ET), WTI settles 3.5 hours *after* the FX observation for the same date. Oil news in that window appears in `commodity_t` but cannot be in `FX_t` — it lands in `FX_{t+1}`. That manufactures apparent predictability out of nothing, which is exactly what H2 says should not exist. Iron ore has the mirror-image problem: it settles ~12 hours *before* a 5pm ET FX close, making the AUD "contemporaneous" regression partly predictive.

**One upside of the empty `fx` folder:** since all four FX series now come from a single Bloomberg pull, the fix time is a free choice rather than something inherited from a legacy file. Choose it deliberately and document it once.

**Two responses:**

1. **Use 5pm ET FX and document it.** That places the FX snap after WTI, Brent and LME settlement, making three of four pairs genuinely contemporaneous. Iron ore / AUD remains misaligned — flag it. `BFIX <GO>` shows Bloomberg's own fixing times, cleaner than the generic `Curncy` last price (an unspecified end-of-day snap).
2. **Make the lead-lag table a headline robustness result, not an appendix.** For each pair, run the regression with the commodity at t−1, t, t+1 against FX at t. If β peaks at t for CAD, NOK and CLP but at t+1 for AUD, the timing problem is self-diagnosed and becomes a finding about measurement. Worth more than another ML variant.

**Do not** attempt to solve alignment with intraday bars — the proposal bars high-frequency extraction. `C:\risklab\data\intraday_data` is the only permitted route and should not be needed.

### 6.3 Calendar alignment

Four exchange holiday calendars plus FX. Chinese New Year halts iron ore for a week while AUD keeps trading. Decide a rule — inner join on days all series trade is cleanest — and state it explicitly.

---

## 7. What the finished result looks like

Roughly six tables and one figure:

1. Coverage, missingness and identifier-join diagnostics — **pre-estimation**
2. Per-pair contemporaneous β, with and without controls, HAC t-stats, R²
3. Pooled panel with pair fixed effects, SEs **two-way clustered by date and pair** (date clustering matters: the dollar induces cross-sectional dependence)
4. Per-pair predictive β, in-sample
5. Out-of-sample R² and Diebold–Mariano vs random walk
6. Walk-forward random forest vs random walk, with DSR if a Sharpe is reported

**Figure:** the lead-lag β profile (t−1, t, t+1) across all four pairs.

### Sanity band for magnitudes

Daily contemporaneous elasticities in this literature typically land around **0.1–0.25**, with R² roughly **5%–25%** depending on pair — copper/CLP usually strongest, iron ore/AUD noisiest. **If β ≈ 0.9 or R² ≈ 60%, there is a bug** — most likely a sign or alignment error.

### Write-up requirement

State effect sizes in economic language, not stars. *"A one-standard-deviation daily copper move corresponds to a 0.4% same-day CLP appreciation"* is a result. *"β is significant at the 1% level"* is not.

---

## 8. Source log — required columns

Per Minimum Output #1, and graders check it:

`terminal function` · `ticker / series ID` · `field` · `frequency` · `date range` · `currency` · `adjustment convention` · `snap time` · `extraction date` · `extractor`

(`snap time` is not in the proposal's list but is added deliberately — see §6.2.)

---

## 9. Next actions

- [ ] Read Ferraro, Rogoff & Rossi (2015) and Chen, Rogoff & Rossi (2010)
- [x] ~~Confirm whether `02_market/fx` is genuinely empty~~ — **confirmed empty 2026-09-20**; all FX except CLP comes from Bloomberg
- [ ] Open the five local CSVs; record actual date ranges, columns, missingness → coverage table
- [ ] Resolve the four DXY duplicates; pick one and document why
- [ ] Verify SGX iron ore generic ticker via `CTM <GO>`; pull volume/OI and plot liquidity
- [ ] Confirm settlement times on each contract's `DES <GO>` page
- [ ] Decide FX fix (recommend 5pm ET) and document
- [ ] Decide copper instrument (LME 3M vs COMEX) and justify
- [ ] Pull `MEMB <GO>` BCOM weights for the appendix
- [ ] Execute Bloomberg pull once → `data/raw/`, immutable
- [ ] Build source log alongside the pull, not after
- [ ] Cleaning/merge script: sign inversion, calendar join rule, roll handling, BCOM orthogonalization
- [ ] Coverage diagnostics table **before** any estimation
- [ ] Estimate H1, then H2; lead-lag table; power / MDE calculation
- [ ] OOS: Diebold–Mariano, Campbell–Thompson R²
- [ ] Walk-forward RF; DSR if reporting Sharpe
- [ ] Draft, preserving nulls and separating exploratory from confirmatory
