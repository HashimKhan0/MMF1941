"""01_source_inventory - resolve every raw file against the RiskLab catalog and
check source coverage.

The guide requires stable dataset IDs retained in the manifest, not invented
ones. The IDs below were read from the RiskLab catalog (`_catalog/catalog.csv`,
schema: id,path,domain,asset_class,ticker_or_id,concept,frequency,fields,...,
sha256,duplicate_group,golden_source,validator_status,issues,...) on 2026-10-26.

Emits manifests/source_inventory.csv: one row per raw file, with the catalog ID,
the catalog's own sha256, the hash of the local copy, and whether they agree.

A hash mismatch is not automatically an error - a format conversion or a Drive
text export changes bytes without changing content - but it must be visible.
"""
from __future__ import annotations

import csv
import hashlib
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
FZ = import_module("src.00_design_freeze") if __package__ else None
if FZ is None:                                     # direct execution
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "freeze", Path(__file__).resolve().parent / "00_design_freeze.py")
    FZ = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(FZ)

# RiskLab catalog records, read 2026-10-26. Do not edit by hand - re-read the
# catalog if a path or hash changes.
CATALOG = [
    dict(catalog_id="RL-495F49CB82F5",
         catalog_path="bloomberg/02_market/futures/AT-04_Daily_Spot_Prices_G10_FX_Pairs_Daily_2000_2025.csv",
         local_file="AT-04_Daily_Spot_Prices_G10_FX_Pairs_Daily_2000_2025.csv",
         catalog_sha256="", golden_source="", rows="", start="2000-01-03", end="2025-09-19",
         note="Filed under 02_market/futures, NOT 02_market/fx (which is empty). Supplies AUDUSD, USDCAD and the USDCHF placebo."),
    dict(catalog_id="RL-36290DAB949B",
         catalog_path="bloomberg/02_market/em/EM-17_USD_Index_DXY_PX-LAST_Daily.csv",
         local_file="EM-17_USD_Index_DXY_PX-LAST_Daily.csv",
         catalog_sha256="18ed5997ec84c0dfee3b8740010cb70758ee4db9584586d628183df394b7669b",
         golden_source="Y", rows="7977", start="1995-01-03", end="2025-09-26",
         note="ICE DXY - the control the brief names. Verified 77.525 on 2010-01-04, 114.106 on 2022-09-27, 71.329 low 2008. Zero missing in window. Local copy retrieved via Drive text export 2026-10-26, so bytes differ from the catalog sha256 - REPLACE with the library original before the final run."),
    dict(catalog_id="RL-B4C76E222224",
         catalog_path="bloomberg/04_macro/USD_Index_DXY_Daily.csv",
         local_file="USD_Index_DXY_Daily.csv",
         catalog_sha256="472e258712bf48cefec5d4be0b62bf810635b74cae00ea3bf4ea7fa4c5431b21",
         golden_source="Y", rows="5185", start="2006-01-02", end="2025-11-14",
         note="MISNAMED. Not ICE DXY - it is the Fed H.10 nominal broad dollar index, base Jan 2006 = 100. Retained as the robustness dollar control. 188 missing in window. Catalog flags RL-E90AD131D587 (USD_Index_DXY_Intraday.csv) as a byte-identical duplicate of this file."),
    dict(catalog_id="RL-38259EF0EF46",
         catalog_path="bloomberg/02_market/em/Commodity_Index_BCOM_Price_Daily.csv",
         local_file="Commodity_Index_BCOM_Price_Daily.csv",
         catalog_sha256="71165a245119945472848cd1ffd08517a7714e6e7ac9b6e090e7a4585c8d704f",
         golden_source="Y", rows="7715", start="1994-12-30", end="2025-09-23",
         note="Price index, not BCOMTR. Binds the CLP and NOK sample ends at 2025-09-23. Stored descending."),
    dict(catalog_id="RL-20930E28331E",
         catalog_path="bloomberg/02_market/etfs/Crude_Oil_WTI_Spot_Daily.csv",
         local_file="Crude_Oil_WTI_Spot_Daily.csv",
         catalog_sha256="6326c905dadc5ea31631673f377565a513f9276c12a22e3d745f31300bc01d20",
         golden_source="Y", rows="7743", start="1994-12-09", end="2025-09-26",
         note="CATALOG MARKS THIS GOLDEN SOURCE - resolves DD-17 against AT-03 on evidence rather than by decision. Named 'Spot' but contains CL1 front-month futures. Stored descending."),
    dict(catalog_id="RL-8446FDC012D6",
         catalog_path="bloomberg/02_market/em/Copper_Price_Daily.csv",
         local_file="Copper_Price_Daily.xlsx",
         catalog_sha256="f538757732eeda4a8493c485da2567dd271fbcbfafb40588cc14a7a10e0799d0",
         golden_source="Y", rows="7738", start="1995-01-03", end="2025-10-01",
         note="Local copy is .xlsx; the catalog record is the .csv. Hash will not match - format conversion. COMEX HG1, used only to orthogonalize BCOM for CLP. PX_BID column unusable."),
    dict(catalog_id="",
         catalog_path="(not a catalog record - student Bloomberg pull)",
         local_file="BBG.xlsx",
         catalog_sha256="", golden_source="", rows="", start="2010-01-01", end="2025-12-31",
         note="Six sheets: nok, clp, wti, brent, iron, copper. Pulled by the student 2026-09-27 via BDH. No catalog ID - not a library file. Provenance is manifests/bloomberg_source_log.csv."),
]

