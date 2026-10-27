"""08b_rf_dsr - the brief's secondary robustness method: a walk-forward random
forest for the predictive direction against a random walk, plus a deflated
Sharpe ratio.

The brief names this as a robustness method. The frozen specification is silent
on it, which is an omission rather than an exclusion, so it runs here - as
robustness, never as a replacement for the primary model (guide: "Treat this as
robustness, not as a replacement").

Rules, all fixed before the first fit:

  Features       dc_t, d_dollar_t, bcom_perp_t and their first lags, plus the
                 squares of dc_t - a linear model cannot use the squares, so
                 they are the forest's chance to find something OLS cannot.
  Hyperparameters  FIXED, NOT TUNED: 300 trees, max_depth 4, min_samples_leaf 50.
                 Shallow and heavily regularised because the signal, if any, is
                 tiny relative to noise. No tuning means no tuning leakage, and
                 N_TRIALS below stays honest.
  Window         expanding, first origin at the sample midpoint - the same
                 origin as the frozen Clark-West exercise (D1), so the forest
                 and the random walk are compared on IDENTICAL test dates.
  Refit          every 42 trading days (~2 months). Refitting daily over ~1,900
                 origins across 14 specifications is not affordable and buys
                 nothing at this signal-to-noise; the schedule is declared here,
                 fixed before the first fit, and is a computational choice that
                 touches no part of the estimand. Between refits the model is
                 held fixed and applied to each new origin, which is exactly
                 what a practitioner refitting bi-monthly would do.
  Scaling        fitted inside the training window only, at every refit.
  Embargo        h observations between train and test, so a label that spans
                 the boundary cannot leak.
  Benchmark      random walk, forecast = 0, on the same dates.

Failed folds are preserved and counted, per the guide.

Outputs
  outputs/tables/results_rf_dsr.csv
  outputs/models/rf_forecasts.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor

from _common import load, banner

FZ = load("00_design_freeze")
E = load("07_primary_estimation")

SEED = FZ.SEED
REFIT_EVERY = 42
EMBARGO = None            # set per horizon = h
RF_KW = dict(n_estimators=300, max_depth=4, min_samples_leaf=50,
             random_state=SEED, n_jobs=-1)
EULER = 0.5772156649015329


def features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature matrix. Everything is dated t; nothing looks ahead."""
    X = pd.DataFrame(index=df.index)
    for c in E.X_COLS:
        X[c] = df[c]
        X[f"{c}_lag1"] = df[c].shift(1)
    X["dc_sq"] = df["dc"] ** 2
    X["dc_abs"] = df["dc"].abs()
    return X


def walk_forward(df: pd.DataFrame, h: int) -> tuple[pd.DataFrame, int]:
    """Expanding-window RF forecasts of ds_{t+h}. Returns forecasts and fold failures."""
    y = df[E.Y_COL[h]]
    X = features(df)
    ok = X.notna().all(axis=1) & y.notna()
    X, y = X[ok], y[ok]
    if len(X) < 400:
        return pd.DataFrame(), 0

    start = len(X) // 2                      # same first origin as Clark-West
    parts, failures = [], 0
    for blk in range(start, len(X), REFIT_EVERY):
        tr = slice(0, max(0, blk - h))       # embargo: drop the h labels spanning blk
        Xtr, ytr = X.iloc[tr], y.iloc[tr]
        if len(Xtr) < 100:
            failures += 1
            continue
        mu, sd = Xtr.mean(), Xtr.std().replace(0, 1)        # fitted in-sample only
        try:
            model = RandomForestRegressor(**RF_KW).fit((Xtr - mu) / sd, ytr)
        except Exception:
            failures += 1
            continue
        # the block this model is responsible for, scored in one call
        te = slice(blk, min(blk + REFIT_EVERY, len(X)))
        Xte = X.iloc[te]
        parts.append(pd.DataFrame({"actual": y.iloc[te].to_numpy(),
                                   "rf": model.predict(((Xte - mu) / sd).to_numpy()),
                                   "rw": 0.0}, index=Xte.index))
    if not parts:
        return pd.DataFrame(), failures
    out = pd.concat(parts)
    out.index.name = "date"
    return out, failures


def oos_stats(fc: pd.DataFrame) -> dict:
    """OOS R2 against the random walk, and a Diebold-Mariano-style comparison.

    DM is legitimate HERE and not for the frozen OLS: the forest does not nest
    the random walk, so DM's non-nested assumption holds (D1 rejects DM only for
    the nested linear model).
    """
    e_rf = fc["actual"] - fc["rf"]
    e_rw = fc["actual"] - fc["rw"]
    d = e_rw ** 2 - e_rf ** 2
    L = E.nw_lags(len(d))
    v = E.long_run_cov(d.to_numpy() - d.mean(), L)[0, 0] / len(d)
    dm = d.mean() / np.sqrt(v) if v > 0 else np.nan
    return {"n_oos": len(fc),
            "oos_r2_vs_rw": 1 - (e_rf ** 2).sum() / (e_rw ** 2).sum(),
            "mspe_rf": (e_rf ** 2).mean(), "mspe_rw": (e_rw ** 2).mean(),
            "dm_stat": dm, "dm_p": 2 * stats.norm.sf(abs(dm)) if dm == dm else np.nan}


