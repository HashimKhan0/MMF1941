"""06_descriptive_diagnostics - everything that must be looked at BEFORE the
specification freezes, and nothing that estimates the quantity of interest.

Guide: "Produce descriptive coverage and pre-estimation diagnostics; stop if key
timing or universe assumptions fail."

Six blocks:
  A  timing gaps between each commodity settlement and the FX snap (DD-18)
  B  iron ore beta by day-of-contract-month - the DD-12 falsification test
  C  hand-calculated sign-convention example (DD-01)
  D  ten hand-checked observations, raw source -> final variable
  E  five randomly reproduced observations (seeded)
  F  date-shift test against the rule declared in DD-19

Block B estimates a coefficient, but on a question about the INSTRUMENT, not
about the hypothesis. It is run here deliberately so its answer is on record
before the baseline is frozen.

Outputs under outputs/diagnostics/:
  timing_gaps.csv  iron_beta_by_day.csv  sign_convention_example.md
  hand_checks.csv  reproduction_check.csv  date_shift_test.csv
"""
from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from _common import load, banner

FZ = load("00_design_freeze")
import data_compile as DC  # noqa: E402

DIAG = FZ.OUTPUTS / "diagnostics"
ST = FZ.CFG["settlement_times"]


# ---------------------------------------------------------------- A. timing
def timing_gaps() -> pd.DataFrame:
    """Hours between the commodity settlement and the FX snap, per pair per day.

    Computed per date rather than held constant: Singapore observes no DST, the
    US and UK transition on different weekends, so the gap genuinely moves
    through the year. Guide failure mode 1 requires this be quantified and
    flagged, not assumed away.
    """
    fx = ST["FX_SNAP"]
    fx_h, fx_m = (int(x) for x in fx["local_time"].split(":"))
    fx_tz = ZoneInfo(fx["tz"])

    rows = []
    for pair, spec in FZ.PAIRS.items():
        c = ST[spec["commodity"]]
        c_h, c_m = (int(x) for x in c["local_time"].split(":"))
        c_tz = ZoneInfo(c["tz"])

        panel = pd.read_csv(FZ.ANALYTIC / f"panel_{pair}.csv",
                            index_col="Date", parse_dates=["Date"])
        gaps, dst_weeks = [], []
        for d in panel.index:
            c_utc = pd.Timestamp(d.year, d.month, d.day, c_h, c_m, tz=c_tz).tz_convert("UTC")
            f_utc = pd.Timestamp(d.year, d.month, d.day, fx_h, fx_m, tz=fx_tz).tz_convert("UTC")
            gaps.append((f_utc - c_utc).total_seconds() / 3600)
            dst_weeks.append(bool(c_tz.dst(d.to_pydatetime())) != bool(fx_tz.dst(d.to_pydatetime())))
        g = pd.Series(gaps, index=panel.index)
        rows.append({
            "pair": pair, "commodity": spec["commodity"],
            "commodity_settle": f"{c['local_time']} {c['tz']}",
            "fx_snap": f"{fx['local_time']} {fx['tz']}",
            "verified": c["verified"],
            "modal_gap_hours": round(g.mode().iloc[0], 2),
            "min_gap_hours": round(g.min(), 2), "max_gap_hours": round(g.max(), 2),
            "n_days_off_mode": int((g != g.mode().iloc[0]).sum()),
            "pct_days_off_mode": round((g != g.mode().iloc[0]).mean() * 100, 1),
            "n": len(g),
        })
        panel["timing_gap_hours"] = g
        panel["dst_misaligned"] = dst_weeks
        panel.to_csv(FZ.ANALYTIC / f"panel_{pair}.csv", index_label="Date")

    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "timing_gaps.csv", index=False)
    return df


# ---------------------------------------------------------------- B. DD-12
def _ols(y: pd.Series, X: pd.DataFrame) -> tuple[float, float, int]:
    """Plain OLS slope on the first regressor, its t-stat, and n."""
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    if len(d) < 30:
        return np.nan, np.nan, len(d)
    Xm = np.column_stack([np.ones(len(d)), d[X.columns].to_numpy()])
    yv = d["y"].to_numpy()
    b, *_ = np.linalg.lstsq(Xm, yv, rcond=None)
    resid = yv - Xm @ b
    s2 = resid @ resid / (len(d) - Xm.shape[1])
    se = np.sqrt(s2 * np.linalg.inv(Xm.T @ Xm)[1, 1])
    return float(b[1]), float(b[1] / se), len(d)


