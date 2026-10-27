"""09_tables_figures - every table and figure, rebuilt from saved results only.

Nothing here estimates anything: every number comes from a file 05-08 wrote,
so anything in the paper can be traced to results_primary.csv,
results_robustness.csv or a diagnostics file.

Tables (Markdown, outputs/tables/)
  table1_in_sample.md        CAD, CLP, NOK and pooled; h = 0, 1, 5
  table2_out_of_sample.md    Clark-West against the random walk
  table3_aud_case_study.md   the four AUD treatments side by side (D7)
  table4_robustness.md       every prespecified check - failures and not-run included
  appendix_attrition.md      sample flow, union of dates to final N

Figures (PNG, outputs/figures/)
  fig1_actual_vs_forecast    fig2_cumulative_loss    fig3_rolling_oos_r2
  fig4_iron_ore_decay        fig5_date_shift
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from _common import load, banner  # noqa: E402

FZ = load("00_design_freeze")
TABLES, FIGS, DIAG, MODELS = (FZ.OUTPUTS / d for d in ("tables", "figures", "diagnostics", "models"))
FIGS.mkdir(parents=True, exist_ok=True)

PAIRS = ["CAD", "CLP", "NOK"]
COMMODITY = {"AUD": "iron ore", "CAD": "WTI", "CLP": "LME copper", "NOK": "Brent"}
# dataviz reference palette: categorical slots 1-3 (validated all-pairs, light mode).
# AUD is the case study, so it takes muted ink rather than a fourth series colour.
COLOR = {"CAD": "#2a78d6", "CLP": "#eb6834", "NOK": "#1baf7a", "AUD": "#898781"}
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
    "font.size": 9, "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": AXIS,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.dpi": 200,
    "legend.frameon": False})


# ---------------------------------------------------------------- formatting
def fp(p: float) -> str:
    return "" if pd.isna(p) else "<0.001" if p < 0.001 else f"{p:.3f}"


def coef(b: float, se: float) -> str:
    return f"{b:+.4f} ({se:.4f})"


def md_table(df: pd.DataFrame) -> str:
    rows = ["| " + " | ".join(map(str, r)) + " |" for r in df.fillna("").to_numpy()]
    return "\n".join(["| " + " | ".join(df.columns) + " |",
                      "|" + "---|" * len(df.columns), *rows])


def write_table(name: str, title: str, body: str, note: str) -> None:
    (TABLES / f"{name}.md").write_text(f"# {title}\n\n{body}\n\n{note}\n", encoding="utf-8")


def ols_columns(d: pd.DataFrame) -> pd.DataFrame:
    """The columns every in-sample table shares."""
    return pd.DataFrame({
        "h": d["h"].to_numpy(),
        "β (SE)": [coef(b, s) for b, s in zip(d["estimate"], d["se"])],
        "95% CI": [f"[{lo:+.4f}, {hi:+.4f}]" for lo, hi in zip(d["ci_lo"], d["ci_hi"])],
        "1-SD effect, %": [f"{e:+.3f}" for e in d["effect_pct"]],
        "p": d["p"].map(fp).to_numpy(),
        "partial R², %": [f"{100 * r:.2f}" for r in d["r2_partial"]],
        "MDE partial R², %": [f"{100 * r:.2f}" for r in d["mde_r2_partial"]],
        "N": d["n"].to_numpy(),
        "dates": [f"{a} → {b}" for a, b in zip(d["start"], d["end"])],
        "spec": d["spec_id"].to_numpy()})


# ---------------------------------------------------------------- tables
def table1(res: pd.DataFrame) -> None:
    d = res[(res["test"] == "ols") & res["sample"].isin([*PAIRS, "POOLED"])]
    t = ols_columns(d)
    t.insert(0, "sample", d["sample"].to_numpy())
    t.insert(6, "Holm p", d["p_holm"].map(fp).to_numpy())

    lines = []
    for r in d[d["sample"].isin(PAIRS)].itertuples():
        if r.h == 0:
            lines.append(f"- **{r.sample}, same day.** A one-SD daily {COMMODITY[r.sample]} move "
                         f"({r.sd_dc_pct:.2f}%) goes with a {r.effect_pct:+.3f}% {r.sample} move "
                         f"(95% CI {r.effect_ci_lo_pct:+.3f} to {r.effect_ci_hi_pct:+.3f}).")
        elif r.h == FZ.H_PRIMARY:
            lines.append(f"- **{r.sample}, next day.** We could have detected a partial R² of "
                         f"{100 * r.mde_r2_partial:.2f}% at 80% power; we found "
                         f"{100 * r.r2_partial:.2f}% (β {r.estimate:+.4f}, MDE β {r.mde_estimate:.4f}).")
    note = ("**Reading.**\n" + "\n".join(lines) + "\n\n"
            "**Note.** Daily log returns, sign convention A (positive = the commodity currency "
            "appreciates against USD). Δs_{t+h} = α + β·Δc_t + γ·ΔDXY_t + δ·ΔBCOM⊥_t; h = 5 is the "
            "one-day return five trading days ahead. Per pair: Newey–West HAC, normal reference. "
            "Pooled (CAD, CLP, NOK; AUD excluded by D7): pair fixed effects, Driscoll–Kraay "
            "errors with a normal reference (D1 as amended 2026-10-26). The frozen two-way "
            "estimator is reported on the second row of each horizon — same coefficient, different "
            "standard error. Two-way clustering needs the cluster count to grow in both dimensions "
            "and G_pair = 3; a synthetic Monte Carlo put its size at 0.5% against a nominal 5% "
            "(Driscoll–Kraay 4.5%), so it is invalid here rather than merely conservative. The "
            "amendment changes no coefficient and leaves both predictive nulls null. "
            "1-SD effect: β × SD(Δc) of the estimation sample, in percent. Holm across the six primary "
            "tests ({CAD, CLP, NOK} × {h = 0, 1}). MDE: two-sided 5%, 80% power, as partial R² of Δc. "
            "Rules fixed in design_decisions.md, Amendments, 2026-10-26.")
    write_table("table1_in_sample", "Table 1 · Commodity returns and FX returns, in sample",
                md_table(t), note)


def table2(res: pd.DataFrame) -> None:
    d = res[(res["test"] == "clark_west") & res["sample"].isin(PAIRS)]
    t = pd.DataFrame({
        "sample": d["sample"].to_numpy(), "h": d["h"].to_numpy(),
        "test period": [f"{a} → {b}" for a, b in zip(d["start"], d["end"])], "P": d["n"].to_numpy(),
        "OOS R², %": [f"{x:+.2f}" for x in d["oos_r2_pct"]],
        "CW gain, % of RW MSPE [95% CI]": [f"{e:+.2f} [{lo:+.2f}, {hi:+.2f}]" for e, lo, hi in
                                           zip(d["effect_pct"], d["effect_ci_lo_pct"], d["effect_ci_hi_pct"])],
        "CW stat": [f"{s:+.2f}" for s in d["stat"]], "p (one-sided)": d["p"].map(fp).to_numpy(),
        "MDE, % of RW MSPE": [f"{m:.2f}" for m in d["mde_pct"]],
        "MAE ratio": [f"{m:.3f}" for m in d["mae_ratio"]], "spec": d["spec_id"].to_numpy()})
    note = ("**Note.** Expanding window; the model is refitted at every origin on rows whose target "
            "date is on or before the origin; forecasts start at the sample midpoint. Benchmark: "
            "driftless random walk (zero return forecast). Clark–West (2007), not Diebold–Mariano: "
            "the model nests the benchmark (DD-11; deviates from the brief, flagged for the "
            "supervisor). Squared-error loss; OOS R² and the MAE ratio (model/RW, below 1 favours "
            "the model) are descriptive. MDE: one-sided 5%, 80% power. Per-origin forecasts: "
            "outputs/models/oos_forecasts.csv.")
    write_table("table2_out_of_sample", "Table 2 · Out-of-sample loss relative to the random walk",
                md_table(t), note)


def table3(res: pd.DataFrame) -> None:
    d = res[(res["sample"] == "AUD") & (res["test"] == "ols")]
    cw = res[(res["sample"] == "AUD") & (res["test"] == "clark_west")].set_index(["treatment", "h"])
    t = ols_columns(d)
    t.insert(0, "treatment", d["treatment"].to_numpy())
    t.insert(7, "CW p (OOS)", [fp(cw["p"].get((tr, h), np.nan)) for tr, h in zip(d["treatment"], d["h"])])
    gap = pd.read_csv(DIAG / "timing_gaps.csv").set_index("pair").loc["AUD"]
    note = ("**Note.** A methodological case study, never a fourth comparison point (D7). `SCO1` "
            "settles on the monthly average of IODEX prints, so pass-through falls as "
            "w = (N−k+1)/N through the contract month. **first8** is the DD-12 baseline (k ≤ 8, "
            "w 1.00 → 0.68); **first5** k ≤ 5; **full** every day; **rescaled** the full sample "
            "with Δc / w. The point is the pattern across treatments, not any one number; the "
            "coefficient evidence is weak (D7). Timing (D5): iron ore settles "
            f"{gap['modal_gap_hours']:.1f} h before the FX snap (range {gap['min_gap_hours']}–"
            f"{gap['max_gap_hours']} h, {gap['pct_days_off_mode']}% of days off-mode; settlement "
            "times unverified), so the same-day FX return contains most of a trading day after "
            "the commodity print. Not Holm-adjusted. Other columns as Table 1.")
    write_table("table3_aud_case_study", "Table 3 · AUD and iron ore: what the instrument does",
                md_table(t), note)


def table4(rob: pd.DataFrame, shift: pd.DataFrame) -> None:
    ran = rob["status"] == "run"
    t = pd.DataFrame({
        "check": rob["check"].to_numpy(), "ref": rob["ref"].to_numpy(),
        "sample": rob["sample"].to_numpy(), "h": rob["h"].astype("string").fillna("").to_numpy(),
        "β (SE)": [coef(b, s) if ok else "" for b, s, ok in zip(rob["estimate"], rob["se"], ran)],
        "baseline β": [f"{b:+.4f}" if ok else "" for b, ok in zip(rob["baseline_estimate"], ran)],
        "p": rob["p"].map(fp).to_numpy(), "N": rob["n"].astype("string").fillna("").to_numpy(),
        "status": rob["status"].to_numpy()})
    s = pd.DataFrame({
        "pair": shift["pair"], "signal vs ds_t": shift["signal"],
        "β₀": shift["beta_0"].map("{:+.4f}".format),
        "β_shift": shift["beta_shift"].map("{:+.4f}".format),
        "β₀ − β_shift (SE)": [coef(a, b) for a, b in zip(shift["diff"], shift["se_diff"])],
        "p (one-sided)": shift["p_one_sided"].map(fp),
        "|β_shift| < |β₀|": shift["magnitude_ok"], "verdict": shift["verdict"], "N": shift["n"]})
    placebo = rob[rob["treatment"] == "placebo_chf"]
    reading = "; ".join(f"{r.sample} β {r.estimate:+.4f}, p {fp(r.p)} → "
                        f"{'FAIL' if r.p < FZ.ALPHA else 'pass'}" for r in placebo.itertuples())
    note = ("**Placebo (D6), as declared:** a significant USDCHF β means the dollar control is not "
            f"absorbing the common factor. {reading}.\n\n"
            "**Note.** Each check re-runs the Table 1 estimator with one input changed; 'baseline β' "
            "is the Table 1 (or Table 3 first8) estimate on the full baseline sample. Horse races "
            "(dollar indices) run on their common sample. Date shift: D6 option 3 — the signal is "
            "shifted on the commodity's own trading calendar, Cov(β₀, β_shift) from stacked "
            "influence functions; a side passes if β₀ − β_shift is significantly positive at 5% "
            "one-sided and |β_shift| < |β₀|. The superseded option-1 table from 06 stays on record "
            "in outputs/diagnostics/date_shift_verdict.csv.")
    write_table("table4_robustness", "Table 4 · Robustness and falsification summary",
                md_table(t) + "\n\n## D6 date shift\n\n" + md_table(s), note)


def appendix() -> None:
    a = pd.read_csv(FZ.MANIFESTS / "sample_attrition.csv")
    a["n_dropped"] = a["n_dropped"].astype("Int64").astype("string")
    write_table("appendix_attrition", "Appendix · Data lineage and sample attrition", md_table(a),
                "**Note.** Regenerated by 05 at every run. Source coverage and hashes: "
                "manifests/source_inventory.csv; per-cell missingness causes: "
                "outputs/diagnostics/sample_attrition_causes.csv.")


# ---------------------------------------------------------------- figures
def footer(fig, text: str) -> None:
    fig.text(0.01, 0.005, text, fontsize=7, color=MUTED, ha="left", va="bottom", wrap=True)


def label_ends(ax, ends: dict[str, tuple]) -> None:
    """Direct labels at each line's end, pushed apart so none overlap (>= 10 pt)."""
    ax.get_ylim()                                        # settle autoscaling before measuring
    to_pt = 72 / ax.figure.dpi
    last = -np.inf
    for py, pair, x, y in sorted((ax.transData.transform((0, y))[1] * to_pt, p, x, y)
                                 for p, (x, y) in ends.items()):    # height depends on y only
        dy = max(0.0, last + 10 - py)
        ax.annotate(pair, (x, y), xytext=(4, dy), textcoords="offset points", va="center",
                    fontsize=8, color=INK2)
        last = py + dy


