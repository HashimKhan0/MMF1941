"""05_merge_analysis_panel - audited join of signals and outcomes, one panel per
pair, with an explicit attrition table and a forecast-origin table.

The join is an inner join on dates where every required series is valid. Each
stage records how many rows it removed and why, so the final N can be traced
back to the union of dates without re-running anything.

Outputs
  data/analytic/panel_<PAIR>.csv
  data/analytic/panel_AUD_full.csv        AUD before the DD-12 restriction (D7)
  data/analytic/panel_pooled.csv
  manifests/sample_attrition.csv
  manifests/forecast_origins.csv          (DD-23)
  outputs/diagnostics/join_audit.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import load, banner

FZ = load("00_design_freeze")

SIG = FZ.INTERIM / "signals.csv"
OUTC = FZ.INTERIM / "outcomes.csv"
DIAG = FZ.OUTPUTS / "diagnostics"


def _stage(rows: list, pair: str, stage: str, n: int, prev: int | None, cause: str) -> None:
    rows.append({"pair": pair, "stage": stage, "n_remaining": n,
                 "n_dropped": None if prev is None else prev - n, "cause": cause})


def build_pair(pair: str, sig: pd.DataFrame, outc: pd.DataFrame,
               attrition: list, audit: list) -> pd.DataFrame:
    spec = FZ.PAIRS[pair]
    fx_stem = spec["fx"].replace("_PX_LAST", "")
    comm_stem = spec["commodity"].replace("_PX_LAST", "")

    ds = outc[f"{fx_stem}_ds"]
    dc = sig[f"{comm_stem}_lret"]
    bcom = sig[f"BCOM_perp_{pair}"]
    dollar = outc["d_dollar"]
    dollar_b = outc["d_dollar_broad"]

    union = ds.index.union(dc.index)
    _stage(attrition, pair, "0 union of dates", len(union), None,
           "any required series has a row")

    df = pd.DataFrame({"ds": ds, "dc": dc, "d_dollar": dollar,
                       "bcom_perp": bcom, "d_dollar_broad": dollar_b}).reindex(union)

    # stage 1 - every required series present
    req = ["ds", "dc", "d_dollar", "bcom_perp"]
    n0 = len(df)
    missing = {c: int(df[c].isna().sum()) for c in req}
    df = df.dropna(subset=req)
    cause = "; ".join(f"{c} missing {n}" for c, n in sorted(missing.items(),
                                                            key=lambda kv: -kv[1]) if n)
    _stage(attrition, pair, "1 inner join: all required series valid", len(df), n0, cause)

    # stage 2 - pair start date (DD-15 for AUD)
    n1 = len(df)
    df = df[df.index >= pd.Timestamp(spec["start"])]
    _stage(attrition, pair, "2 pair start date", len(df), n1, spec["start"])

    # stage 3 - excluded observations already NA upstream, recorded for the trail
    n2 = len(df)
    flags = {}
    if spec["contract_field"]:
        flags["roll"] = f"{comm_stem}_roll"
        flags["roll_indeterminate"] = f"{comm_stem}_roll_indeterminate"
    for name, col in flags.items():
        if col in sig.columns:
            df[name] = sig[col].reindex(df.index).fillna(False)
    df["long_span"] = outc[f"{fx_stem}_long_span"].reindex(df.index).fillna(False)
    _stage(attrition, pair, "3 roll and non-positive exclusions", len(df), n2,
           "applied upstream in 03/04; counts in roll_counts.csv")

    # stage 4 - DD-14 long-span returns
    n3 = len(df)
    df = df[~df["long_span"]]
    _stage(attrition, pair, f"4 long-span returns (> {FZ.CLP_MAX_SPAN_DAYS} cal days)",
           len(df), n3, "DD-14")

    # leads for the predictive horizons. Amendment 2026-10-26: the target is the
    # currency's return h trading days ahead on its OWN calendar. Shifting the
    # filtered panel instead skipped every dropped row (rolls, long spans, AUD
    # days 9+), so 5-16% of h=1 and 23-75% of h=5 targets were the wrong day.
    fx_own = outc.loc[outc[f"{fx_stem}_ds"].notna()]
    target = fx_own[f"{fx_stem}_ds"].mask(fx_own[f"{fx_stem}_long_span"].astype(bool))
    for h in (FZ.H_PRIMARY, FZ.H_SECONDARY):
        df[f"ds_lead{h}"] = target.shift(-h).reindex(df.index)
        df[f"ds_lead{h}_date"] = fx_own.index.to_series().shift(-h).reindex(df.index)

    # stage 5 - DD-12 iron ore early-month baseline (AUD only)
    n4 = len(df)
    if pair == "AUD":
        for c in ("IRON_k", "IRON_N", "IRON_w", "IRON_early_baseline",
                  "IRON_early_robust", "IRON_lret_rescaled"):
            df[c] = sig[c].reindex(df.index)
        # D7: the unrestricted sample, for the full and 1/w case-study treatments
        df.assign(pair=pair).to_csv(FZ.ANALYTIC / "panel_AUD_full.csv", index_label="Date")
        df = df[df["IRON_early_baseline"].fillna(False)]
        _stage(attrition, pair,
               f"5 iron ore first {FZ.IRON_BASELINE_DAYS} trading days (DD-12)",
               len(df), n4, "average-price settlement; w = (N-k+1)/N")
    else:
        _stage(attrition, pair, "5 iron ore early-month restriction", len(df), n4,
               "not applicable")

    _stage(attrition, pair, "6 FINAL N contemporaneous", len(df), None,
           f"{df.index.min().date()} -> {df.index.max().date()}" if len(df) else "EMPTY")

    n_pred = int(df[f"ds_lead{FZ.H_PRIMARY}"].notna().sum())
    _stage(attrition, pair, f"7 FINAL N predictive (h={FZ.H_PRIMARY})", n_pred,
           len(df), "no lead at sample end, or the target is a long-span return")

    # join audit
    audit.append({"pair": pair, "n": len(df),
                  "duplicate_dates": int(df.index.duplicated().sum()),
                  "index_monotonic": bool(df.index.is_monotonic_increasing),
                  "any_all_nan_row": bool(df[["ds", "dc"]].isna().all(axis=1).any()),
                  "start": str(df.index.min().date()) if len(df) else "",
                  "end": str(df.index.max().date()) if len(df) else ""})

    df["pair"] = pair
    return df


def forecast_origins(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """DD-23: one row per forecast origin, with what was observable at it.

    The timing column is deliberately blunt: settlement times are unverified
    (DD-18), so the honest statement is that same-day alignment is assumed, not
    established.
    """
    rows = []
    for pair, df in panels.items():
        for h in (FZ.H_PRIMARY, FZ.H_SECONDARY):
            col = f"ds_lead{h}"
            ok = df[col].notna()
            if not ok.any():
                continue
            idx = df.index[ok]
            rows.append({
                "pair": pair, "horizon": h,
                "n_origins": int(ok.sum()),
                "first_origin": str(idx.min().date()),
                "last_origin": str(idx.max().date()),
                "first_target": str(df.loc[idx.min(), f"ds_lead{h}_date"].date()),
                "information_at_origin": "dc_t, d_dollar_t, bcom_perp_t (all dated t)",
                "target": f"ds_(t+{h})",
                "timing_caveat": "same-day alignment ASSUMED; settlement times "
                                 "unverified (DD-18). Commodity settles before the "
                                 "FX snap in all four pairs.",
            })
    return pd.DataFrame(rows)


def main() -> None:
    banner("05_merge_analysis_panel",
           [str(SIG.relative_to(FZ.ROOT)), str(OUTC.relative_to(FZ.ROOT))],
           ["data/analytic/panel_<PAIR>.csv", "manifests/sample_attrition.csv",
            "manifests/forecast_origins.csv", "outputs/diagnostics/join_audit.csv"])

    sig = pd.read_csv(SIG, index_col="Date", parse_dates=["Date"])
    outc = pd.read_csv(OUTC, index_col="Date", parse_dates=["Date"])

    attrition, audit, panels = [], [], {}
    for pair in FZ.PAIR_NAMES:
        df = build_pair(pair, sig, outc, attrition, audit)
        df.to_csv(FZ.ANALYTIC / f"panel_{pair}.csv", index_label="Date")
        panels[pair] = df

    pooled = pd.concat(df for p, df in panels.items() if p != "AUD").sort_index()  # D7
    pooled.to_csv(FZ.ANALYTIC / "panel_pooled.csv", index_label="Date")

    att = pd.DataFrame(attrition)
    att.to_csv(FZ.MANIFESTS / "sample_attrition.csv", index=False)
    pd.DataFrame(audit).to_csv(DIAG / "join_audit.csv", index=False)
    fo = forecast_origins(panels)
    fo.to_csv(FZ.MANIFESTS / "forecast_origins.csv", index=False)

    print("\n  final samples")
    for pair, df in panels.items():
        pred = int(df[f"ds_lead{FZ.H_PRIMARY}"].notna().sum())
        print(f"    {pair}  contemporaneous {len(df):>5}   predictive {pred:>5}"
              f"   {df.index.min().date()} -> {df.index.max().date()}")
    print(f"    pooled {len(pooled):>5}  (CAD, CLP, NOK - AUD excluded by D7)")

    aud = pd.DataFrame(audit)
    bad = aud[(aud.duplicate_dates > 0) | (~aud.index_monotonic)]
    print(f"\n  join audit: {'clean' if bad.empty else 'PROBLEMS - see join_audit.csv'}")
    print(f"  forecast origins: {len(fo)} rows -> manifests/forecast_origins.csv")


if __name__ == "__main__":
    main()