def iron_beta_by_day() -> pd.DataFrame:
    """DD-12 falsification: does raw beta rise through the contract month as 1/w?

    If average-price settlement is biting, the futures return understates the
    real move by w, so the fitted slope on it should scale roughly as 1/w. Flat
    means the mechanism is not operating and the full sample is usable - and
    that conclusion is recorded HERE, before the baseline is frozen.

    Run on the UNRESTRICTED AUD join so every day-of-month bucket is populated.
    """
    sig = pd.read_csv(FZ.INTERIM / "signals.csv", index_col="Date", parse_dates=["Date"])
    out = pd.read_csv(FZ.INTERIM / "outcomes.csv", index_col="Date", parse_dates=["Date"])
    df = pd.DataFrame({
        "ds": out["AUDUSD_ds"], "dc": sig["IRON_lret"],
        "d_dollar": out["d_dollar"], "bcom_perp": sig["BCOM_perp_AUD"],
        "k": sig["IRON_k"], "w": sig["IRON_w"],
    }).dropna()

    buckets = [(1, 4), (5, 8), (9, 12), (13, 16), (17, 25)]
    rows = []
    for lo, hi in buckets:
        d = df[(df.k >= lo) & (df.k <= hi)]
        beta, t, n = _ols(d["ds"], d[["dc", "d_dollar", "bcom_perp"]])
        rows.append({"bucket": f"days {lo}-{hi}", "k_lo": lo, "k_hi": hi, "n": n,
                     "mean_w": round(d["w"].mean(), 3),
                     "beta": round(beta, 4) if beta == beta else None,
                     "t_stat": round(t, 2) if t == t else None,
                     "implied_beta_times_w": round(beta * d["w"].mean(), 4)
                     if beta == beta else None})
    res = pd.DataFrame(rows)
    res.to_csv(DIAG / "iron_beta_by_day.csv", index=False)
    return res


# ---------------------------------------------------------------- C. DD-01
def sign_convention_example() -> str:
    """Hand-calculated sign test: one pulled pair and one inverted pair.

    Required by the guide's universal checks, and supplies five of the ten
    hand-checked observations the supervisor checkpoint asks for.
    """
    cur, sig = DC.curncy_df, pd.read_csv(FZ.INTERIM / "signals.csv",
                                         index_col="Date", parse_dates=["Date"])
    iron = sig["IRON_lret"].dropna()
    big = iron[iron.abs() > iron.abs().quantile(0.99)]
    date = next((d for d in big.index
                 if pd.notna(cur["AUDUSD_PX_LAST"].get(d))
                 and pd.notna(cur["USDCAD_PX_LAST"].get(d))), big.index[0])
    prev_a = cur["AUDUSD_PX_LAST"].loc[:date].dropna().iloc[-2]
    now_a = cur["AUDUSD_PX_LAST"].loc[date]
    prev_c = cur["USDCAD_PX_LAST"].loc[:date].dropna().iloc[-2]
    now_c = cur["USDCAD_PX_LAST"].loc[date]

    ds_a = np.log(now_a / prev_a)
    ds_c = -np.log(now_c / prev_c)
    inv_prev, inv_now = 1 / prev_c, 1 / now_c
    ds_c_direct = np.log(inv_now / inv_prev)

    md = f"""# Sign-convention test, worked by hand

**DD-01.** Every rate is USD per unit of the commodity currency, so a positive
return always means the commodity currency appreciated and beta is expected
positive in all four pairs.

Date: **{date.date()}**

## AUDUSD - already USD per unit, used as pulled

    previous close   {prev_a:.5f}  USD per AUD
    this close       {now_a:.5f}  USD per AUD
    ds = ln({now_a:.5f} / {prev_a:.5f}) = {ds_a:+.6f}  ({ds_a*100:+.4f}%)

The rate {'rose' if ds_a > 0 else 'fell'}, so one AUD buys
{'more' if ds_a > 0 else 'fewer'} USD: the AUD
{'appreciated' if ds_a > 0 else 'depreciated'}. s rose => positive return. Correct.

## USDCAD - quoted CAD per USD, must be inverted

    previous close   {prev_c:.5f}  CAD per USD
    this close       {now_c:.5f}  CAD per USD

Inverting the quote:

    previous         1/{prev_c:.5f} = {inv_prev:.6f}  USD per CAD
    this close       1/{now_c:.5f} = {inv_now:.6f}  USD per CAD
    ds = ln({inv_now:.6f} / {inv_prev:.6f}) = {ds_c_direct:+.6f}

Negating the raw log return instead, since log(1/x) = -log(x):

    ds = -ln({now_c:.5f} / {prev_c:.5f}) = {ds_c:+.6f}

The two agree to {abs(ds_c - ds_c_direct):.2e}, which is floating-point noise.
This is why the pipeline negates the return rather than inverting the price: the
stored price column stays exactly as pulled.

The rate {'rose' if np.log(now_c/prev_c) > 0 else 'fell'}, so one USD buys
{'more' if np.log(now_c/prev_c) > 0 else 'fewer'} CAD: the CAD
{'depreciated' if np.log(now_c/prev_c) > 0 else 'appreciated'}. After inversion
ds = {ds_c:+.6f}, which is {'positive' if ds_c > 0 else 'negative'} - the same
economic reading as AUD. Correct.

## Automated counterpart

`outputs/diagnostics/sign_check.csv` requires every convention-A return to
correlate NEGATIVELY with the dollar factor. A positive correlation means an
inversion was missed.
"""
    (DIAG / "sign_convention_example.md").write_text(md, encoding="utf-8")
    return str(date.date())


