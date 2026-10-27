"""08_robustness - the prespecified alternatives, placebos and alignment checks.

Prespecified checks only, each tied to the decision that declared it. Every check
re-runs the 07 estimator with ONE input changed and reports the 07 baseline beta
beside it. Checks that cannot run stay in the table with the reason.

  D3   dollar control: Fed broad index vs ICE DXY, on their common sample
  O1   CAD: DXY rebuilt without CAD, vs DXY on the same sample
  D2   CLP: BCOM-perp recomputed against LME copper instead of HG1
  D2   NOK: pre-2022 subsample (gas revenue rivals oil afterwards)
  D4   CLP: long-span returns retained, with a span control
  D4   NOK: the four indeterminate-roll Brent observations retained
  D6   placebo: USDCHF on each commodity (h = 0)
  D6   influence: drop 2020 H1; drop the largest |dc| observation
  D6   date shift, option 3: Wald test that lag 0 dominates each +/-1 shift

Outputs
  outputs/tables/results_robustness.csv     same schema as results_primary.csv
  outputs/diagnostics/date_shift_wald.csv
  outputs/diagnostics/bug_gate_robustness.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import load, banner

FZ = load("00_design_freeze")
E = load("07_primary_estimation")
S03 = load("03_build_events_or_signals")      # return and roll rules, reused as written
S04 = load("04_build_outcomes")
import data_compile as DC  # noqa: E402

BASE = {"AUD": "first8", "CAD": "baseline", "CLP": "baseline", "NOK": "baseline"}
SPAN_CONTROL = {0: "span", 1: "span_lead1"}    # span of the dependent-variable return
COLUMNS = ["spec_id", "check", "ref", "status", "sample", "treatment", "h",
           "baseline_estimate", "n", "start", "end", "estimate", "se", "ci_lo", "ci_hi",
           "stat", "p", "units", "sd_dc_pct", "effect_pct", "effect_ci_lo_pct", "effect_ci_hi_pct",
           "mde_estimate", "mde_pct", "r2_total", "r2_partial", "mde_r2_partial", "inference"]


def read_interim(name: str) -> pd.DataFrame:
    df = pd.read_csv(FZ.INTERIM / f"{name}.csv", index_col="Date")
    df.index = pd.to_datetime(df.index, format=E.ISO)
    return df


SIG, OUT = read_interim("signals"), read_interim("outcomes")
PANELS = {p: E.read_panel(p) for p in BASE}


# ---------------------------------------------------------------- rebuilt inputs
def bcom_perp_on(x: pd.Series) -> pd.Series:
    """BCOM return net of its full-sample loading on x - 03's first stage, re-run."""
    d = pd.concat([SIG["BCOM_lret"], x.rename("x")], axis=1).dropna()
    slope, intercept = np.polyfit(d["x"], d["BCOM_lret"], 1)
    return SIG["BCOM_lret"] - (intercept + slope * x)


def rejoin(pair: str, dc: pd.Series, bcom_perp: pd.Series,
           keep_long_span: bool = False) -> pd.DataFrame:
    """One pair's panel rebuilt as 05 builds it, for checks that swap an input 05 fixed.

    The h=1 target is the next return on the currency's own calendar, as in 05.
    """
    stem = FZ.PAIRS[pair]["fx"].replace("_PX_LAST", "")
    own = OUT.loc[OUT[f"{stem}_ds"].notna()]
    ds = own[f"{stem}_ds"]
    if not keep_long_span:
        ds = ds.mask(own[f"{stem}_long_span"])
    span = own[f"{stem}_span_days"]
    df = pd.DataFrame({"ds": ds, "dc": dc, "d_dollar": OUT["d_dollar"], "bcom_perp": bcom_perp,
                       "span": span, "ds_lead1": ds.shift(-1), "span_lead1": span.shift(-1)})
    df = df.dropna(subset=["ds", *E.X_COLS])
    return df[df.index >= pd.Timestamp(FZ.PAIRS[pair]["start"])].assign(pair=pair)


