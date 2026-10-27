# Raw data provenance

**MMF1941 Project 1 (A14-03)** · recorded 2026-10-27

Every file in this folder, where it came from, and whether it may leave this
machine. The folder name is historical: **most of it is not a Bloomberg pull.**
Seven of the eight files are RiskLab library files reached through the shared
Drive, and only `BBG.xlsx` was pulled from the terminal by the student.

Authoritative records, which this file summarizes rather than replaces:

- `manifests/source_inventory.csv` — catalog ID, catalog SHA-256, local SHA-256, match
- `manifests/source_inventory_rejected.csv` — catalog records considered and rejected
- `manifests/bloomberg_source_log.csv` — per-series retrieval log, 17 columns
- `FREEZE.md` — SHA-256 of every raw input as of the specification freeze

---

## Student Bloomberg pull — redistributable

| File | Retrieved | Supplies |
|---|---|---|
| `BBG.xlsx` | 2026-09-27, BDH via the Excel add-in | Six sheets: `nok`, `clp`, `wti`, `brent`, `iron`, `copper`. USDNOK and USDCLP spot; CO1 Brent and SCO1 iron ore front-month generics with their `FUT_CUR_GEN_TICKER` roll columns; LMCADS03 copper forward; CL1 contract codes. |

This is the only raw file produced by the student, and the only one included in
any upload or submission.

Two rows in the source log are recorded against this file as **not obtained**:
SGX `VOLUME`/`OPEN_INT` (the liquidity diagnostic — `PX_VOLUME` returned nothing
and access was lost before it could be resolved) and a CL1 adjudication pull that
was never executed. Both are logged rather than dropped.

## RiskLab library — not redistributable

Reached through the RiskLab shared Drive. These are provider files: they are
never edited, and they are **excluded from any upload**. A reader with library
access resolves each one by its catalog ID; the SHA-256 in `FREEZE.md` confirms
the exact bytes used.

| File | Catalog ID | Golden | Supplies |
|---|---|---|---|
| `AT-04_Daily_Spot_Prices_G10_FX_Pairs_Daily_2000_2025.csv` | `RL-495F49CB82F5` | | AUDUSD, USDCAD, and the USDCHF placebo. Filed under `02_market/futures`, not `02_market/fx`, which is empty. |
| `EM-17_USD_Index_DXY_PX-LAST_Daily.csv` | `RL-36290DAB949B` | Y | ICE DXY, the dollar control the brief names. Local copy is a Drive text export, so its bytes differ from the catalog SHA-256. |
| `USD_Index_DXY_Daily.csv` | `RL-B4C76E222224` | Y | **Misnamed.** Not ICE DXY but the Fed H.10 nominal broad dollar index, base Jan 2006 = 100. Retained as the robustness dollar control. |
| `Commodity_Index_BCOM_Price_Daily.csv` | `RL-38259EF0EF46` | Y | BCOM price index, not BCOMTR. Binds the CLP and NOK sample ends at 2025-09-23. Stored descending. |
| `Crude_Oil_WTI_Spot_Daily.csv` | `RL-20930E28331E` | Y | CL1 front-month futures despite the "Spot" name. Catalog marks it golden source, which settled the WTI source question on evidence. Stored descending. |
| `Copper_Price_Daily.xlsx` | `RL-8446FDC012D6` | Y | COMEX HG1, used only to orthogonalize BCOM for CLP. Local copy is `.xlsx` against a `.csv` catalog record, so the hash differs by format conversion. `PX_BID` is unusable. |
| `AT-03_WTI_CL1_extract.csv` | task output, RiskLab Drive | | Alternative WTI series, used once to test the golden source against it. Identical on 3,960 of 3,961 dates. |

---

## Consolidation, 2026-10-27

There were two raw folders. `raw_data/` was removed: its six data files were
byte-identical duplicates of the copies here, verified by SHA-256, and its
`bloomberg_source_log.csv` was a superseded draft still carrying `TBC`
placeholders and an unresolved iron ore ticker. The live log is
`manifests/bloomberg_source_log.csv`.

`data/raw_bloomberg/` is the single raw folder and is the path `config/
project_config.yaml` resolves as `paths.raw`.

## Reproducing without library access

The pipeline will not run end to end from `BBG.xlsx` alone, because the FX
outcomes, both dollar controls and the commodity index all come from the library
files above. What travels instead is the specification and the audit trail: the
catalog IDs resolve each input for anyone inside RiskLab, `FREEZE.md` fixes the
bytes, and `outputs/tables/` carries every number the paper reports.