# ---------------------------------------------------------------- D/E
def hand_checks() -> pd.DataFrame:
    """Ten observations traced raw source -> final variable, chosen not at random.

    Deliberately weighted toward the dates the data is known to be awkward on,
    because a random ten would almost certainly all be ordinary days.
    """
    sig = pd.read_csv(FZ.INTERIM / "signals.csv", index_col="Date", parse_dates=["Date"])
    out = pd.read_csv(FZ.INTERIM / "outcomes.csv", index_col="Date", parse_dates=["Date"])
    comm, cur = DC.comm_df, DC.curncy_df

    picks = [
        ("2013-04-09", "IRON_PX_LAST", "first usable iron ore return (DD-15)"),
        ("2020-04-20", "WTI_PX_LAST", "WTI settles -37.63; log return undefined (DD-16)"),
        ("2020-04-21", "WTI_PX_LAST", "return out of the negative print (DD-16)"),
        ("2010-08-30", "BRENT_PX_LAST", "Brent contract code null; roll indeterminate (DD-05)"),
        ("2023-01-02", "BRENT_PX_LAST", "second Brent null contract code (DD-05)"),
        ("2011-11-30", "USDCLP_PX_LAST", "CLP return spans the 2012 coverage hole (DD-14)"),
        ("2010-01-01", "USDNOK_PX_LAST", "New Year's Day; FX does not trade (DD-20)"),
        ("2025-07-31", "HG1_PX_LAST", "COMEX -22% tariff dislocation absent from LME (DD-02)"),
        ("2015-06-15", "COPPER_PX_LAST", "ordinary day, LME constant maturity, no roll"),
        ("2018-03-14", "AUDUSD_PX_LAST", "ordinary day, pulled series, no inversion"),
    ]
    rows = []
    for ds_, col, why in picks:
        d = pd.Timestamp(ds_)
        src = comm if col in comm.columns else cur
        raw = src[col].get(d, np.nan)
        stem = col.replace("_PX_LAST", "")
        final = (sig.get(f"{stem}_lret", pd.Series(dtype=float)).get(d, np.nan)
                 if col in comm.columns else
                 out.get(f"{stem}_ds", pd.Series(dtype=float)).get(d, np.nan))
        prev = src[col].loc[:d].dropna()
        prev_v = prev.iloc[-2] if len(prev) >= 2 and prev.index[-1] == d else np.nan
        expected = (np.log(raw / prev_v)
                    if pd.notna(raw) and pd.notna(prev_v) and raw > 0 and prev_v > 0
                    else np.nan)
        if col.startswith(("USDCAD", "USDCLP", "USDNOK")) and pd.notna(expected):
            expected = -expected
        agree = ("n/a (excluded by design)" if pd.isna(final)
                 else "YES" if pd.notna(expected) and abs(final - expected) < 1e-12
                 else "CHECK")
        rows.append({"date": ds_, "series": col, "why_chosen": why,
                     "raw_price": raw, "prev_raw_price": prev_v,
                     "hand_computed": expected, "pipeline_value": final,
                     "agrees": agree})
    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "hand_checks.csv", index=False)
    return df


def reproduction_check() -> pd.DataFrame:
    """Five randomly selected observations rebuilt from raw source (seeded)."""
    rng = np.random.default_rng(FZ.SEED)
    rows = []
    for pair in FZ.PAIR_NAMES:
        panel = pd.read_csv(FZ.ANALYTIC / f"panel_{pair}.csv",
                            index_col="Date", parse_dates=["Date"])
        if panel.empty:
            continue
        d = panel.index[rng.integers(0, len(panel))]
        spec = FZ.PAIRS[pair]
        px = DC.curncy_df[spec["fx"]]
        hist = px.loc[:d].dropna()
        hand = np.log(hist.iloc[-1] / hist.iloc[-2])
        if spec["invert"]:
            hand = -hand
        rows.append({"pair": pair, "date": str(d.date()), "variable": "ds",
                     "raw_t": hist.iloc[-1], "raw_t_minus_1": hist.iloc[-2],
                     "hand_computed": hand, "panel_value": panel.loc[d, "ds"],
                     "abs_diff": abs(hand - panel.loc[d, "ds"]),
                     "agrees": "YES" if abs(hand - panel.loc[d, "ds"]) < 1e-12 else "CHECK"})
    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "reproduction_check.csv", index=False)
    return df