# Catalog records considered and rejected, kept so the choice is auditable.
REJECTED = [
    dict(catalog_id="RL-AABD123B1625",
         catalog_path="bloomberg/02_market/em/USD_Index_DXY_Daily.csv",
         reason="Third DXY copy: same 1995-2025 range and row count as RL-36290DAB949B but a different sha256 and size (140,905 vs 149,281). Not used - RL-36290DAB949B chosen as the EM-17 task output with explicit provenance."),
    dict(catalog_id="RL-E90AD131D587",
         catalog_path="bloomberg/04_macro/USD_Index_DXY_Intraday.csv",
         reason="Byte-identical duplicate of RL-B4C76E222224 despite the 'Intraday' name; catalog marks golden_source=N. Confirms the earlier suspicion that the filename is wrong."),
    dict(catalog_id="RL-48DA2EB8968B",
         catalog_path="bloomberg/02_market/em/EM-27_CLP-Curncy_PX-LAST_2009-2025.csv",
         reason="CLP spot, but starts 2015-01-02 (2,724 rows) despite the 2009 filename, and is on a different pricing source. Five years short of the study window. USDCLP pulled fresh instead."),
]

COLS = ["local_file", "catalog_id", "catalog_path", "golden_source", "catalog_rows",
        "catalog_start", "catalog_end", "local_bytes", "local_sha256",
        "catalog_sha256", "hash_match", "note"]


def main() -> None:
    rows, problems = [], []
    for rec in CATALOG:
        path = FZ.RAW / rec["local_file"]
        if not path.exists():
            problems.append(f"MISSING: {rec['local_file']}")
            continue
        blob = path.read_bytes()
        local = hashlib.sha256(blob).hexdigest()
        cat = rec["catalog_sha256"]
        match = "n/a" if not cat else ("YES" if local == cat else "NO")
        if match == "NO":
            problems.append(f"hash differs: {rec['local_file']} (see note)")
        rows.append({
            "local_file": rec["local_file"], "catalog_id": rec["catalog_id"],
            "catalog_path": rec["catalog_path"], "golden_source": rec["golden_source"],
            "catalog_rows": rec["rows"], "catalog_start": rec["start"],
            "catalog_end": rec["end"], "local_bytes": len(blob),
            "local_sha256": local, "catalog_sha256": cat,
            "hash_match": match, "note": rec["note"],
        })

    out = FZ.MANIFESTS / "source_inventory.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)

    rej = FZ.MANIFESTS / "source_inventory_rejected.csv"
    with open(rej, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["catalog_id", "catalog_path", "reason"])
        w.writeheader()
        w.writerows(REJECTED)

    print(f"{len(rows)} source files resolved -> {out.relative_to(FZ.ROOT)}")
    for r in rows:
        cid = r["catalog_id"] or "(no catalog id)"
        print(f"  {cid:<18} {r['local_file']:<56} hash {r['hash_match']}")
    print(f"\n{len(REJECTED)} catalog records considered and rejected "
          f"-> {rej.relative_to(FZ.ROOT)}")
    if problems:
        print("\nFLAGS (not failures - each is explained in the note column):")
        for p in problems:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
