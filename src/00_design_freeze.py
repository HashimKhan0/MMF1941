"""00_design_freeze - the approved estimand, windows, universe, exclusions and
sign conventions, loaded once from config/project_config.yaml and asserted.

Every other module imports from here. No module may define its own copy of a
constant that appears in the config: that is how a spec silently drifts.

Nothing here reads data. Nothing here estimates anything.

Usage:
    from importlib import import_module
    FZ = import_module("src.00_design_freeze")        # or see src/__init__.py
    FZ.PAIRS["AUD"]["commodity"]
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "project_config.yaml"

with open(CONFIG_PATH, encoding="utf-8") as fh:
    CFG = yaml.safe_load(fh)

# ---------------------------------------------------------------- paths
PATHS = {k: ROOT / v for k, v in CFG["paths"].items()}
RAW, INTERIM, ANALYTIC = PATHS["raw"], PATHS["interim"], PATHS["analytic"]
MANIFESTS, OUTPUTS = PATHS["manifests"], PATHS["outputs"]
for p in (INTERIM, ANALYTIC, OUTPUTS / "diagnostics"):
    p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- sample
START = CFG["sample"]["start"]
END = CFG["sample"]["end"]
BINDING_END = CFG["sample"]["binding_end"]

# ---------------------------------------------------------------- universe
PAIRS = CFG["pairs"]
PAIR_NAMES = list(PAIRS)

DOLLAR = CFG["controls"]["dollar"]["column"]
DOLLAR_ROBUST = CFG["controls"]["dollar_robustness"]["column"]
BCOM = CFG["controls"]["broad_commodity"]["column"]
ORTHOGONALIZE = CFG["controls"]["broad_commodity"]["orthogonalize"]

# ---------------------------------------------------------------- frozen spec
FROZEN = CFG["frozen"]

SIGN_RULE = FROZEN["sign_convention"]["rule"]
EXPECTED_BETA_SIGN = FROZEN["sign_convention"]["expected_beta_sign"]

RETURN_TYPE = FROZEN["returns"]["type"]
ROLL_RULE = FROZEN["returns"]["roll_rule"]
EXPECTED_ROLLS_PER_YEAR = FROZEN["returns"]["expected_rolls_per_year"]

H_CONTEMP = FROZEN["horizons"]["contemporaneous"]
H_PRIMARY = FROZEN["horizons"]["predictive_primary"]
H_SECONDARY = FROZEN["horizons"]["predictive_secondary"]
HORIZONS = [H_CONTEMP, H_PRIMARY, H_SECONDARY]
LOSS = FROZEN["horizons"]["loss_function"]

IRON = FROZEN["iron_ore"]
IRON_BASELINE_DAYS = 8          # DD-12: first 8 trading days of the contract month
IRON_ROBUST_DAYS = 5

EXCL = FROZEN["exclusions"]
WTI_NEGATIVE_DATES = EXCL["wti_negative_price_dates"]
NOK_DROP_DATES = EXCL["nok_drop_dates"]
BRENT_INDETERMINATE_ROLL_DATES = EXCL["brent_indeterminate_roll_dates"]
CLP_MAX_SPAN_DAYS = EXCL["clp_max_return_span_calendar_days"]

INF = FROZEN["inference"]
SEED = INF["seed"]
PLACEBO = INF["placebo_outcome"]
N_PRIMARY_TESTS = INF["n_primary_tests"]
POWER_TARGET = INF["power_target"]

# D6: a catastrophe gate, not an expectation band. The old sanity band was
# removed 2026-10-26 - it had no basis and risked anchoring the result.
BUG_ABS_BETA_MAX = CFG["bug_detector"]["abs_beta_max"]
BUG_R2_MAX = CFG["bug_detector"]["r2_max"]

DATE_FORMATS = CFG["date_formats"]
NA_VALUES = CFG["na_values"]

FROZEN_ON = CFG["project"].get("frozen_on")


# ---------------------------------------------------------------- assertions
def _assert_frozen() -> None:
    """Fail loudly if the config has drifted from the recorded design."""
    assert len(PAIR_NAMES) == 4, f"expected 4 pairs, got {PAIR_NAMES}"
    assert set(PAIR_NAMES) == {"AUD", "CAD", "CLP", "NOK"}, PAIR_NAMES

    # DD-01: AUDUSD is the only pair not inverted
    inverted = {p for p, s in PAIRS.items() if s["invert"]}
    assert inverted == {"CAD", "CLP", "NOK"}, f"inversion set drifted: {inverted}"

    # DD-03: iron ore is not a BCOM constituent; the other three are
    assert PAIRS["AUD"]["orthogonalize_against"] is None
    for p in ("CAD", "CLP", "NOK"):
        assert PAIRS[p]["orthogonalize_against"], f"{p} must be orthogonalized"
    # DD-02/DD-03: LME is the CLP regressor, COMEX is its orthogonalization input
    assert PAIRS["CLP"]["commodity"] == "COPPER_PX_LAST"
    assert PAIRS["CLP"]["orthogonalize_against"] == "HG1_PX_LAST"

    # DD-05: only LMCADS03 has no contract field
    no_roll = {p for p, s in PAIRS.items() if s["contract_field"] is None}
    assert no_roll == {"CLP"}, f"roll-exempt set drifted: {no_roll}"

    # DD-08
    assert H_CONTEMP == 0 and H_PRIMARY == 1 and H_SECONDARY == 5, HORIZONS
    assert LOSS == "squared_error", LOSS

    # DD-11
    assert INF["oos_test"] == "clark_west", INF["oos_test"]

    # DD-13 as amended 2026-10-26
    assert DOLLAR == "DXY_PX_LAST", DOLLAR
    assert CFG["controls"]["dollar"]["is_ice_dxy"] is True
    assert DOLLAR_ROBUST == "USD_BROAD_PX_LAST", DOLLAR_ROBUST

    # DD-12
    assert IRON_BASELINE_DAYS == 8 and IRON_ROBUST_DAYS == 5
    assert PAIRS["AUD"]["start"] == "2013-04-08", PAIRS["AUD"]["start"]  # DD-15

    # DD-16 / DD-20
    assert len(WTI_NEGATIVE_DATES) == 2, WTI_NEGATIVE_DATES
    assert NOK_DROP_DATES == ["2010-01-01"], NOK_DROP_DATES
    assert CLP_MAX_SPAN_DAYS == 5, CLP_MAX_SPAN_DAYS

    assert N_PRIMARY_TESTS == 4 * 2
    assert RETURN_TYPE == "log" and ROLL_RULE == "drop"

    # D6: the bug detector is a gate, never an expectation
    assert BUG_ABS_BETA_MAX >= 0.5 and BUG_R2_MAX >= 0.4
    assert "sanity" not in CFG, "the old sanity band was removed - see D6"


_assert_frozen()


def summary() -> str:
    frozen = FROZEN_ON or "NOT YET FROZEN"
    return (
        f"design freeze: {frozen}\n"
        f"  sample      {START} .. {END}  (binding: {BINDING_END})\n"
        f"  pairs       {', '.join(PAIR_NAMES)}\n"
        f"  sign        {SIGN_RULE}; beta expected {EXPECTED_BETA_SIGN}\n"
        f"  returns     {RETURN_TYPE}; rolls {ROLL_RULE}\n"
        f"  horizons    h={HORIZONS}, loss={LOSS}\n"
        f"  controls    {DOLLAR} (primary), {DOLLAR_ROBUST} (robustness), {BCOM}"
        f"{' orthogonalized' if ORTHOGONALIZE else ''}\n"
        f"  iron ore    baseline first {IRON_BASELINE_DAYS} trading days, "
        f"robustness {IRON_ROBUST_DAYS}; w=(N-k+1)/N\n"
        f"  inference   {INF['per_pair']} per pair; {INF['pooled']} pooled; "
        f"{INF['oos_test']} OOS; {INF['multiple_testing']} over {N_PRIMARY_TESTS} tests\n"
        f"  seed        {SEED}\n"
        f"  bug gate    |beta| > {BUG_ABS_BETA_MAX} or R2 > {BUG_R2_MAX} => say so, do not report"
    )


if __name__ == "__main__":
    print(summary())
    print("\nall design assertions passed")