# ---------------------------------------------------------------- F. DD-19
def date_shift_test() -> pd.DataFrame:
    """Move the signal +/-1 day and compare against the DD-19 rule.

    DD-19, declared before this ran: alignment is sound if |beta| at lag 0
    exceeds |beta| at BOTH shifts by at least a factor of 2, and the shifted
    coefficients are individually insignificant at 5% (|t| < 1.96).
    A shift that rivals lag 0 means the data is misaligned by a day.
    """
    rows = []
    for pair in FZ.PAIR_NAMES:
        panel = pd.read_csv(FZ.ANALYTIC / f"panel_{pair}.csv",
                            index_col="Date", parse_dates=["Date"])
        for shift in (-1, 0, 1):
            dc = panel["dc"].shift(shift)
            beta, t, n = _ols(panel["ds"], pd.DataFrame(
                {"dc": dc, "d_dollar": panel["d_dollar"],
                 "bcom_perp": panel["bcom_perp"]}))
            rows.append({"pair": pair, "shift": shift, "n": n,
                         "beta": round(beta, 4) if beta == beta else None,
                         "t_stat": round(t, 2) if t == t else None})
    df = pd.DataFrame(rows)

    verdicts = []
    for pair, g in df.groupby("pair"):
        b = {int(r.shift): (r.beta, r.t_stat) for r in g.itertuples()}
        b0 = abs(b[0][0]) if b[0][0] is not None else np.nan
        ok = all(b[s][0] is not None and abs(b[s][0]) * 2 <= b0
                 and abs(b[s][1]) < 1.96 for s in (-1, 1))
        verdicts.append({"pair": pair, "beta_lag0": b[0][0],
                         "beta_shift_minus1": b[-1][0], "beta_shift_plus1": b[1][0],
                         "t_minus1": b[-1][1], "t_plus1": b[1][1],
                         "dd19_rule": "|b0| >= 2*|b_shift| and |t_shift| < 1.96 both sides",
                         "verdict": "PASS" if ok else "REVIEW"})
    out = pd.DataFrame(verdicts)
    df.to_csv(DIAG / "date_shift_test.csv", index=False)
    out.to_csv(DIAG / "date_shift_verdict.csv", index=False)
    return out


def main() -> None:
    banner("06_descriptive_diagnostics",
           ["data/analytic/panel_<PAIR>.csv", "data/interim/*.csv"],
           ["outputs/diagnostics/{timing_gaps,iron_beta_by_day,hand_checks,"
            "reproduction_check,date_shift_test}.csv",
            "outputs/diagnostics/sign_convention_example.md"])

    print("\n  A. timing gaps (DD-18)")
    tg = timing_gaps()
    for _, r in tg.iterrows():
        mark = "" if r.verified == "exchange_spec" else "  [UNVERIFIED]"
        print(f"    {r.pair}  commodity settles {r.modal_gap_hours:>5.2f}h before the FX snap"
              f"   range {r.min_gap_hours}-{r.max_gap_hours}h"
              f"   {r.pct_days_off_mode}% of days off-mode{mark}")

    print("\n  B. iron ore beta by day of contract month (DD-12 falsification)")
    ib = iron_beta_by_day()
    for _, r in ib.iterrows():
        print(f"    {r.bucket:<12} n={r.n:>4}  w={r.mean_w:4.2f}  "
              f"beta={r.beta}  t={r.t_stat}  beta*w={r.implied_beta_times_w}")

    d = sign_convention_example()
    print(f"\n  C. sign-convention worked example -> sign_convention_example.md ({d})")

    hc = hand_checks()
    print(f"\n  D. ten hand checks: "
          f"{(hc.agrees == 'YES').sum()} agree, "
          f"{(hc.agrees.str.startswith('n/a')).sum()} excluded by design, "
          f"{(hc.agrees == 'CHECK').sum()} to review")

    rc = reproduction_check()
    print(f"  E. reproduction (seed {FZ.SEED}): "
          f"{(rc.agrees == 'YES').sum()}/{len(rc)} reproduce exactly")

    print("\n  F. date-shift test (DD-19)")
    ds = date_shift_test()
    for _, r in ds.iterrows():
        print(f"    {r.pair}  lag0 {r.beta_lag0}   -1 {r.beta_shift_minus1} "
              f"(t {r.t_minus1})   +1 {r.beta_shift_plus1} (t {r.t_plus1})"
              f"   [{r.verdict}]")


if __name__ == "__main__":
    main()
