"""08c_costs - transaction costs on the random forest strategy.

The guide's completion checklist requires that "economic magnitudes, costs and
confidence intervals are reported together", and construction hint 12 asks for
"realistic carry, financing and stress-period transaction costs". The baseline
specification is a regression, not a position, so costs do not enter it. They do
enter 08b, which turns each forecast into a signed position and reports a Sharpe
ratio - and a Sharpe before costs is not a Sharpe.

Cost model, fixed before the first run:

  Half-spread   per pair, in basis points of notional, one way. CAD and NOK are
                major pairs; AUD is major but the iron ore pair; CLP is an
                emerging-market cross and trades far wider. Values are
                conservative round numbers for daily interbank FX, declared
                here rather than estimated, because no bid-ask series was
                obtainable (the one bid column in the data is unusable, D3).
  Stress        spreads widen in stress. The declared stress window is
                2020-01-01 to 2020-06-30 - the same window used for the
                influence check in 08 - with a multiplier applied to it.
  Turnover      the strategy holds sign(forecast). Cost is charged on the
                CHANGE in position, so a hold costs nothing and a flip costs a
                full round trip (two half-spreads).
  Carry         NOT computed. Daily carry is the interest differential, which
                requires forward points; those were never obtained and the
                Bloomberg API is suspended. The omission is declared rather
                than approximated, and its direction is discussed below.

Also reports the BREAK-EVEN half-spread: the cost at which the gross Sharpe
reaches zero. That is the useful number, because it is independent of whatever
spread assumption anyone prefers.

Outputs
  outputs/tables/results_costs.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import load, banner

FZ = load("00_design_freeze")
DSR = load("08b_rf_dsr")

# one-way half-spread, basis points of notional. Declared, not estimated.
HALF_SPREAD_BPS = {"CAD": 1.0, "NOK": 1.5, "AUD": 1.0, "CLP": 7.5}
STRESS_WINDOW = ("2020-01-01", "2020-06-30")
STRESS_MULTIPLIER = 3.0
ANN = 252


def costed(fc: pd.DataFrame, pair: str) -> pd.DataFrame:
    """Net the strategy return of turnover cost, per observation."""
    hs = HALF_SPREAD_BPS[pair] / 1e4
    pos = np.sign(fc["rf"]).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())        # first trade is an entry
    mult = pd.Series(1.0, index=fc.index)
    mult.loc[STRESS_WINDOW[0]:STRESS_WINDOW[1]] = STRESS_MULTIPLIER
    cost = turn * hs * mult
    gross = pos * fc["actual"]
    return pd.DataFrame({"gross": gross, "cost": cost, "net": gross - cost,
                         "turnover": turn, "half_spread": hs * mult})


def breakeven_half_spread(d: pd.DataFrame) -> float:
    """Half-spread in bps at which the mean net return is zero.

    mean(gross) = mean(turnover) * hs  =>  hs = mean(gross) / mean(turnover).
    Negative or undefined when the gross mean is already negative.
    """
    t = d["turnover"].mean()
    if t <= 0 or d["gross"].mean() <= 0:
        return np.nan
    return d["gross"].mean() / t * 1e4


def main() -> None:
    banner("08c_costs", ["outputs/models/rf_forecasts.csv"],
           ["outputs/tables/results_costs.csv"])

    path = FZ.OUTPUTS / "models" / "rf_forecasts.csv"
    if not path.exists():
        print("  rf_forecasts.csv not found - run 08b first")
        return
    fc = pd.read_csv(path, index_col="date", parse_dates=["date"])

    print(f"\n  half-spreads (bps, one way): {HALF_SPREAD_BPS}")
    print(f"  stress window {STRESS_WINDOW[0]} to {STRESS_WINDOW[1]}, "
          f"spreads x{STRESS_MULTIPLIER}")
    print("  carry and financing NOT computed - no forward points obtainable\n")

    rows = []
    for spec, g in fc.groupby("spec_id"):
        pair = spec.split(".")[0]
        d = costed(g.sort_index(), pair)
        n_trials = fc["spec_id"].nunique()
        gross = DSR.deflated_sharpe(d["gross"], n_trials)
        net = DSR.deflated_sharpe(d["net"], n_trials)
        rows.append({
            "spec_id": spec, "pair": pair, "n": len(d),
            "half_spread_bps": HALF_SPREAD_BPS[pair],
            "mean_turnover": d["turnover"].mean(),
            "annual_cost_pct": d["cost"].mean() * ANN * 100,
            "sharpe_gross": gross["sharpe"], "sharpe_net": net["sharpe"],
            "dsr_gross": gross["dsr"], "dsr_net": net["dsr"],
            "breakeven_half_spread_bps": breakeven_half_spread(d),
            "survives_costs": bool(net["sharpe"] > 0 and net["dsr"] > 0.95),
        })

    res = pd.DataFrame(rows).sort_values("spec_id")
    res.to_csv(FZ.OUTPUTS / "tables" / "results_costs.csv", index=False)

    print(f"  {'spec':<26} {'turn':>5} {'cost%/y':>8} {'SR gross':>9} "
          f"{'SR net':>7} {'DSR net':>8} {'b/e bps':>8}")
    for _, r in res.iterrows():
        be = f"{r.breakeven_half_spread_bps:8.2f}" if r.breakeven_half_spread_bps == r.breakeven_half_spread_bps else "       -"
        print(f"  {r.spec_id:<26} {r.mean_turnover:5.2f} {r.annual_cost_pct:8.2f} "
              f"{r.sharpe_gross:+9.2f} {r.sharpe_net:+7.2f} {r.dsr_net:8.3f}{be}")

    n_pos_gross = int((res.sharpe_gross > 0).sum())
    n_pos_net = int((res.sharpe_net > 0).sum())
    print(f"\n  positive Sharpe gross: {n_pos_gross} of {len(res)}")
    print(f"  positive Sharpe net:   {n_pos_net} of {len(res)}")
    print(f"  surviving costs with DSR > 0.95: {int(res.survives_costs.sum())} of {len(res)}")
    be = res["breakeven_half_spread_bps"].dropna()
    if len(be):
        print(f"  break-even half-spread, where gross is positive: "
              f"{be.min():.2f} to {be.max():.2f} bps "
              f"(assumed {min(HALF_SPREAD_BPS.values())}-{max(HALF_SPREAD_BPS.values())} bps)")


if __name__ == "__main__":
    main()
