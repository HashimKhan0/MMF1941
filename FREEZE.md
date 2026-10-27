# FREEZE.md — specification freeze record

**MMF1941 Project 1 · A14-03 · Khan, Hashim**

## Frozen 2026-10-26

The specification in `design_decisions.md` (D1–D7) and
`config/project_config.yaml` is frozen as of this date. **No primary estimate
had been produced when this record was written.** `src/07_primary_estimation`
did not yet exist.

### Why this record exists

The implementation guide asks for an approving supervisor on each decision. None
was available. A signature would in any case be a weaker guarantee than what is
recorded here, because a signature cannot be checked after the fact and these
hashes can.

The claim being made is narrow and verifiable: **the specification below existed,
in exactly this form, before any coefficient of interest was computed.** Anyone
can confirm it by hashing these files at the freeze commit and checking that the
freeze commit precedes the first estimation commit in the git history.

Signature lines in `design_decisions.md` are deliberately left blank. They are
not to be back-filled.

### What is frozen

Estimand, sample, horizons, loss function, inference and multiple-testing
treatment (D1); sign convention, pair mapping, roll rule and orthogonalization
(D2); instrument and source choices (D3); exclusions and their thresholds (D4);
timing treatment (D5); the date-shift criterion, placebo, forecast-origin table
and bug detector (D6); and the AUD case-study framing (D7).

One item remains open and is declared as open: **O1**, the CAD-excluded dollar
factor. It is a robustness construction, not part of the baseline.

### Specification files at freeze

| File | SHA-256 |
|---|---|
| `config/project_config.yaml` | `b19a28a38609cfe9864f0f695bb83aadd87fbd4c8b4a9574e8eb90933064bffb` |
| `design_decisions.md` | `1860f48b8c7a79881c85376bafac7b7db6f0be431be531b87360c323d9452c9e` |
| `CLAUDE.md` | `b0bb512985a827df7e81992b31820116691f01d3bacfceb0d7300f89af75ef4d` |
| `data_compile.py` | `26e78f70dfc5c4830c2c7a10fadd0a6bbc1b9c37729837dd00381b0a9c34e002` |
| `src/00_design_freeze.py` | `ef0a26af98d44f41783957bd707e4320f0b408d71e4d356267a41057da4bdd25` |
| `src/01_source_inventory.py` | `f0c1dd9c5542c467915edbdad37a81a96bd5e6f7f26eca69e0140f4668155b79` |
| `src/03_build_events_or_signals.py` | `e97e379d97c87baf564111970e7477be67c9493eb02d9c4ac60305e038523f43` |
| `src/04_build_outcomes.py` | `ad6d947226ac7a8df063266652c735a090df79855566b2134bfb1bf0012f1a9c` |
| `src/05_merge_analysis_panel.py` | `2308f80c3cb1b5f3bf55ca380bbb191ecc980521aaf131b4f25803456d00b8c3` |
| `src/06_descriptive_diagnostics.py` | `d1585e694959b5e4a3e2d2f9e2e83b97c4453b1b5f6e142c74741ef005b80701` |

### Raw data at freeze

| File | SHA-256 |
|---|---|
| `AT-04_Daily_Spot_Prices_G10_FX_Pairs_Daily_2000_2025.csv` | `798c0d24a7fa8e7f2d7c20ee75cbb1d0b0cd1757508c2aeba01a230cca1f3a10` |
| `BBG.xlsx` | `c78fee675fcc7b3d6e522fd20fa2180ca34223271c213ea18ed8cc47de6cb41c` |
| `Commodity_Index_BCOM_Price_Daily.csv` | `71165a245119945472848cd1ffd08517a7714e6e7ac9b6e090e7a4585c8d704f` |
| `Copper_Price_Daily.xlsx` | `5413c3e37201531949ce17eafc71c92ee8e67f2f76af33e259b3cd75912eb2c2` |
| `Crude_Oil_WTI_Spot_Daily.csv` | `6326c905dadc5ea31631673f377565a513f9276c12a22e3d745f31300bc01d20` |
| `EM-17_USD_Index_DXY_PX-LAST_Daily.csv` | `18ed5997ec84c0dfee3b8740010cb70758ee4db9584586d628183df394b7669b` |
| `USD_Index_DXY_Daily.csv` | `472e258712bf48cefec5d4be0b62bf810635b74cae00ea3bf4ea7fa4c5431b21` |

Four of these match the RiskLab catalog's own recorded hashes exactly
(`manifests/source_inventory.csv`). `Copper_Price_Daily.xlsx` differs because it
is a format conversion of the catalogued `.csv`; `BBG.xlsx` is a student pull
with no catalog record, its provenance in `manifests/bloomberg_source_log.csv`.

### Sample at freeze

| Pair | Contemporaneous | Predictive (h=1) | Window |
|---|---|---|---|
| AUD | 1,023 | 1,022 | 2013-04-09 → 2025-09-10 |
| CAD | 3,766 | 3,765 | 2010-01-05 → 2025-09-19 |
| CLP | 3,629 | 3,628 | 2010-01-05 → 2025-09-23 |
| NOK | 3,774 | 3,773 | 2010-01-05 → 2025-09-23 |
| Pooled (ex-AUD per D7) | — | — | recomputed at estimation |

### Environment

- Python 3.13.17 · pandas 3.0.5 · numpy 2.5.3 · pyyaml 6.0.3
- Platform at freeze: Linux x86_64
- Seed: 20261026

### Diagnostics on record before the freeze

`outputs/diagnostics/` — sign check (4/4 pass), roll counts, iron ore decay
profile, iron ore β by contract-month bucket, timing gaps, date-shift test, ten
hand checks (5 agree, 5 excluded by design), five-observation reproduction (4/4
exact), join audit (clean).

### After this point

Any change to a frozen item requires a dated line in `design_decisions.md`
§Amendments stating what changed and why, and must not be motivated by a result.
