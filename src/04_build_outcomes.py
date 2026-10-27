"""04_build_outcomes - FX-side variables, built independently of the signals.

Applies convention A (DD-01): every rate is expressed as USD per unit of the
commodity currency, so a positive return always means the commodity currency
appreciated and beta is expected positive in all four pairs.

Inverting a rate and negating its log return are the same operation, since
log(1/x) = -log(x). We negate rather than invert the price so the stored price
columns stay as pulled.

Produces, per currency:
  <X>_ds            log return under convention A
  <X>_span_days     calendar days spanned by that return
  <X>_long_span     span > 5 calendar days (DD-14; material for CLP)
  <X>_dropped       excluded date (DD-20; USDNOK 2010-01-01)

plus the dollar controls, the BCOM-free placebo outcome (DD-22), and the
variable dictionary the reproducibility record requires.

Outputs
  data/interim/outcomes.csv
  manifests/variable_dictionary.csv
  outputs/diagnostics/sign_check.csv
"""
from __future__ import annotations

import csv

import numpy as np
import pandas as pd

from _common import load, banner

FZ = load("00_design_freeze")
import data_compile as DC  # noqa: E402

OUT = FZ.INTERIM / "outcomes.csv"
DIAG = FZ.OUTPUTS / "diagnostics"

# FX column -> (pair, invert?) from the frozen config
FX = {spec["fx"]: (pair, spec["invert"]) for pair, spec in FZ.PAIRS.items()}
PLACEBO = FZ.PLACEBO          # USDCHF_PX_LAST - non-commodity G10 control


def _fx_returns(px: pd.Series, invert: bool) -> tuple[pd.Series, pd.Series]:
    """Convention-A log return and the calendar span it covers.

    log(1/x) = -log(x), so inverting the quote is a sign flip on the return.

    Returns are computed between consecutive OWN quotes, not consecutive rows of
    the joined index: a USDCLP return spanning the 2012 coverage hole must EXIST
    in order to be flagged and excluded by DD-14. Computing it on the joined
    index would make it NaN, which is a silent deletion.
    """
    own = px.dropna()
    pos = own.gt(0)
    usable = pos & pos.shift(fill_value=False)
    lr = np.log(own / own.shift()).where(usable)
    ds = (-lr if invert else lr).reindex(px.index)
    span = pd.Series(own.index, index=own.index).diff().dt.days.reindex(px.index)
    return ds, span


def build() -> pd.DataFrame:
    cur = DC.curncy_df
    out = pd.DataFrame(index=cur.index)

    drop_dates = pd.to_datetime(FZ.NOK_DROP_DATES)

    for col, (pair, invert) in FX.items():
        stem = col.replace("_PX_LAST", "")
        px = cur[col].astype(float).copy()

        dropped = pd.Series(False, index=cur.index)
        hit = cur.index.isin(drop_dates) & px.notna()
        if col.startswith("USDNOK") and hit.any():
            dropped.loc[hit] = True
            px.loc[hit] = np.nan          # DD-20: FX does not trade on 1 Jan

        ds, span = _fx_returns(px, invert)
        out[f"{stem}_ds"] = ds
        out[f"{stem}_span_days"] = span
        out[f"{stem}_long_span"] = span.gt(FZ.CLP_MAX_SPAN_DAYS)
        out[f"{stem}_dropped"] = dropped

    # placebo outcome (DD-22): Switzerland exports none of the four commodities
    if PLACEBO in cur.columns:
        ds, span = _fx_returns(cur[PLACEBO].astype(float), invert=True)
        stem = PLACEBO.replace("_PX_LAST", "")
        out[f"{stem}_ds"] = ds
        out[f"{stem}_span_days"] = span

    # dollar controls
    dxy = DC.usd_df[FZ.DOLLAR]
    out["d_dollar"] = np.log(dxy / dxy.shift()).reindex(out.index)
    broad = DC.usdbroad_df[FZ.DOLLAR_ROBUST]
    out["d_dollar_broad"] = np.log(broad / broad.shift()).reindex(out.index)
    return out


def sign_check(out: pd.DataFrame) -> pd.DataFrame:
    """Every convention-A FX return must correlate NEGATIVELY with the dollar.

    A positive correlation means an inversion was missed. This is the automated
    half of DD-01; the hand-calculated example is the other half.
    """
    rows = []
    for col, (pair, invert) in FX.items():
        stem = col.replace("_PX_LAST", "")
        d = out[[f"{stem}_ds", "d_dollar"]].dropna()
        rho = d.corr().iloc[0, 1]
        rows.append({"pair": pair, "series": stem, "inverted": invert,
                     "corr_with_dollar": round(rho, 4), "n": len(d),
                     "result": "PASS" if rho < 0 else "FAIL"})
    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "sign_check.csv", index=False)
    return df