def dxy_ex_cad() -> pd.Series:
    """O1: log change of DXY without CAD, from the AT-04 components, weights renormalised."""
    spec = FZ.CFG["controls"]["dollar_cad_excluded"]
    px = pd.concat([DC._fx_csv_pair(c) for c in spec["weights_full"]], axis=1).dropna()
    w = pd.Series(spec["weights_full"]).add_suffix("_PX_LAST") / spec["weight_sum_available"]
    return (np.log(px / px.shift()) * w).sum(axis=1, min_count=len(w))


def self_checks() -> None:
    """The rebuilt inputs must reproduce 03 and 05 exactly before they are trusted."""
    perp = bcom_perp_on(SIG["HG1_lret"])
    assert np.allclose(perp.dropna(), SIG["BCOM_perp_CLP"].dropna()), "bcom_perp_on != 03"
    for pair, comm in (("CLP", "COPPER"), ("NOK", "BRENT")):
        df = rejoin(pair, SIG[f"{comm}_lret"], SIG[f"BCOM_perp_{pair}"])
        assert df.index.equals(PANELS[pair].index), f"rejoin({pair}) != 05 panel"
        assert np.allclose(df["ds_lead1"], PANELS[pair]["ds_lead1"], equal_nan=True)


# ---------------------------------------------------------------- checks
def checks():
    """Yield (id, description, decision, sample, frame, regressors, horizons)."""
    X, H = E.X_COLS, (0, 1)

    # D3: Fed broad dollar vs DXY - a horse race, so both on the common sample (D6)
    for p in ("CAD", "CLP", "NOK"):
        com = PANELS[p].dropna(subset=["d_dollar_broad"])
        yield "dxy_common", "ICE DXY, on the Fed-index sample", "D3, D6", p, com, X, H
        yield "fed_broad", "Fed H.10 broad dollar instead of DXY", "D3", p, \
            com.assign(d_dollar=com["d_dollar_broad"]), X, H

    # O1: CAD is a 9.1% DXY constituent
    excad = dxy_ex_cad()
    com = PANELS["CAD"].assign(d_excad=excad).dropna(subset=["d_excad"])
    print(f"  O1 DXY ex-CAD vs DXY: corr {com['d_excad'].corr(com['d_dollar']):.3f}, "
          f"n {len(com)} of {len(PANELS['CAD'])}")
    yield "dxy_common_o1", "ICE DXY, on the ex-CAD sample", "O1, D6", "CAD", com, X, H
    yield "dxy_ex_cad", "DXY rebuilt without CAD (86.7% of the non-CAD basket)", "O1", "CAD", \
        com.assign(d_dollar=com["d_excad"]), X, H

    # D2: HG1 rolls are invisible, so recompute BCOM-perp on roll-free LME copper
    yield "bcom_perp_lme", "BCOM-perp orthogonalized on LME, not HG1", "D2", "CLP", \
        PANELS["CLP"].assign(bcom_perp=bcom_perp_on(SIG["COPPER_lret"])), X, H

    # D2: Brent stops tracking Norwegian export revenue once gas rivals oil
    yield "pre_2022", "sample ends 2021-12-31", "D2", "NOK", \
        PANELS["NOK"].loc[:"2021-12-31"], X, H

    # D4: with/without each consequential exclusion
    clp = rejoin("CLP", SIG["COPPER_lret"], SIG["BCOM_perp_CLP"], keep_long_span=True)
    for h in H:
        yield "long_span_kept", "long-span returns retained, span control", "D4", "CLP", \
            clp, [*X, SPAN_CONTROL[h]], (h,)

    px = DC.comm_df["BRENT_PX_LAST"].astype(float)
    lret, _, _ = S03._log_returns(px)
    roll, _ = S03._roll_flags(DC.comm_df["BRENT_FUT_CUR_GEN_TICKER"], px)
    brent = lret.where(~roll)                      # indeterminate days kept as no-roll
    yield "brent_indet_kept", "indeterminate-roll Brent observations retained", "D4", "NOK", \
        rejoin("NOK", brent, bcom_perp_on(brent)), X, H

    # D6: placebo - Switzerland exports none of the four commodities
    chf, _ = S04._fx_returns(DC._fx_csv_pair("USDCHF")["USDCHF_PX_LAST"].astype(float), invert=True)
    for p, df in PANELS.items():
        yield "placebo_chf", "USDCHF as the outcome", "D6", p, df.assign(ds=chf), X, (0,)

    # D6: influence
    for p, df in PANELS.items():
        yield "drop_2020h1", "2020-01-01 to 2020-06-30 dropped", "D6", p, \
            df.drop(df.loc["2020-01-01":"2020-06-30"].index), X, H
        yield "drop_largest", "largest |dc| observation dropped", "D6", p, \
            df.drop(df["dc"].abs().idxmax()), X, H


