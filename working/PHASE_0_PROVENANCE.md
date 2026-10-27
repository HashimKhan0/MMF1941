# Phase 0 — Provenance recovered from files

**MMF1941 Project 1 (A14-03) · 2026-10-26**

Established without Bloomberg access, from the raw files in `raw_data/`.
Data unchanged since the 2026-10-05 validation run.

---

## 0.1 Formulas — not recoverable

`BBG.xlsx` contains **zero formula cells**. The workbook was saved as values, so
the original `=BDH(...)` calls are gone and the tickers cannot be read off them.

**The contract codes recover them instead**, which is stronger evidence anyway —
a formula records what was requested, a contract code records what came back.

| Sheet | First code | Last code | Root | Ticker |
|---|---|---|---|---|
| `wti` | `CLG10` | `CLG6` | `CL` | `CL1 Comdty` |
| `brent` | `COG10` | `COH6` | `CO` | `CO1 Comdty` |
| `iron` | `SCOJ13` | `SCOZ5` | **`SCO`** | **`SCO1 Comdty`** |

### The iron ore ticker is confirmed

`SCO` is the SGX TSI / IODEX 62% Fe CFR China front-month generic. Source-log
row 6 has read `TBC - confirm via CTM` since September; it is now closed.

`SCOJ13` = April 2013, `SCOZ5` = December 2025 — consistent monthly contracts
across the whole series.

Record it as **recovered from returned contract codes, not confirmed on `CTM`**.
That distinction belongs in the limitations list.

`nok`, `clp` and `copper` carry no contract field, which is correct: two spot FX
series and a constant-maturity forward.

---

## 0.2 Coverage — Bloomberg sheets

| Sheet | Rows | First | Last | Rolls | Value range |
|---|---|---|---|---|---|
| `wti` *(contract field only)* | 4,030 | 2010-01-04 | 2025-12-31 | 192 | — |
| `brent` | 4,131 | 2010-01-04 | 2025-12-31 | 193 | 19.33 – 127.98 |
| `iron` | 3,312 | 2013-04-08 | 2025-12-31 | 152 | 38.15 – 223.94 |
| `copper` | 4,042 | 2010-01-04 | 2025-12-31 | **0** | 4,331 – 12,558 |
| `nok` | 4,173 | 2010-01-01 | 2025-12-31 | — | — |
| `clp` | 3,898 | 2010-01-04 | 2025-12-31 | — | — |

Roll counts are all ~12/year over their own windows (192/16y, 193/16y,
152/12.7y). Copper shows zero, confirming `LMCADS03` is constant-maturity as
specified.

**Every Bloomberg sheet runs to 2025-12-31.** The September cutoff is entirely a
shared-library constraint — see 0.4.

---

## 0.3 Coverage — local files

| File | Rows | First | Last | Row order |
|---|---|---|---|---|
| `AT-04_..._2000_2025.csv` (AUDUSD, USDCAD) | 6,710 | 2000-01-03 | **2025-09-19** | ascending |
| `Crude_Oil_WTI_Spot_Daily.csv` | 7,743 | 1994-12-09 | 2025-09-26 | **descending** |
| `Commodity_Index_BCOM_Price_Daily.csv` | 7,715 | 1994-12-30 | **2025-09-23** | **descending** |
| `USD_Index_DXY_Daily.csv` | 5,185 | **2006-01-02** | 2025-11-14 | ascending |
| `Copper_Price_Daily.xlsx` (HG1) | 7,738 | 1995-01-03 | 2025-10-01 | **descending** |

Three of five are stored newest-first. `data_compile._finish()` sorts ascending,
so this is handled — but any new script that reads a raw file directly will
produce sign-flipped returns. Always go through the loaders.

---

## 0.4 What actually binds the sample end

Not "September 2025" generally. Two different series bind two different pairs:

| Pair | Binding series | Sample ends |
|---|---|---|
| **AUD** | AT-04 (`AUDUSD`) | **2025-09-19** |
| **CAD** | AT-04 (`USDCAD`) | **2025-09-19** |
| **CLP** | BCOM | **2025-09-23** |
| **NOK** | BCOM | **2025-09-23** |

So extending the window to 2025-12-31 requires exactly **two re-pulls**: the
AT-04 FX pairs and BCOM. Everything else already reaches year end.

Not actionable while the API is suspended. Recorded so the ask is specific when
access returns.

---

## 0.5 The dollar index is confirmed as the Fed H.10 broad index

Three independent checks, all consistent:

| Date | File value | ICE DXY would be |
|---|---|---|
| 2006-01-02 | **101.4155** | ~91 |
| 2010-01-04 | 92.3566 | ~77.5 |
| 2022 peak | 128.4544 | ~114 |

