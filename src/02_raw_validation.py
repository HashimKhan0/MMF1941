"""Raw-data validation: one row per loaded series, plus a list of extreme returns.

Every statistic is computed on the series' OWN rows (status ok or src_na), not on the
outer-joined calendar - a date another market traded but this one did not (no_row) is
not a gap in this series.

Per series:
    column, dtype, first/last date, source rows, missing (src_na), no_row, uncovered,
    longest run of consecutive identical values (with its dates), and for price series
    min/max against the expected level band in CLAUDE.md.
    Ticker columns report the number of contract changes instead (expect ~12/year).

Extreme returns: log return between consecutive source rows, both present and positive,
flagged where |r| > 5 x full-sample std. Roll days are flagged, not removed. Non-positive
prices (log undefined) are listed separately rather than silently becoming NaN.

Outputs:
    outputs/diagnostics/raw_validation_summary.csv
    outputs/diagnostics/raw_validation_outliers.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data_compile import (OK, SRC_NA, NO_ROW, UNCOVERED,  # noqa: E402
                          curncy_df, curncy_status, comm_df, comm_status,
                          bcom_df, bcom_status, dxy_df, dxy_status)

OUT = ROOT / "outputs" / "diagnostics"
SIGMA = 5.0

# expected levels, CLAUDE.md "Expected levels" - approximate, so reported not asserted
BANDS = {
    "USDNOK_PX_LAST": (5.5, 11), "USDCLP_PX_LAST": (470, 1000),
    "AUDUSD_PX_LAST": (0.55, 1.10), "USDCAD_PX_LAST": (0.95, 1.47),
    "WTI_PX_LAST": (-37.63, 114), "BRENT_PX_LAST": (20, 128),
    "COPPER_PX_LAST": (4300, 11000), "HG1_PX_LAST": (200, 680),
    "IRON_PX_LAST": (40, 220),
}
# price column -> its generic-contract ticker column, for flagging roll days
TICKER = {"WTI_PX_LAST": "WTI_FUT_CUR_GEN_TICKER", "BRENT_PX_LAST": "BRENT_FUT_CUR_GEN_TICKER",
          "IRON_PX_LAST": "IRON_FUT_CUR_GEN_TICKER"}


def longest_run(v: pd.Series) -> tuple[int, object, object]:
    """Longest run of identical consecutive non-NA values: (length, first date, last date)."""
    v = v.dropna()
    if v.empty:
        return 0, pd.NaT, pd.NaT
    grp = (v != v.shift()).cumsum()
    sizes = grp.value_counts()
    g = sizes.idxmax()
    dates = v.index[grp == g]
    return int(sizes.max()), dates[0].date(), dates[-1].date()


def summarize(frame: str, df: pd.DataFrame, st: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    rows, flags = [], []
    for c in df.columns:
        own = st[c].isin([OK, SRC_NA])
        s = df.loc[own, c]
        counts = st[c].value_counts()
        n_run, run_from, run_to = longest_run(s)
        row = {
            "frame": frame, "series": c, "dtype": str(df[c].dtype),
            "first_date": s.first_valid_index().date(), "last_date": s.last_valid_index().date(),
            "source_rows": int(own.sum()), "missing_src_na": int(counts[SRC_NA]),
            "no_row": int(counts[NO_ROW]), "uncovered": int(counts[UNCOVERED]),
            "longest_identical_run": n_run, "run_from": run_from, "run_to": run_to,
        }

        if not pd.api.types.is_numeric_dtype(df[c]):
            t = s.dropna()
            row["contract_changes"] = int((t != t.shift()).iloc[1:].sum())
            rows.append(row)
            continue

        lo, hi = BANDS.get(c, (np.nan, np.nan))
        row.update(min=s.min(), max=s.max(), band_lo=lo, band_hi=hi,
                   out_of_band=bool(c in BANDS and (s.min() < lo or s.max() > hi)))

        for d, p in s[s <= 0].items():
            flags.append({"series": c, "date": d.date(), "kind": "nonpositive_price",
                          "price": p, "prev_price": s.shift().get(d)})

        prev = s.shift()
        valid = s.gt(0) & prev.gt(0)  # both consecutive source rows present and positive
        r = np.log(s / prev).where(valid)
        sd = r.std()
        row.update(n_returns=int(r.notna().sum()), ret_std=sd, n_gt_5sigma=int((r.abs() > SIGMA * sd).sum()))

        roll = None
        if c in TICKER:
            t = df[TICKER[c]].reindex(s.index)
            roll = (t != t.shift()) & t.notna() & t.shift().notna()
        for d in r.index[r.abs() > SIGMA * sd]:
            flags.append({"series": c, "date": d.date(), "kind": "gt_5sigma",
                          "price": s[d], "prev_price": prev[d], "log_return": r[d],
                          "z": r[d] / sd, "roll_day": bool(roll[d]) if roll is not None else None})
        rows.append(row)
    return rows, flags


def main() -> None:
    rows, flags = [], []
    for name, df, st in [("curncy", curncy_df, curncy_status), ("comm", comm_df, comm_status),
                         ("bcom", bcom_df, bcom_status), ("dxy", dxy_df, dxy_status)]:
        r, f = summarize(name, df, st)
        rows += r
        flags += f

    summary = pd.DataFrame(rows)
    outliers = pd.DataFrame(flags).sort_values(["series", "date"], ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT / "raw_validation_summary.csv", index=False)
    outliers.to_csv(OUT / "raw_validation_outliers.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_columns", None, "display.max_rows", None):
        print(summary.to_string(index=False))
        print(f"\n{len(outliers)} flagged observations:")
        print(outliers.to_string(index=False))
        bad = summary.loc[summary.get("out_of_band", pd.Series(dtype=bool)).fillna(False).astype(bool), "series"]
        print("\nOUT OF EXPECTED BAND:", list(bad) or "none")


if __name__ == "__main__":
    main()