def not_run() -> list[dict]:
    """Prespecified or required checks that cannot run - kept, with the reason."""
    no_brent = pd.isna(SIG["BRENT_lret"].get(pd.Timestamp("2010-01-04")))
    rows = [
        ("wti_neg_kept", "WTI 2020-04-20/21 retained", "D4", "CAD",
         "not estimable: a log return is undefined at a negative price; D4 rejects simple returns"),
        ("nok_0101_kept", "USDNOK 2010-01-01 retained", "D4", "NOK",
         "no effect: it changes only the 2010-01-04 USDNOK return, and no Brent return exists that day"
         if no_brent else "CHECK: a Brent return exists on 2010-01-04 - run this"),
        ("at03_wti", "WTI from AT-03 instead of the golden source", "D3", "CAD",
         "not run: AT-03 is not on this machine and the API is suspended"),
        ("aud_zero_returns", "AUD zero-return-share diagnostic", "D4", "AUD",
         "not run: D4's trigger ('if AUD proves unstable at the sample start') has no operational rule"),
        ("rf_dsr", "walk-forward random forest vs random walk, DSR", "brief", "all",
         "not run: in the brief's robustness method but not in the frozen specification - "
         "needs a supervisor decision"),
    ]
    return [{"spec_id": f"{s}.{i}", "treatment": i, "check": c, "ref": r, "sample": s, "status": st}
            for i, c, r, s, st in rows]


def run_checks() -> pd.DataFrame:
    primary = pd.read_csv(FZ.OUTPUTS / "tables" / "results_primary.csv").set_index("spec_id")
    rows = []
    for cid, desc, ref, sample, df, x, horizons in checks():
        for h in horizons:
            y = E.Y_COL[h]
            res, _ = E.fit(df, y, x)
            rows.append({"spec_id": f"{sample}.{cid}.h{h}.ols", "check": desc, "ref": ref,
                         "status": "run", "sample": sample, "treatment": cid, "h": h,
                         "baseline_estimate": primary.loc[f"{sample}.{BASE[sample]}.h{h}.ols",
                                                          "estimate"], **res})
    return (pd.DataFrame(rows + not_run()).reindex(columns=COLUMNS)
            .astype({"h": "Int64", "n": "Int64"}))