The series **starts 2006-01-02 at 101.4** — the Federal Reserve's nominal broad
dollar index is based at 100 = January 2006. That base, the level path, and the
gaps on US federal holidays all identify it.

This is not ICE DXY and must not be called DXY anywhere in the project. See
Phase 1, DD-13.

Consequence: the "CAD is ~9.1% of DXY" note in `CLAUDE.md` is unsupported — it
refers to a different index with different weights.

---

## 0.6 Confirmed data traps

**WTI 2020-04-20 = −37.63.** Present in the file.

```
2020-04-17    18.27
2020-04-20   -37.63
2020-04-21    10.01
```

Two log returns are undefined, not one — into and out of the negative print.

**Brent has two rows with a null contract code**: 2010-08-30 and 2023-01-02. Roll
status is indeterminate on those dates, so the returns into and out of each are
indeterminate too. Four observations. Flag, do not silently keep.

**NOK has an observation dated 2010-01-01** — New Year's Day, when FX does not
trade. Every other series starts 2010-01-04. Almost certainly a carried value.
Drop or flag it; do not let it generate a return.

**Filename mismatch.** The source log names `CrudeOil_WTI_Price_Daily.csv`; the
file in `raw_data/` is `Crude_Oil_WTI_Spot_Daily.csv`. Same data (2025-09-23 =
63.41, matching), but the log must be corrected. Note also that the file is named
"Spot" while containing `CL1` front-month futures.

---

## 0.7 File hashes — SHA-256, 2026-10-26

| Hash (first 16) | Bytes | File |
|---|---|---|
| `798c0d24a7fa8e7f` | 726,108 | `AT-04_Daily_Spot_Prices_G10_FX_Pairs_Daily_2000_2025.csv` |
| `c78fee675fcc7b3d` | 450,769 | `BBG.xlsx` |
| `71165a2451199454` | 158,486 | `Commodity_Index_BCOM_Price_Daily.csv` |
| `5413c3e372015319` | 148,795 | `Copper_Price_Daily.xlsx` |
| `6326c905dadc5ea3` | 139,170 | `Crude_Oil_WTI_Spot_Daily.csv` |
| `472e258712bf48ce` | 104,623 | `USD_Index_DXY_Daily.csv` |
| `d54e69c0b76966dd` | 8,148 | `bloomberg_source_log.csv` |

Full hashes belong in the `file_hash` column of the source log. Recompute and
compare before the final run — if one changes, a supposedly immutable file was
rewritten.

---

## 0.8 `data_compile.py` review

**Sound.** Outer joins, no forward-fill, no `dropna`, no silent coercion. The
four-state status frame (`ok` / `src_na` / `no_row` / `uncovered`) is exactly
what the coverage diagnostics need, and keeping it in a parallel frame protects
the float dtype of the price columns. `_hg1()` correctly omits the unusable BID
column. `_finish()` sorts ascending, which handles the descending files.

**One defect, and it violates this project's own rule.**

`CLAUDE.md` states: *"Never let pandas infer a date format from a text file.
Formats differ per source, so state the format explicitly for every CSV read."*

`_finish()` calls `pd.to_datetime(df.index)` with no `format=`, so every CSV date
column is inferred — AT-04, WTI, BCOM, DXY. Inference currently produces correct
results, but it is one ambiguous file away from silently reading `03/04/2020` as
March 4 instead of April 3.

Fix: pass an explicit format per source. The `.xlsx` reads need none — native
Excel datetimes, as `CLAUDE.md` says.

**One gap.** No loader drops the NOK 2010-01-01 row.

---

## 0.9 `CLAUDE.md` is out of date in four places

Correct before building on it:

1. **"Iron ore is not a BCOM constituent — AUD needs no orthogonalization and is
   the clean pair."** The first clause is true; the conclusion is not. AUD is now
   the *most* caveated pair — average-price settlement plus the largest
   commodity-to-FX timing gap.
2. **"Golden source resolved by a fresh CL1 pull."** It was not. The API was
   suspended before the pull. See Phase 1.
3. **"CAD is ~9.1% of DXY."** Wrong index — see 0.5.
4. **The pairs table** can now name `SCO1 Comdty` instead of a description.

---

## Still outstanding in Phase 0

**Settlement times.** `DES` is unavailable, but CME, ICE, LME and SGX publish
contract specifications on their own websites. Source them there, cite the
exchange rather than Bloomberg, and mark them `source: exchange website, not
verified on DES`. This unblocks the timing analysis, which is otherwise the
largest open item in the project.

**Split `BBG.xlsx` into six CSVs** — one file per table, per the guide.

**Fill the source log** from sections 0.1–0.7.