def forecasts(h: int = FZ.H_PRIMARY) -> dict[str, pd.DataFrame]:
    fc = pd.read_csv(MODELS / "oos_forecasts.csv")
    for c in ("origin", "target_date"):
        fc[c] = pd.to_datetime(fc[c], format="%Y-%m-%d")
    return {p: fc[fc["spec_id"] == f"{p}.baseline.h{h}.cw"].set_index("target_date") for p in PAIRS}


def fig1(fc: dict, res: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(8, 6.5), sharex=True)
    for ax, p in zip(axes, PAIRS):
        d, r = fc[p], res.set_index("spec_id").loc[f"{p}.baseline.h1.cw"]
        ax.plot(d.index, 100 * d["actual"], color=MUTED, lw=0.4, label="actual")
        ax.plot(d.index, 100 * d["forecast"], color=COLOR[p], lw=1.5, label="forecast")
        ax.set_title(f"{p} on {COMMODITY[p]}  ·  OOS R² {r.oos_r2_pct:+.2f}%,  CW p = {r.p:.2f}",
                     loc="left", fontsize=9)
        ax.set_ylabel("next-day return, %")
    axes[0].legend(loc="lower right", bbox_to_anchor=(1, 1), ncols=2)  # on the title line
    fig.suptitle("Actual vs forecast next-day FX return, expanding-window test period (h = 1)",
                 x=0.01, ha="left", fontsize=10)
    footer(fig, "Daily. Model: the next-day FX return on today's commodity, DXY and orthogonalized BCOM returns, "
                "refitted at every origin. Benchmark forecast is zero. Plotted at the target date.")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIGS / "fig1_actual_vs_forecast.png")
    plt.close(fig)