def deflated_sharpe(r: pd.Series, n_trials: int) -> dict:
    """Bailey & Lopez de Prado deflated Sharpe ratio.

    The strategy is the sign of the forecast times the realised return - the
    simplest way to turn a forecast into a track record. DSR asks whether the
    observed Sharpe beats what the BEST of n_trials independent strategies would
    produce under a true null, correcting for skew, kurtosis and selection.
    """
    T = len(r)
    sr = r.mean() / r.std() if r.std() > 0 else np.nan
    if not np.isfinite(sr) or T < 30:
        return {"sharpe": np.nan, "sr0": np.nan, "dsr": np.nan, "n_trials": n_trials}
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    # expected maximum Sharpe of n_trials draws under the null, in the same units
    e = np.e
    sr0 = np.sqrt(1 / T) * ((1 - EULER) * stats.norm.ppf(1 - 1 / n_trials)
                            + EULER * stats.norm.ppf(1 - 1 / (n_trials * e)))
    den = np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    dsr = stats.norm.cdf((sr - sr0) * np.sqrt(T - 1) / den) if den > 0 else np.nan
    return {"sharpe": sr * np.sqrt(252), "sharpe_per_obs": sr,
            "sr0_per_obs": sr0, "dsr": dsr, "n_trials": n_trials,
            "skew": g3, "kurtosis": g4}


def main() -> None:
    banner("08b_rf_dsr", ["data/analytic/panel_<PAIR>.csv"],
           ["outputs/tables/results_rf_dsr.csv", "outputs/models/rf_forecasts.csv"])

    samples = [(s, t, df) for s, t, role, df in E.samples() if s != "POOLED"]
    horizons = [FZ.H_PRIMARY, FZ.H_SECONDARY]
    n_trials = len(samples) * len(horizons)      # every strategy evaluated, declared

    rows, allfc = [], []
    print(f"\n  fixed hyperparameters, no tuning: {RF_KW}")
    print(f"  refit every {REFIT_EVERY} obs, embargo = h, first origin at the midpoint")
    print(f"  n_trials for the DSR = {n_trials} (every strategy run here)\n")

    for sample, treatment, df in samples:
        for h in horizons:
            fc, failures = walk_forward(df, h)
            if fc.empty:
                rows.append({"spec_id": f"{sample}.{treatment}.h{h}.rf",
                             "sample": sample, "treatment": treatment, "h": h,
                             "status": "not estimable: fewer than 400 usable rows",
                             "folds_failed": failures})
                print(f"    {sample}.{treatment} h={h}: not estimable")
                continue
            st = oos_stats(fc)
            strat = np.sign(fc["rf"]) * fc["actual"]
            ds = deflated_sharpe(strat, n_trials)
            rows.append({"spec_id": f"{sample}.{treatment}.h{h}.rf",
                         "sample": sample, "treatment": treatment, "h": h,
                         "status": "ok", "folds_failed": failures, **st, **ds})
            allfc.append(fc.assign(spec_id=f"{sample}.{treatment}.h{h}.rf"))
            print(f"    {sample}.{treatment:<9} h={h}  OOS R2 {st['oos_r2_vs_rw']:+.4%}"
                  f"  DM {st['dm_stat']:+.2f} (p {st['dm_p']:.3f})"
                  f"  Sharpe {ds['sharpe']:+.2f}  DSR {ds['dsr']:.3f}"
                  f"  n {st['n_oos']}" + (f"  [{failures} folds failed]" if failures else ""))

    res = pd.DataFrame(rows)
    res.to_csv(FZ.OUTPUTS / "tables" / "results_rf_dsr.csv", index=False)
    if allfc:
        pd.concat(allfc).to_csv(FZ.OUTPUTS / "models" / "rf_forecasts.csv",
                                index_label="date")

    beat = res[(res.get("oos_r2_vs_rw", pd.Series(dtype=float)) > 0)]
    print(f"\n  specifications beating the random walk out of sample: "
          f"{len(beat)} of {len(res)}")
    sig = res[res.get("dsr", pd.Series(dtype=float)) > 0.95]
    print(f"  deflated Sharpe above 0.95: {len(sig)} of {len(res)}")
    print(f"  total folds failed: {int(res['folds_failed'].sum())}")


if __name__ == "__main__":
    main()
