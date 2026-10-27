"""03_build_events_or_signals - commodity-side variables, built WITHOUT any
outcome information.

No FX series is read here. That separation is the point: nothing on the signal
side can be tuned against the thing it is supposed to predict.

Produces, per commodity:
  <X>_lret              log return, computed only where the contract pointer is
                        unchanged day-over-day (DD-05); NA on roll days
  <X>_roll              roll-day flag
  <X>_roll_indeterminate contract code missing, so roll status is unknown (Brent)
  <X>_nonpositive       price <= 0, log return undefined (WTI 2020-04-20/21)
  <X>_span_days         calendar days the return covers
  <X>_long_span         span > 5 calendar days

and for iron ore specifically (DD-12):
  IRON_k                trading day within the contract month, 1-based
  IRON_N                trading days in that contract month
  IRON_w                pass-through weight (N - k + 1) / N
  IRON_early_baseline   k <= 8   (the frozen baseline)
  IRON_early_robust     k <= 5   (robustness cut)
  IRON_lret_rescaled    lret / w  (robustness: full sample, attenuation removed)

and per pair:
  BCOM_perp_<PAIR>      BCOM return orthogonalized against that pair's own
                        commodity return (DD-03). AUD has none - iron ore is not
                        a BCOM constituent.

Outputs
  data/interim/signals.csv
  outputs/diagnostics/iron_decay_profile.csv   the DD-12 evidence, regenerated
  outputs/diagnostics/roll_counts.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import load, banner

FZ = load("00_design_freeze")
import data_compile as DC  # noqa: E402  (after sys.path fix in _common)

OUT = FZ.INTERIM / "signals.csv"
DIAG = FZ.OUTPUTS / "diagnostics"

# commodity column -> contract-pointer column (None = no roll)
COMMODITIES = {
    "WTI_PX_LAST": "WTI_FUT_CUR_GEN_TICKER",
    "BRENT_PX_LAST": "BRENT_FUT_CUR_GEN_TICKER",
    "IRON_PX_LAST": "IRON_FUT_CUR_GEN_TICKER",
    "COPPER_PX_LAST": None,          # LMCADS03, constant maturity
    "HG1_PX_LAST": None,             # COMEX, contract field not retrievable
}


def _log_returns(px: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Log returns between consecutive OWN observations, plus flags.

    `comm_df` is an outer join, so shifting on the joined index would compare a
    price to a blank whenever another series traded and this one did not - the
    return would silently vanish. Returns are therefore computed on the series'
    own observations and then reindexed, and the calendar span each return
    covers is carried so a gap-spanning return can be flagged rather than lost.

    A log return needs both endpoints strictly positive, so one bad print kills
    two returns: the one into it and the one out of it (DD-16).
    """
    own = px.dropna()
    pos = own.gt(0)
    usable = pos & pos.shift(fill_value=False)
    lr = np.log(own / own.shift()).where(usable)
    span = pd.Series(own.index, index=own.index).diff().dt.days
    return (lr.reindex(px.index), span.reindex(px.index),
            (~px.gt(0)) & px.notna())