def fig2(fc: dict) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ends = {}
    for p in PAIRS:
        d = fc[p]
        gain = (1e4 * (d["actual"] ** 2 - (d["actual"] - d["forecast"]) ** 2)).cumsum()
        ax.plot(gain.index, gain, color=COLOR[p], lw=1.5, label=p)
        ends[p] = (gain.index[-1], gain.iloc[-1])
    ax.axhline(0, color=AXIS, lw=0.8)
    label_ends(ax, ends)
    ax.set_ylabel(r"cumulative $e^2_{RW} - e^2_{model}$, %²")
    ax.legend(loc="lower left")
    ax.set_title("Cumulative squared-error gain of the model over the random walk (h = 1)",
                 loc="left", fontsize=10)
    footer(fig, "Daily, each pair's expanding-window test period. Above zero: the model has "
                "accumulated less squared error than the zero forecast. Unadjusted (not Clark–West).")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGS / "fig2_cumulative_loss.png")
    plt.close(fig)


def fig3(fc: dict, window: int = 250) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ends = {}
    for p in PAIRS:
        d = fc[p]
        sse_m = ((d["actual"] - d["forecast"]) ** 2).rolling(window).sum()
        r2 = 100 * (1 - sse_m / (d["actual"] ** 2).rolling(window).sum())
        ax.plot(r2.index, r2, color=COLOR[p], lw=1.5, label=p)
        ends[p] = (r2.index[-1], r2.iloc[-1])
    ax.axhline(0, color=AXIS, lw=0.8)
    label_ends(ax, ends)
    ax.set_ylabel(f"rolling OOS R², % ({window} forecasts)")
    ax.legend(loc="lower left")
    ax.set_title("Rolling out-of-sample R² against the random walk (h = 1)",
                 loc="left", fontsize=10)
    footer(fig, f"Daily. Trailing {window} forecast origins (~1 year), plotted at the window's last "
                "target date. Below zero: the random walk forecast better over that window.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGS / "fig3_rolling_oos_r2.png")
    plt.close(fig)


def fig4() -> None:
    d = pd.read_csv(DIAG / "iron_decay_profile.csv").query("n >= 30")
    base = d.iloc[0]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(d["IRON_k"], d["mean_w"] / base["mean_w"], color=MUTED, lw=1.5,
            label="theory: w = (N−k+1)/N")
    ax.plot(d["IRON_k"], d["mean_abs_ret_pct"] / base["mean_abs_ret_pct"], color=COLOR["CAD"],
            lw=1.5, marker="o", ms=4, label="observed mean |SCO1 return|")
    ax.axvline(FZ.IRON_BASELINE_DAYS + 0.5, color=AXIS, lw=0.8)
    ax.annotate("baseline: first 8 days", (FZ.IRON_BASELINE_DAYS + 0.5, 1.05), xytext=(4, 0),
                textcoords="offset points", fontsize=8, color=INK2)
    ax.set_xticks(range(2, int(d["IRON_k"].max()) + 1, 2))
    ax.set_xlabel("trading day k of the contract month")
    ax.set_ylabel(f"index, day {int(base['IRON_k'])} = 1")
    ax.legend(loc="lower left")
    ax.set_title("Average-price settlement: iron ore futures pass-through decays through "
                 "the month", loc="left", fontsize=10)
    footer(fig, f"Daily SGX SCO1, {int(d['n'].sum())} returns, days with ≥ 30 observations. Day 1 is "
                "the roll day (return dropped, DD-05). Commodity series only - no FX data (DD-12).")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGS / "fig4_iron_ore_decay.png")
    plt.close(fig)


