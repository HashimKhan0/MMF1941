"""07_primary_estimation - the frozen specification, estimated once.

    ds_{t+h} = a + b*dc_t + g*d_dollar_t + d*bcom_perp_t + e,     h = 0, 1, 5

Samples (D7):
  CAD, CLP, NOK  per-pair OLS, Newey-West HAC. h=0 and h=1 are the six tests in
                 the Holm family; h=5 is the prespecified secondary horizon.
  POOLED         CAD + CLP + NOK, pair fixed effects, Driscoll-Kraay errors
                 (D1 amended 2026-10-26); the frozen two-way result is also
                 reported, same coefficient, different standard error
                 and pair.
  AUD            methodological case study - never pooled, never in the Holm
                 family. Four treatments side by side: first8 (the DD-12
                 baseline), first5, full, rescaled (dc / w).

Out of sample (h = 1, 5): expanding-window Clark-West against the zero-return
random walk. Not Diebold-Mariano: the model nests the benchmark (DD-11).

Every rule applied here that the freeze left unstated - HAC bandwidth, pooled
critical values, MDE, bug-gate R2, CW window - was fixed in design_decisions.md
(Amendments, 2026-10-26) before this file existed.

Outputs
  outputs/tables/results_primary.csv   the one machine-readable results table
  outputs/models/coefficients.csv      every coefficient, controls included
  outputs/models/oos_forecasts.csv     one row per forecast origin (D6)
  outputs/models/run_record.json       code, config and environment behind it
  outputs/diagnostics/bug_gate.csv     the D6 catastrophe gate, pass or fail
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import scipy
from scipy import stats

from _common import load, banner

FZ = load("00_design_freeze")

TABLES, MODELS, DIAG = (FZ.OUTPUTS / d for d in ("tables", "models", "diagnostics"))
for _p in (TABLES, MODELS):
    _p.mkdir(parents=True, exist_ok=True)

X_COLS = ["dc", "d_dollar", "bcom_perp"]       # beta is always the coefficient on x[0]
Y_COL = {0: "ds", 1: "ds_lead1", 5: "ds_lead5"}
ISO = "%Y-%m-%d"
NORMAL = stats.norm()

COLUMNS = ["spec_id", "sample", "treatment", "role", "h", "test",
           "n", "entities", "start", "end",
           "estimate", "se", "ci_lo", "ci_hi", "stat", "p", "p_holm",
           "units", "sd_dc_pct", "effect_pct", "effect_ci_lo_pct", "effect_ci_hi_pct",
           "mde_estimate", "mde_pct", "r2_total", "r2_partial", "mde_r2_partial",
           "oos_r2_pct", "mae_ratio", "inference"]


# ---------------------------------------------------------------- data
def read_panel(name: str) -> pd.DataFrame:
    """A 05 panel, with dates parsed to a declared format (never inferred)."""
    df = pd.read_csv(FZ.ANALYTIC / f"panel_{name}.csv", index_col="Date")
    df.index = pd.to_datetime(df.index, format=ISO)
    for h in (FZ.H_PRIMARY, FZ.H_SECONDARY):
        df[f"ds_lead{h}_date"] = pd.to_datetime(df[f"ds_lead{h}_date"], format=ISO)
    return df


def samples() -> list[tuple[str, str, str, pd.DataFrame]]:
    """(sample, treatment, role, panel) for every specification estimated here."""
    out = [(p, "baseline", "primary", read_panel(p)) for p in ("CAD", "CLP", "NOK")]
    out.append(("POOLED", "baseline", "pooled", pd.concat(df for *_, df in out)))
    aud, full = read_panel("AUD"), read_panel("AUD_full")
    out += [("AUD", "first8", "case_study", aud),
            ("AUD", "first5", "case_study", aud[aud["IRON_k"] <= FZ.IRON_ROBUST_DAYS]),
            ("AUD", "full", "case_study", full),
            ("AUD", "rescaled", "case_study", full.assign(dc=full["IRON_lret_rescaled"]))]
    return out


# ---------------------------------------------------------------- variance
def nw_lags(T: int) -> int:
    """Newey-West (1994) rule of thumb, L = floor(4 (T/100)^(2/9)) - amendment rule 1."""
    return int(4 * (T / 100) ** (2 / 9))


def long_run_cov(u: np.ndarray, lags: int) -> np.ndarray:
    """Bartlett-weighted sum of the autocovariances of the rows of u."""
    u = u.reshape(len(u), -1)
    S = u.T @ u
    for lag in range(1, lags + 1):
        G = u[lag:].T @ u[:-lag]
        S += (1 - lag / (lags + 1)) * (G + G.T)
    return S


def cluster_cov(u: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Sum over clusters of the outer product of within-cluster score sums, x G/(G-1)."""
    s = pd.DataFrame(u).groupby(groups).sum().to_numpy()
    return len(s) / (len(s) - 1) * s.T @ s