VARDICT = [
    ("<CCY>_ds", "outcome", "log(S_t / S_{t-1}), negated where the quote is "
     "local-per-USD", "log return, USD per unit of commodity currency",
     "FX snap, convention unverified (DD-18)", "DD-01"),
    ("<CCY>_span_days", "diagnostic", "calendar days since the previous valid quote",
     "days", "n/a", "DD-14"),
    ("<CCY>_long_span", "flag", "span_days > 5", "bool", "n/a", "DD-14"),
    ("<CCY>_dropped", "flag", "date excluded as a non-trading observation",
     "bool", "n/a", "DD-20"),
    ("<COMM>_lret", "signal", "log(P_t / P_{t-1}), NA on roll and indeterminate days",
     "log return", "exchange settlement, unverified (DD-18)", "DD-05"),
    ("<COMM>_roll", "flag", "contract pointer changed vs previous date", "bool",
     "n/a", "DD-05"),
    ("IRON_k", "schedule", "trading day within the contract month, 1-based",
     "count", "n/a", "DD-12"),
    ("IRON_N", "schedule", "trading days in that contract month", "count", "n/a", "DD-12"),
    ("IRON_w", "schedule", "(N - k + 1) / N, pass-through of an index move to the future",
     "fraction", "n/a", "DD-12"),
    ("IRON_early_baseline", "flag", "k <= 8, the frozen AUD baseline sample",
     "bool", "n/a", "DD-12"),
    ("IRON_lret_rescaled", "signal", "IRON_lret / IRON_w, attenuation removed",
     "log return", "as IRON_lret", "DD-12"),
    ("BCOM_perp_<PAIR>", "control", "residual from regressing BCOM return on the "
     "pair's own commodity return", "log return", "index close", "DD-03"),
    ("d_dollar", "control", "log return of ICE DXY", "log return",
     "unverified", "DD-13"),
    ("d_dollar_broad", "control", "log return of the Fed H.10 broad dollar index; "
     "robustness only", "log return", "unverified", "DD-13"),
    ("USDCHF_ds", "placebo", "convention-A return on a non-commodity G10 currency",
     "log return", "as other FX", "DD-22"),
]


def write_vardict() -> None:
    path = FZ.MANIFESTS / "variable_dictionary.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["variable", "role", "formula", "units", "timing", "decision"])
        w.writerows(VARDICT)


def main() -> None:
    banner("04_build_outcomes",
           ["data_compile.curncy_df", "data_compile.usd_df", "data_compile.usdbroad_df"],
           [str(OUT.relative_to(FZ.ROOT)), "manifests/variable_dictionary.csv",
            "outputs/diagnostics/sign_check.csv"])

    out = build()
    out.to_csv(OUT, index_label="Date")
    write_vardict()

    chk = sign_check(out)
    print("\n  sign check (DD-01) - every series must be NEGATIVE vs the dollar")
    for _, r in chk.iterrows():
        inv = "inverted" if r.inverted else "as pulled"
        print(f"    {r.pair}  {r.series:<8} {inv:<10} rho={r.corr_with_dollar:+.4f}"
              f"  n={r.n:<5} [{r['result']}]")
    if (chk["result"] == "FAIL").any():
        print("\n    *** SIGN CHECK FAILED - an inversion was missed. Stop here. ***")

    print("\n  long-span returns (DD-14)")
    for col, (pair, _) in FX.items():
        stem = col.replace("_PX_LAST", "")
        n = int(out[f"{stem}_long_span"].fillna(False).sum())
        mx = out[f"{stem}_span_days"].max()
        print(f"    {pair}  {n:>3} returns span > {FZ.CLP_MAX_SPAN_DAYS} days"
              f"  (max {mx:.0f})")

    ndrop = int(sum(out[f"{c.replace('_PX_LAST','')}_dropped"].sum() for c in FX))
    print(f"\n  excluded dates (DD-20): {ndrop}")
    print(f"  wrote {out.shape[0]} rows x {out.shape[1]} cols -> {OUT.name}")


if __name__ == "__main__":
    main()