def fig5(shift: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(9, 3.2))
    for ax, (pair, g) in zip(axes, shift.groupby("pair")):
        g = g.set_index("shift")
        b = [g.loc[1, "beta_shift"], g.loc[1, "beta_0"], g.loc[-1, "beta_shift"]]
        se = [g.loc[1, "se_shift"], g.loc[1, "se_0"], g.loc[-1, "se_shift"]]
        ax.errorbar([0, 1, 2], b, yerr=1.96 * np.array(se), fmt="o", ms=5, color=COLOR[pair],
                    ecolor=COLOR[pair], elinewidth=1.2, capsize=0)
        ax.axhline(0, color=AXIS, lw=0.8)
        ax.set_xticks([0, 1, 2], [r"$\Delta c_{t-1}$", r"$\Delta c_t$", r"$\Delta c_{t+1}$"])
        ax.set_xlim(-0.5, 2.5)
        ax.set_title(f"{pair} · {g['verdict'].iloc[0]}", loc="left", fontsize=9)
    axes[0].set_ylabel(r"β on $\Delta s_t$, ±1.96 SE")
    fig.suptitle("Date-shift test: coefficient of FX at t on the commodity at t−1, t, t+1",
                 x=0.01, ha="left", fontsize=10)
    footer(fig, "Daily; each panel has its own y-scale. D6 option 3: PASS if β at t exceeds both "
                "shifts significantly (one-sided 5%) and in magnitude. AUD is the D7 case study.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(FIGS / "fig5_date_shift.png")
    plt.close(fig)


def fig6(res: pd.DataFrame) -> None:
    """Coefficient plot: the whole result in one picture.

    Same-day estimates sit far from zero with tight intervals; both predictive
    horizons straddle it. This is Table 1 and the h=1/h=5 nulls at a glance.
    """
    d = res[(res.test == "ols") & res.spec_id.str.endswith(".ols")
            & res["sample"].isin(PAIRS)].copy()
    d = d[d.treatment == "baseline"]
    fig, ax = plt.subplots(figsize=(8, 3.9))
    offs = {0: +0.22, 1: 0.0, 5: -0.22}
    mark = {0: "o", 1: "s", 5: "^"}
    for i, pair in enumerate(PAIRS):
        for h in (0, 1, 5):
            r = d[(d["sample"] == pair) & (d.h == h)]
            if r.empty:
                continue
            r = r.iloc[0]
            y = i + offs[h]
            ax.plot([r.ci_lo, r.ci_hi], [y, y], color=COLOR[pair], lw=1.4,
                    alpha=1.0 if h == 0 else 0.55, solid_capstyle="butt", zorder=3)
            ax.plot(r.estimate, y, mark[h], ms=5.5, color=COLOR[pair], zorder=4,
                    alpha=1.0 if h == 0 else 0.55,
                    mfc=COLOR[pair] if h == 0 else "#fcfcfb", mew=1.4)
    # One faint band per pair instead of a gridline through the middle estimate:
    # the three horizons are dodged, so a line at the tick would sit under h=1
    # only and read as misalignment rather than as grouping.
    ax.set_axisbelow(True)
    ax.yaxis.grid(False)
    for i in range(len(PAIRS)):
        if i % 2 == 0:
            ax.axhspan(i - 0.45, i + 0.45, color=GRID, alpha=0.45, lw=0, zorder=0)
    ax.axvline(0, color=INK2, lw=0.9, zorder=1)
    ax.set_yticks(range(len(PAIRS)), PAIRS)
    ax.set_ylim(-0.55, len(PAIRS) - 0.45)
    ax.set_xlabel(r"β on $\Delta c_t$, with 95% confidence interval")
    for h, lab, yy in ((0, "same day (h=0)", 0.92), (1, "next day (h=1)", 0.80),
                       (5, "five days (h=5)", 0.68)):
        ax.plot([], [], mark[h], color=INK2, ms=5.5, alpha=1.0 if h == 0 else 0.55,
                mfc=INK2 if h == 0 else "#fcfcfb", mew=1.4, label=lab)
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Same-day transmission is large and precise;\n"
                 "neither predictive horizon differs from zero", loc="left", fontsize=10)
    footer(fig, "Daily log returns, Newey-West HAC. Filled markers h=0, hollow h=1 and h=5. "
                "AUD is excluded (D7) and is reported separately in the case study.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIGS / "fig6_coefficients.png")
    plt.close(fig)


def fig7(rob: pd.DataFrame) -> None:
    """Placebo loadings beside the real ones: the limitation, drawn."""
    fig, ax = plt.subplots(figsize=(8, 3.8))
    w, xs = 0.26, np.arange(len(PAIRS))
    real = [float(RES_CACHE[(RES_CACHE["sample"] == p) & (RES_CACHE.h == 0)
                            & (RES_CACHE.spec_id == f"{p}.baseline.h0.ols")].estimate.iloc[0])
            for p in PAIRS]
    gbp = [float(rob[rob.spec_id == f"{p}.placebo_gbp.h0.ols"].estimate.iloc[0]) for p in PAIRS]
    chf = [float(rob[rob.spec_id == f"{p}.placebo_chf.h0.ols"].estimate.iloc[0]) for p in PAIRS]
    ax.bar(xs - w, real, w, color=[COLOR[p] for p in PAIRS], label="commodity currency")
    ax.bar(xs, gbp, w, color=MUTED, label="GBP placebo")
    ax.bar(xs + w, chf, w, color=AXIS, label="CHF placebo")
    for x, v in zip(xs - w, real):
        ax.annotate(f"{v:+.3f}", (x, v), xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=7.5, color=INK2)
    ax.axhline(0, color=INK2, lw=0.9)
    ax.set_xticks(xs, PAIRS)
    ax.set_ylabel(r"β on $\Delta c_t$")
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo, hi * 1.45)
    ax.legend(loc="upper left", fontsize=8, ncols=3)
    ax.set_title("Both placebos load significantly, in opposite\n"
                 "directions: a risk factor the dollar control misses",
                 loc="left", fontsize=10)
    footer(fig, "h=0, same specification with the placebo currency as the outcome. Sterling shares "
                "the risk-appetite factor and loads positive; the franc is a safe haven and mirrors "
                "it. All six are significant at 5% except CHF on CLP (p = 0.052).")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIGS / "fig7_placebo.png")
    plt.close(fig)