# ---------------------------------------------------------------- estimators
def driscoll_kraay(u: np.ndarray, dates: np.ndarray) -> np.ndarray:
    """Driscoll-Kraay meat: Newey-West on the cross-sectionally summed scores.

    Sums the per-observation scores within each date, then takes the Bartlett
    long-run covariance of that time series. Asymptotics are T -> infinity with
    N fixed, which is this panel's regime (3 pairs, ~3,700 dates) - unlike
    two-way clustering, which needs the cluster count in EACH dimension to grow
    and has only 3 in the pair dimension. D1, amended 2026-10-26.
    """
    h = pd.DataFrame(u).groupby(dates).sum().to_numpy()
    return long_run_cov(h, nw_lags(len(h)))


def fit(df: pd.DataFrame, y: str, x: list[str] = X_COLS, pooled: bool = False,
        pooled_estimator: str | None = None) -> tuple[dict, pd.DataFrame]:
    """OLS of y on x; x[0] is the commodity return, the coefficient of interest.

    Per pair: intercept, Newey-West HAC, normal reference distribution.
    Pooled:   pair fixed effects absorbed by demeaning within pair (identical
              slopes, by FWL). Default errors are Driscoll-Kraay with a normal
              reference (D1 as amended 2026-10-26); pass
              pooled_estimator="two_way_cluster" for the frozen alternative,
              which is still reported. r2_total is then the within R2.
    """
    d = df.dropna(subset=[y, *x])
    pairs = d["pair"].to_numpy()
    if pooled:
        v = d[[y, *x]] - d.groupby("pair")[[y, *x]].transform("mean")
        X, Y, terms = v[x].to_numpy(), v[y].to_numpy(), list(x)
    else:
        X = np.column_stack([d[x].to_numpy(), np.ones(len(d))])
        Y, terms = d[y].to_numpy(), [*x, "const"]

    B = np.linalg.inv(X.T @ X)
    b = B @ X.T @ Y
    e = Y - X @ b
    u = X * e[:, None]                                    # per-observation scores

    if pooled:
        dates = d.index.to_numpy()
        est = pooled_estimator or FZ.INF["pooled"]
        if est == "two_way_cluster":
            meat = (cluster_cov(u, dates) + cluster_cov(u, pairs)
                    - cluster_cov(u, np.arange(len(d))))
            G = min(len(set(dates)), len(set(pairs)))
            ref = stats.t(G - 1)
            how = f"two-way cluster date x pair, G={G}, t({G - 1})"
        else:
            meat = driscoll_kraay(u, dates)
            T = len(set(dates))
            ref = NORMAL
            how = (f"Driscoll-Kraay, Bartlett L={nw_lags(T)}, T={T}, "
                   f"N={len(set(pairs))}, normal")
    else:
        L = nw_lags(len(d))
        meat = long_run_cov(u, L)
        ref, how = NORMAL, f"Newey-West HAC, Bartlett, L={L}"
    V = B @ meat @ B
    w, Q = np.linalg.eigh(V)
    if w.min() < 0:                                       # CGM (2011): clip to PSD
        V, how = Q @ np.diag(w.clip(0)) @ Q.T, how + ", eigenvalues clipped"

    # partial R2 of dc for any slope bb: dc net of the controls (FWL), amendment rule 3
    Z = X[:, 1:]
    dc_perp = X[:, 0] - Z @ np.linalg.lstsq(Z, X[:, 0], rcond=None)[0]
    sxx, sse = dc_perp @ dc_perp, e @ e
    r2_partial = lambda bb: bb ** 2 * sxx / (bb ** 2 * sxx + sse)

    beta, se = b[0], np.sqrt(V[0, 0])
    crit = ref.ppf(1 - FZ.ALPHA / 2)
    mde = (crit + ref.ppf(FZ.POWER_TARGET)) * se
    sd = 100 * d[x[0]].std()                              # one SD of dc, in percent
    res = {"n": len(d), "entities": len(set(pairs)),
           "start": d.index.min().date(), "end": d.index.max().date(),
           "estimate": beta, "se": se, "ci_lo": beta - crit * se, "ci_hi": beta + crit * se,
           "stat": beta / se, "p": 2 * ref.sf(abs(beta / se)),
           "units": f"% FX return per 1-SD {x[0]}", "sd_dc_pct": sd,
           "effect_pct": beta * sd, "effect_ci_lo_pct": (beta - crit * se) * sd,
           "effect_ci_hi_pct": (beta + crit * se) * sd,
           "mde_estimate": mde, "mde_pct": mde * sd,
           "r2_total": 1 - sse / ((Y - Y.mean()) ** 2).sum(),
           "r2_partial": r2_partial(beta), "mde_r2_partial": r2_partial(mde),
           "inference": how}
    coef = pd.DataFrame({"term": terms, "coef": b, "se": np.sqrt(np.diag(V))})
    return res, coef