# ---------------------------------------------------------------- D6 date shift
def date_shift_wald() -> pd.DataFrame:
    """D6 option 3: does the lag-0 coefficient dominate each one-day shift?

    The signal is shifted on the commodity's own trading calendar (amendment
    rule 8): s = -1 puts dc_{t+1} against ds_t, s = +1 puts dc_{t-1}. beta_0 and
    beta_s come from separate regressions on one common sample; their covariance
    is the Newey-West long-run covariance of the two estimators' influence
    functions (X'X)^-1 x_t e_t. A side passes if beta_0 - beta_s is significantly
    positive (one-sided 5%) and |beta_s| < |beta_0|; a pair passes if both do.
    """
    rows = []
    for pair, df in PANELS.items():
        com = FZ.PAIRS[pair]["commodity"]
        own = SIG[f"{com.replace('_PX_LAST', '')}_lret"].reindex(
            DC.comm_df.index[DC.comm_df[com].notna()])
        d = df.assign(**{f"dc_s{s}": own.shift(s).reindex(df.index) for s in (-1, 1)})
        d = d.dropna(subset=["dc_s-1", "dc_s1"])
        beta, infl = {}, {}
        for s, col in ((0, "dc"), (-1, "dc_s-1"), (1, "dc_s1")):
            X = np.column_stack([np.ones(len(d)), d[[col, "d_dollar", "bcom_perp"]]])
            B = np.linalg.inv(X.T @ X)
            b = B @ X.T @ d["ds"].to_numpy()
            e = d["ds"].to_numpy() - X @ b
            beta[s], infl[s] = b[1], (X * e[:, None]) @ B[:, 1]
        L = E.nw_lags(len(d))
        for s in (-1, 1):
            C = E.long_run_cov(np.column_stack([infl[0], infl[s]]), L)
            diff, se = beta[0] - beta[s], np.sqrt(C[0, 0] + C[1, 1] - 2 * C[0, 1])
            p = E.NORMAL.sf(diff / se)
            rows.append({"pair": pair, "shift": s,
                         "signal": "dc_{t+1}" if s == -1 else "dc_{t-1}", "n": len(d),
                         "beta_0": beta[0], "se_0": np.sqrt(C[0, 0]),
                         "beta_shift": beta[s], "se_shift": np.sqrt(C[1, 1]),
                         "diff": diff, "se_diff": se, "z": diff / se, "p_one_sided": p,
                         "magnitude_ok": abs(beta[s]) < abs(beta[0]),
                         "side_pass": bool(p < FZ.ALPHA and abs(beta[s]) < abs(beta[0])),
                         "inference": f"Newey-West L={L}, influence-function covariance"})
    out = pd.DataFrame(rows)
    out["verdict"] = out.groupby("pair")["side_pass"].transform("all").map(
        {True: "PASS", False: "FAIL"})
    return out


def main() -> None:
    banner("08_robustness", ["data/analytic/panel_<PAIR>.csv", "data/interim/*.csv",
                             "outputs/tables/results_primary.csv"],
           ["outputs/tables/results_robustness.csv", "outputs/diagnostics/date_shift_wald.csv"])
    self_checks()
    print("  self-checks: rebuilt inputs reproduce 03 and 05 exactly\n")

    res = run_checks()
    E.enforce_gate(res[res["status"] == "run"].assign(test="ols"),
                   E.DIAG / "bug_gate_robustness.csv")
    res.to_csv(E.TABLES / "results_robustness.csv", index=False)

    print("\n  check                  sample  h   beta (baseline)        p      n")
    for r in res.itertuples():
        if r.status != "run":
            print(f"  {r.treatment:<22} {r.sample:<6}  -   {r.status}")
            continue
        print(f"  {r.treatment:<22} {r.sample:<6}  {r.h}  {r.estimate:+.4f} ({r.baseline_estimate:+.4f})"
              f"   {r.p:.3f}  {r.n:>5}")

    ds = date_shift_wald()
    ds.to_csv(E.DIAG / "date_shift_wald.csv", index=False)
    print("\n  D6 date shift (option 3): beta_0 - beta_shift > 0, one-sided 5%")
    for r in ds.itertuples():
        print(f"    {r.pair}  {r.signal:<9} b0 {r.beta_0:+.4f}  b_shift {r.beta_shift:+.4f}"
              f"  diff {r.diff:+.4f} (se {r.se_diff:.4f})  p {r.p_one_sided:.3f}"
              f"  |b_s|<|b0| {r.magnitude_ok}   [{r.verdict}]")


if __name__ == "__main__":
    main()