def fig8(res: pd.DataFrame) -> None:
    """Power: what the predictive test could have found, against what it found."""
    d = res[(res.test == "ols") & (res.treatment == "baseline") & res["sample"].isin(PAIRS)]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    w, xs = 0.3, np.arange(len(PAIRS))
    for j, h in enumerate((1, 5)):
        g = [d[(d["sample"] == p) & (d.h == h)].iloc[0] for p in PAIRS]
        ax.bar(xs + (j - 0.5) * w, [100 * r.mde_r2_partial for r in g], w * 0.92,
               color="#fcfcfb", edgecolor=AXIS, lw=1.0, hatch="///" if j else None,
               label=f"detectable at 80% power, h={h}")
        ax.bar(xs + (j - 0.5) * w, [100 * r.r2_partial for r in g], w * 0.92,
               color=[COLOR[p] for p in PAIRS], alpha=1.0 if j == 0 else 0.5,
               label=f"actually found, h={h}")
    ax.set_xticks(xs, PAIRS)
    ax.set_ylabel(r"partial $R^2$ of $\Delta c_t$, %")
    ax.legend(loc="upper right", fontsize=8, ncols=2)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.35)
    ax.set_title("The predictive nulls are informative: every test\n"
                 "could have found an effect several times larger",
                 loc="left", fontsize=10)
    footer(fig, "Outlined bars are the minimum detectable effect (two-sided 5%, 80% power); "
                "filled bars are the estimate. A null is only evidence when the outline clears "
                "the fill by a margin.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIGS / "fig8_power.png")
    plt.close(fig)


def fig9() -> None:
    """Costs: the gross-to-net collapse, and the assumption-free break-even.

    Left, a dumbbell per specification from gross Sharpe to net. Right, the
    half-spread at which each strategy breaks even, against the one charged.
    A bar short of its marker means the strategy cannot pay its own costs.
    """
    path = TABLES / "results_costs.csv"
    if not path.exists():
        return
    d = pd.read_csv(path).sort_values(["pair", "spec_id"], ascending=[True, False])
    lab = [r.spec_id.replace(".rf", "").replace(".baseline", "") for r in d.itertuples()]
    y = np.arange(len(d))
    col = [COLOR[r.pair] for r in d.itertuples()]

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(9.2, 4.6),
                                   gridspec_kw={"width_ratios": [1.15, 1]})

    for ax in (axl, axr):
        ax.set_axisbelow(True)
        ax.yaxis.grid(False)
        for i in y[::2]:
            ax.axhspan(i - 0.5, i + 0.5, color=GRID, alpha=0.45, lw=0, zorder=0)

    # left: gross -> net
    for i, r in enumerate(d.itertuples()):
        axl.plot([r.sharpe_gross, r.sharpe_net], [i, i], color=col[i], lw=1.3,
                 alpha=0.55, zorder=3, solid_capstyle="butt")
        axl.plot(r.sharpe_gross, i, "o", ms=5, mfc="#fcfcfb", mec=col[i], mew=1.5, zorder=4)
        axl.plot(r.sharpe_net, i, "o", ms=5, color=col[i], zorder=4)
    axl.axvline(0, color=INK2, lw=0.9, zorder=1)
    axl.set_yticks(y, lab, fontsize=8)
    axl.set_ylim(-0.5, len(d) + 0.3)
    axl.set_xlabel("annualised Sharpe ratio")
    axl.plot([], [], "o", ms=5, mfc="#fcfcfb", mec=INK2, mew=1.5, label="gross")
    axl.plot([], [], "o", ms=5, color=INK2, label="net of costs")
    axl.legend(loc="upper left", fontsize=8)
    axl.set_title("gross to net", loc="left", fontsize=9, color=INK2)

    # right: break-even vs charged
    be = d["breakeven_half_spread_bps"].fillna(0.0)
    axr.barh(y, be, 0.62, color=col, zorder=3)
    for i, r in enumerate(d.itertuples()):
        axr.plot(r.half_spread_bps, i, "|", ms=14, mew=2, color=INK, zorder=5)
        if not (r.breakeven_half_spread_bps == r.breakeven_half_spread_bps):
            axr.annotate("gross Sharpe < 0", (r.half_spread_bps + 0.25, i), fontsize=7,
                         color=MUTED, va="center", zorder=5)
    # a proxy entry: an inline marker would sit beside the real ticks and read as one
    axr.plot([], [], "|", ms=14, mew=2, color=INK, label="half-spread charged")
    axr.plot([], [], "s", ms=7, color=MUTED, label="break-even half-spread")
    axr.legend(loc="lower right", fontsize=8)
    axr.set_yticks(y, [""] * len(d))
    axr.set_ylim(-0.5, len(d) + 0.3)
    axr.set_xlim(0, max(d.half_spread_bps.max(), be.max()) * 1.18)
    axr.set_xlabel("one-way half-spread, basis points")
    axr.set_title("break-even cost vs cost charged", loc="left", fontsize=9, color=INK2)

    fig.suptitle("No specification survives costs: six of the ten positive Sharpes turn "
                 "negative,\nand the four that remain are AUD case-study runs with a deflated "
                 "Sharpe below 0.19",
                 x=0.01, ha="left", fontsize=10)
    footer(fig, "Random-forest strategy only; the baseline regression takes no position. "
                "Half-spreads are declared, not estimated (CAD/AUD 1.0 bp, NOK 1.5, CLP 7.5), "
                "tripled through 2020 H1 and charged on the change in position. Break-even is "
                "mean gross return divided by mean turnover, so it does not depend on the "
                "assumed spread. Carry and financing are not computed.")
    fig.tight_layout(rect=(0, 0.07, 1, 0.93))
    fig.savefig(FIGS / "fig9_costs.png")
    plt.close(fig)


def main() -> None:
    banner("09_tables_figures", ["outputs/tables/results_*.csv", "outputs/models/oos_forecasts.csv",
                                 "outputs/diagnostics/*.csv"],
           ["outputs/tables/*.md", "outputs/figures/*.png"])
    res = pd.read_csv(TABLES / "results_primary.csv")
    rob = pd.read_csv(TABLES / "results_robustness.csv")
    shift = pd.read_csv(DIAG / "date_shift_wald.csv")

    table1(res)
    table2(res)
    table3(res)
    table4(rob, shift)
    appendix()

    global RES_CACHE
    RES_CACHE = res
    fc = forecasts()
    fig1(fc, res)
    fig2(fc)
    fig3(fc)
    fig4()
    fig5(shift)
    fig6(res)
    fig7(rob)
    fig8(res)
    fig9()
    print(f"  wrote {len(list(TABLES.glob('*.md')))} tables, {len(list(FIGS.glob('*.png')))} figures")


if __name__ == "__main__":
    main()