def clark_west(df: pd.DataFrame, h: int) -> tuple[dict, pd.DataFrame]:
    """Expanding-window forecasts of ds_{t+h} against the zero-return random walk.

    At each origin the model is refitted on rows whose target date is on or
    before the origin, so nothing unknown at the origin enters the fit. Targets
    are sorted, so that set is a prefix of the sample. Forecasts begin at the
    sample midpoint (amendment rule 5).

    Clark & West (2007): f = e_rw^2 - (e_m^2 - (yhat_rw - yhat_m)^2), yhat_rw = 0.
    One-sided: the model must beat the random walk. The CI is two-sided 95%.
    """
    y = Y_COL[h]
    d = df.dropna(subset=[y, *X_COLS])
    X = np.column_stack([np.ones(len(d)), d[X_COLS].to_numpy()])
    Y = d[y].to_numpy()
    origin, target = d.index.to_numpy(), d[f"{y}_date"].to_numpy()
    assert (np.diff(target) > np.timedelta64(0)).all(), "targets must be increasing"

    rows = []
    for i in range(int(len(d) * FZ.OOS_FIRST_ORIGIN), len(d)):
        k = np.searchsorted(target, origin[i], side="right")   # rows realised by origin i
        b = np.linalg.lstsq(X[:k], Y[:k], rcond=None)[0]
        rows.append({"origin": origin[i], "target_date": target[i], "train_end": origin[k - 1],
                     "n_train": k, "actual": Y[i], "forecast": X[i] @ b})
    fc = pd.DataFrame(rows)

    e_m = fc["actual"] - fc["forecast"]
    f = (fc["actual"] ** 2 - e_m ** 2 + fc["forecast"] ** 2).to_numpy()
    L = nw_lags(len(f))
    se = np.sqrt(long_run_cov(f - f.mean(), L)[0, 0]) / len(f)
    mspe_rw = 100 / (fc["actual"] ** 2).mean()            # scales MSPE to % of the RW's
    crit2 = NORMAL.ppf(1 - FZ.ALPHA / 2)
    mde = (NORMAL.ppf(1 - FZ.ALPHA) + NORMAL.ppf(FZ.POWER_TARGET)) * se
    res = {"n": len(f), "entities": 1,
           "start": fc["origin"].min().date(), "end": fc["origin"].max().date(),
           "estimate": f.mean(), "se": se,
           "ci_lo": f.mean() - crit2 * se, "ci_hi": f.mean() + crit2 * se,
           "stat": f.mean() / se, "p": NORMAL.sf(f.mean() / se),
           "units": "% of random-walk MSPE, CW-adjusted",
           "effect_pct": f.mean() * mspe_rw, "effect_ci_lo_pct": (f.mean() - crit2 * se) * mspe_rw,
           "effect_ci_hi_pct": (f.mean() + crit2 * se) * mspe_rw,
           "mde_estimate": mde, "mde_pct": mde * mspe_rw,
           "oos_r2_pct": 100 - (e_m ** 2).mean() * mspe_rw,
           "mae_ratio": e_m.abs().mean() / fc["actual"].abs().mean(),
           "inference": f"Clark-West, one-sided, Newey-West L={L}, first origin "
                        f"{fc['origin'].min().date()}"}
    return res, fc


def holm(p: pd.Series) -> pd.Series:
    """Holm (1979) step-down adjusted p-values."""
    s = p.sort_values()
    adj = (s * (len(s) - np.arange(len(s)))).cummax().clip(upper=1)
    return adj.reindex(p.index)


def bug_gate(res: pd.DataFrame) -> pd.DataFrame:
    """D6 catastrophe gate on every OLS row: |beta| > 0.5 or partial R2 of dc > 0.40."""
    ols = res[res["test"] != "clark_west"]
    return ols[["spec_id", "estimate", "r2_partial"]].assign(
        tripped=(ols["estimate"].abs() > FZ.BUG_ABS_BETA_MAX)
        | (ols["r2_partial"] > FZ.BUG_R2_MAX))


def enforce_gate(res: pd.DataFrame, path) -> None:
    """Write the gate; if it trips, say so and stop before any result is written."""
    gate = bug_gate(res)
    gate.to_csv(path, index=False)
    if gate["tripped"].any():
        print("\n  *** D6 BUG GATE TRIPPED - a sign or alignment bug, not a finding. ***")
        print(gate[gate["tripped"]].to_string(index=False))
        print(f"  No results written. Details: {path}")
        sys.exit(1)


