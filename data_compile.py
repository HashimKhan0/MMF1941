"""Load raw_data/ into four date-indexed DataFrames.

    curncy_df : AUDUSD, USDCAD (AT-04 csv) + USDNOK, USDCLP (BBG.xlsx)
    comm_df   : WTI, Brent, iron ore, LME copper, COMEX copper (HG1) prices
                + FUT_CUR_GEN_TICKER where available
    bcom_df   : BCOM price index
    dxy_df    : DXY index

All joins are outer joins on date, so a date present in any source is kept and
anything a source lacks for that date is NA. Everything is restricted to
START..END (2010-01-01 to 2025-12-31); within that window no rows or NA cells are dropped.
Quotes are left exactly as pulled (no inversion, no returns) - cleaning happens downstream.

Every NA is not the same NA. Each loader can also return a status frame (same index
and columns, categorical) saying *why* a cell is what it is:

    ok          value present
    src_na      the source has a row for this date but the value is missing (#N/A / blank)
    no_row      the source has no row for this date, inside its own first..last date:
                a day this series did not trade (or was not pulled) but another did
    uncovered   the date is before the source's first row or after its last row

The status lives in its own frame rather than in the price cells so price columns
stay float64 - a sentinel number or string in a price column would either leak into
returns or turn the column into object dtype.

Usage:
    from data_compile import curncy_df, comm_df, bcom_df, dxy_df
    from data_compile import curncy_status, comm_status, bcom_status, dxy_status
    df, status = load_comm(status=True)
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parent / "raw_data"
BBG = RAW / "BBG.xlsx"
FX_CSV = RAW / "AT-04_Daily_Spot_Prices_G10_FX_Pairs_Daily_2000_2025.csv"
HG1_XLSX = RAW / "Copper_Price_Daily.xlsx"

# study window (inclusive); only trims dates outside it, NA inside it is kept
START, END = "2010-01-01", "2025-12-31"

# Bloomberg error strings that should be read as missing
NA_VALUES = ["#N/A", "#N/A N/A", "#N/A Invalid Security", "#N/A Field Not Applicable", "N/A", ""]

# per-cell provenance labels for the outer join (see module docstring)
OK, SRC_NA, NO_ROW, UNCOVERED = "ok", "src_na", "no_row", "uncovered"
STATUS = pd.CategoricalDtype([OK, SRC_NA, NO_ROW, UNCOVERED])


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    """Date index, sorted ascending, clipped to START..END; whitespace-only strings -> NA."""
    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"
    if df.index.duplicated().any():
        raise ValueError(f"duplicate dates in {list(df.columns)}")
    df = df.sort_index().loc[START:END]
    obj = df.select_dtypes("object").columns
    df[obj] = df[obj].apply(lambda s: s.str.strip() if s.dtype == "object" else s).replace("", pd.NA)
    return df


def _status(frames: list[pd.DataFrame], index: pd.DatetimeIndex) -> pd.DataFrame:
    """Status of every cell of the outer join of `frames` on `index`."""
    cols = {}
    for f in frames:
        has_row = index.isin(f.index)
        covered = (index >= f.index.min()) & (index <= f.index.max())
        g = f.reindex(index)
        for c in f.columns:
            cols[c] = np.select([has_row & g[c].notna().to_numpy(), has_row, covered],
                                [OK, SRC_NA, NO_ROW], UNCOVERED)
    return pd.DataFrame(cols, index=index).astype(STATUS)


def _outer(frames: list[pd.DataFrame], status: bool = False):
    df = _finish(pd.concat(frames, axis=1, join="outer"))
    return (df, _status(frames, df.index)) if status else df


def _bbg_sheet(sheet: str, prefix: str) -> pd.DataFrame:
    df = pd.read_excel(BBG, sheet_name=sheet, na_values=NA_VALUES)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]  # stray blank columns
    df = df.set_index("DATE")
    df.columns = [f"{prefix}_{c}" for c in df.columns]
    return _finish(df)


def _csv_series(fname: str, value_col: str, name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / fname, na_values=NA_VALUES)
    return _finish(df.set_index("Date")[[value_col]].rename(columns={value_col: name}))


def _hg1() -> pd.DataFrame:
    # COMEX copper, used only to orthogonalize BCOM. Dates are native Excel datetimes.
    # HG1_Comdty_PX_BID is deliberately not loaded - stale/unusable (see CLAUDE.md).
    df = pd.read_excel(HG1_XLSX, na_values=NA_VALUES, usecols=["Date", "HG1_Comdty_PX_LAST"])
    return _finish(df.set_index("Date").rename(columns={"HG1_Comdty_PX_LAST": "HG1_PX_LAST"}))


def _fx_csv_pair(pair: str) -> pd.DataFrame:
    # each pair has its own Date column in the AT-04 file; pair them explicitly
    raw = pd.read_csv(FX_CSV, na_values=NA_VALUES)
    date_col = f"{pair} - Date"
    px_col = next(c for c in raw.columns if c.startswith(pair) and "Last Price" in c)
    df = raw[[date_col, px_col]].dropna(subset=[date_col])  # only drops padding rows with no date
    return _finish(df.set_index(date_col).rename(columns={px_col: f"{pair}_PX_LAST"}))


def load_curncy(status: bool = False):
    return _outer([
        _fx_csv_pair("AUDUSD"),
        _fx_csv_pair("USDCAD"),
        _bbg_sheet("nok", "USDNOK"),
        _bbg_sheet("clp", "USDCLP"),
    ], status)


def load_comm(status: bool = False):
    # WTI price is only in the csv; its generic-contract ticker is only in BBG.xlsx
    wti_px = _csv_series("Crude_Oil_WTI_Spot_Daily.csv", "Last Price", "WTI_PX_LAST")
    return _outer([
        wti_px,
        _bbg_sheet("wti", "WTI"),
        _bbg_sheet("brent", "BRENT"),
        _bbg_sheet("iron", "IRON"),
        _bbg_sheet("copper", "COPPER"),
        _hg1(),
    ], status)


def load_bcom(status: bool = False):
    return _outer([_csv_series("Commodity_Index_BCOM_Price_Daily.csv", "BCOM_PX_LAST", "BCOM_PX_LAST")], status)


def load_dxy(status: bool = False):
    return _outer([_csv_series("USD_Index_DXY_Daily.csv", "DXY Index", "DXY_PX_LAST")], status)


curncy_df, curncy_status = load_curncy(status=True)
comm_df, comm_status = load_comm(status=True)
bcom_df, bcom_status = load_bcom(status=True)
dxy_df, dxy_status = load_dxy(status=True)


if __name__ == "__main__":
    for name, df, st in [("curncy_df", curncy_df, curncy_status), ("comm_df", comm_df, comm_status),
                         ("bcom_df", bcom_df, bcom_status), ("dxy_df", dxy_df, dxy_status)]:
        print(f"\n=== {name}  {df.shape}  {df.index.min().date()} -> {df.index.max().date()}")
        print(pd.DataFrame({"first": df.apply(lambda s: s.first_valid_index()),
                            "last": df.apply(lambda s: s.last_valid_index()),
                            "n_obs": df.notna().sum(),
                            "n_na": df.isna().sum()})
              .join(st.apply(lambda s: s.value_counts()).T[STATUS.categories]))