def _roll_flags(ticker: pd.Series, px: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Roll-day flag and indeterminate flag, evaluated on the series' OWN rows.

    `comm_df` is an outer join, so most NA tickers are simply dates this series
    did not trade. Those are absent, not indeterminate. A roll is a change in
    the code between two CONSECUTIVE OWN observations; indeterminate means the
    series did trade but the code is missing, so we cannot tell whether a roll
    happened (DD-05: Brent 2010-08-30 and 2023-01-02, four observations).
    """
    own = px.notna()
    t = ticker.where(own)
    prev = t.loc[own].shift()                      # previous OWN observation
    prev = prev.reindex(ticker.index)

    roll = pd.Series(False, index=ticker.index)
    indet = pd.Series(False, index=ticker.index)

    have_both = own & t.notna() & prev.notna()
    roll.loc[have_both] = t[have_both].ne(prev[have_both])

    first_own = own & ~prev.notna()
    indet.loc[own & ~first_own & (t.isna() | prev.isna())] = True
    return roll, indet


def _iron_schedule(ticker: pd.Series) -> pd.DataFrame:
    """k, N and w = (N-k+1)/N for the iron ore contract month (DD-12).

    The front-month generic for month M settles against M's average, so k counts
    trading days inside the current contract and N is that contract's total.
    """
    grp = ticker.ne(ticker.shift()).cumsum()
    k = ticker.groupby(grp).cumcount() + 1
    n = ticker.groupby(grp).transform("size")
    w = (n - k + 1) / n
    return pd.DataFrame({"IRON_k": k, "IRON_N": n, "IRON_w": w}, index=ticker.index)


def build() -> pd.DataFrame:
    comm = DC.comm_df
    sig = pd.DataFrame(index=comm.index)
    roll_counts = []

    for px_col, tk_col in COMMODITIES.items():
        stem = px_col.replace("_PX_LAST", "")
        px = comm[px_col].astype(float)
        lret, span, nonpos = _log_returns(px)

        if tk_col:
            roll, indet = _roll_flags(comm[tk_col], px)
            lret = lret.where(~roll)            # DD-05: drop, do not adjust
            lret = lret.where(~indet)
            own_dates = comm.index[px.notna()]
            years = (own_dates[-1] - own_dates[0]).days / 365.25
            roll_counts.append({"series": stem, "rolls": int(roll.sum()),
                                "years": round(years, 1),
                                "rolls_per_year": round(roll.sum() / years, 1),
                                "indeterminate": int(indet.sum())})
        else:
            roll = pd.Series(False, index=comm.index)
            indet = pd.Series(False, index=comm.index)
            roll_counts.append({"series": stem, "rolls": 0, "years": None,
                                "rolls_per_year": 0.0, "indeterminate": 0})

        sig[f"{stem}_lret"] = lret
        sig[f"{stem}_span_days"] = span
        sig[f"{stem}_long_span"] = span.gt(FZ.CLP_MAX_SPAN_DAYS)
        sig[f"{stem}_roll"] = roll
        sig[f"{stem}_roll_indeterminate"] = indet
        sig[f"{stem}_nonpositive"] = nonpos

    # --- DD-12: iron ore pass-through schedule -----------------------------
    sched = _iron_schedule(comm["IRON_FUT_CUR_GEN_TICKER"])
    sig = sig.join(sched)
    sig["IRON_early_baseline"] = sig["IRON_k"].le(FZ.IRON_BASELINE_DAYS)
    sig["IRON_early_robust"] = sig["IRON_k"].le(FZ.IRON_ROBUST_DAYS)
    sig["IRON_lret_rescaled"] = sig["IRON_lret"] / sig["IRON_w"]

    # --- DD-03: BCOM orthogonalized per pair -------------------------------
    bcom = np.log(DC.bcom_df[FZ.BCOM] / DC.bcom_df[FZ.BCOM].shift())
    bcom = bcom.reindex(sig.index)
    sig["BCOM_lret"] = bcom

    for pair, spec in FZ.PAIRS.items():
        tgt = spec["orthogonalize_against"]
        if tgt is None:                      # AUD: iron ore is not in BCOM
            sig[f"BCOM_perp_{pair}"] = bcom
            continue
        own = sig[f"{tgt.replace('_PX_LAST','')}_lret"]
        d = pd.concat([bcom.rename("b"), own.rename("x")], axis=1).dropna()
        beta = np.polyfit(d["x"], d["b"], 1)[0] if len(d) > 2 else np.nan
        alpha = d["b"].mean() - beta * d["x"].mean()
        sig[f"BCOM_perp_{pair}"] = bcom - (alpha + beta * own)
        sig.attrs[f"bcom_loading_{pair}"] = float(beta)

    pd.DataFrame(roll_counts).to_csv(DIAG / "roll_counts.csv", index=False)
    return sig


def decay_profile(sig: pd.DataFrame) -> pd.DataFrame:
    """The DD-12 evidence: mean |return| by trading day within the contract month."""
    d = sig[["IRON_k", "IRON_N", "IRON_w", "IRON_lret"]].dropna(subset=["IRON_lret"])
    g = d.groupby("IRON_k").agg(n=("IRON_lret", "size"),
                                mean_abs_ret_pct=("IRON_lret", lambda s: s.abs().mean() * 100),
                                mean_w=("IRON_w", "mean"))
    g.to_csv(DIAG / "iron_decay_profile.csv")
    return g


def main() -> None:
    banner("03_build_events_or_signals",
           ["data_compile.comm_df", "data_compile.bcom_df"],
           [str(OUT.relative_to(FZ.ROOT)), "outputs/diagnostics/iron_decay_profile.csv",
            "outputs/diagnostics/roll_counts.csv"])

    sig = build()
    sig.to_csv(OUT, index_label="Date")

    rc = pd.read_csv(DIAG / "roll_counts.csv")
    print("\n  rolls")
    for _, r in rc.iterrows():
        extra = f", {int(r.indeterminate)} indeterminate" if r.indeterminate else ""
        print(f"    {r.series:<7} {int(r.rolls):>4} rolls"
              f"  ({r.rolls_per_year}/yr{extra})")

    g = decay_profile(sig)
    print("\n  iron ore pass-through (DD-12 evidence)")
    for k in (2, 5, 8, 12, 18, 21):
        if k in g.index:
            r = g.loc[k]
            print(f"    day {k:>2}  n={int(r.n):>4}  mean|r| {r.mean_abs_ret_pct:5.2f}%"
                  f"  w {r.mean_w:4.2f}")

    base = sig["IRON_early_baseline"] & sig["IRON_lret"].notna()
    rob = sig["IRON_early_robust"] & sig["IRON_lret"].notna()
    full = sig["IRON_lret"].notna()
    print(f"\n  iron ore observations: full {full.sum()}, "
          f"first {FZ.IRON_BASELINE_DAYS}d {base.sum()} (baseline), "
          f"first {FZ.IRON_ROBUST_DAYS}d {rob.sum()} (robustness)")

    print("\n  BCOM loadings (orthogonalization first stage)")
    for pair in FZ.PAIR_NAMES:
        b = sig.attrs.get(f"bcom_loading_{pair}")
        print(f"    {pair}: " + ("not orthogonalized (iron ore not in BCOM)"
                                 if b is None else f"beta = {b:.4f}"))

    print(f"\n  wrote {sig.shape[0]} rows x {sig.shape[1]} cols -> {OUT.name}")


if __name__ == "__main__":
    main()