# ---------------------------------------------------------------- run
def estimate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows, coefs, forecasts = [], [], []
    for sample, treatment, role, df in samples():
        for h in FZ.HORIZONS:
            r = "secondary" if role == "primary" and h == FZ.H_SECONDARY else role
            key = {"sample": sample, "treatment": treatment, "role": r, "h": h}

            spec = f"{sample}.{treatment}.h{h}.ols"
            res, coef = fit(df, Y_COL[h], pooled=sample == "POOLED")
            rows.append({"spec_id": spec, **key, "test": "ols", **res})
            coefs.append(coef.assign(spec_id=spec))

            # D1 amended: the frozen two-way estimator is still reported, as a
            # secondary row with the same coefficient and a different SE.
            if sample == "POOLED":
                alt = FZ.INF["pooled_also_reported"]
                spec_alt = f"{sample}.{treatment}.h{h}.ols_{alt}"
                res_alt, coef_alt = fit(df, Y_COL[h], pooled=True,
                                        pooled_estimator=alt)
                rows.append({"spec_id": spec_alt, **{**key, "role": "secondary"},
                             "test": "ols", **res_alt})
                coefs.append(coef_alt.assign(spec_id=spec_alt))

            if h > 0 and sample != "POOLED":
                spec = f"{sample}.{treatment}.h{h}.cw"
                res, fc = clark_west(df, h)
                rows.append({"spec_id": spec, **key, "test": "clark_west", **res})
                forecasts.append(fc.assign(spec_id=spec))

    res = pd.DataFrame(rows).reindex(columns=COLUMNS)
    family = (res["role"] == "primary") & (res["test"] == "ols")
    assert family.sum() == FZ.N_PRIMARY_TESTS, family.sum()
    res.loc[family, "p_holm"] = holm(res.loc[family, "p"])
    return res, pd.concat(coefs), pd.concat(forecasts)


def run_record() -> dict:
    """What produced these numbers: commit, uncommitted edits, hashes, versions."""
    git = lambda *a: subprocess.run(["git", *a], cwd=FZ.ROOT, capture_output=True,
                                    text=True).stdout
    files = ["config/project_config.yaml", "design_decisions.md", "data_compile.py",
             "src/05_merge_analysis_panel.py", "src/07_primary_estimation.py"]
    return {"run_at": datetime.now().isoformat(timespec="seconds"),
            "git_head": git("rev-parse", "HEAD").strip(),
            "uncommitted": git("status", "--porcelain", "--", *files).splitlines(),
            "sha256": {f: hashlib.sha256((FZ.ROOT / f).read_bytes()).hexdigest() for f in files},
            "python": platform.python_version(), "platform": platform.platform(),
            "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__}


def main() -> None:
    banner("07_primary_estimation", ["data/analytic/panel_<PAIR>.csv", "panel_AUD_full.csv"],
           ["outputs/tables/results_primary.csv", "outputs/models/*",
            "outputs/diagnostics/bug_gate.csv"])

    res, coefs, forecasts = estimate()
    enforce_gate(res, DIAG / "bug_gate.csv")

    res.to_csv(TABLES / "results_primary.csv", index=False)
    coefs.to_csv(MODELS / "coefficients.csv", index=False)
    forecasts.to_csv(MODELS / "oos_forecasts.csv", index=False)
    (MODELS / "run_record.json").write_text(json.dumps(run_record(), indent=2))

    print("\n  in-sample  (effect = % FX move per 1-SD commodity move;  MDE at 80% power)")
    for r in res[res["test"] == "ols"].itertuples():
        holm_p = "" if pd.isna(r.p_holm) else f"  holm {r.p_holm:.3f}"
        print(f"    {r.spec_id:<26} b={r.estimate:+.4f} ({r.se:.4f})  effect {r.effect_pct:+.3f}%"
              f"  p={r.p:.3f}{holm_p:<12}  R2p {100 * r.r2_partial:5.2f}%"
              f"  MDE R2p {100 * r.mde_r2_partial:4.2f}%  n={r.n}")
    print("\n  out-of-sample  (Clark-West vs random walk, one-sided)")
    for r in res[res["test"] == "clark_west"].itertuples():
        print(f"    {r.spec_id:<26} CW={r.stat:+.2f}  p={r.p:.3f}  OOS R2 {r.oos_r2_pct:+.2f}%"
              f"  MDE {r.mde_pct:.2f}% of RW MSPE  P={r.n}")
    print(f"\n  bug gate: passed on {int((res['test'] == 'ols').sum())} OLS rows")


if __name__ == "__main__":
    main()
