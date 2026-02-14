from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = REPO_ROOT / "data_processed" / "scope_receipts.json"
CANDIDATES_PATH = REPO_ROOT / "data_processed" / "chart2_selection_candidates.csv"
CURVES_PATH = REPO_ROOT / "data_processed" / "chart2_net_proxy_curves.csv"


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def require(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)


def main() -> None:
    for path in [SCOPE_PATH, CANDIDATES_PATH, CURVES_PATH]:
        require(path.exists(), f"missing required artifact: {path}")

    scope = json.loads(SCOPE_PATH.read_text(encoding="ascii"))
    candidates = pd.read_csv(CANDIDATES_PATH)
    curves = pd.read_csv(CURVES_PATH)

    required_scope_keys = [
        "chart2_selected_cohorts",
        "chart2_selected_count",
        "chart2_used_fallback",
        "chart2_plot_pool_count",
        "chart2_selected_min_n0",
        "chart2_policy",
    ]
    for key in required_scope_keys:
        require(key in scope, f"scope_receipts missing key: {key}")

    selected_cohorts = scope["chart2_selected_cohorts"]
    selected_count = scope["chart2_selected_count"]
    used_fallback = scope["chart2_used_fallback"]
    plot_pool_count = scope["chart2_plot_pool_count"]
    selected_min_n0 = scope["chart2_selected_min_n0"]
    policy = scope["chart2_policy"]

    require(isinstance(selected_cohorts, list), "chart2_selected_cohorts must be list")
    require(all(isinstance(x, str) for x in selected_cohorts), "chart2_selected_cohorts must be list[str]")
    require(isinstance(selected_count, int), "chart2_selected_count must be int")
    require(isinstance(used_fallback, bool), "chart2_used_fallback must be bool")
    require(isinstance(plot_pool_count, int), "chart2_plot_pool_count must be int")
    require(
        (selected_min_n0 is None) or isinstance(selected_min_n0, int),
        "chart2_selected_min_n0 must be int or null",
    )
    require(isinstance(policy, dict), "chart2_policy must be object")
    for key, expected in [
        ("MIN_COHORT_N", int),
        ("MIN_PLOT_COHORT_N", int),
        ("H", int),
        ("RIGHT_CENSOR_MODE", str),
        ("OBSERVED_ONLY", bool),
    ]:
        require(key in policy, f"chart2_policy missing key: {key}")
        require(isinstance(policy[key], expected), f"chart2_policy.{key} wrong type")

    required_candidate_cols = {
        "cohort_month",
        "n0",
        "denom_month0_gross_valid",
        "m2_logo_retention",
        "plot_floor_pass",
        "eligible_cohort",
        "selected_for_plot",
        "selection_reason",
        "rank_logo_m2",
    }
    missing_candidate_cols = required_candidate_cols - set(candidates.columns)
    require(
        not missing_candidate_cols,
        f"candidates missing columns: {sorted(missing_candidate_cols)}",
    )
    require(len(candidates) > 0, "candidates file is empty")

    candidates["eligible_cohort"] = candidates["eligible_cohort"].astype(bool)
    candidates["selected_for_plot"] = candidates["selected_for_plot"].astype(bool)
    candidates["plot_floor_pass"] = candidates["plot_floor_pass"].astype(bool)
    allowed_reasons = {"bottom", "mid", "top", "not_selected"}
    invalid_reasons = sorted(set(candidates["selection_reason"].astype(str)) - allowed_reasons)
    require(not invalid_reasons, f"invalid selection_reason values: {invalid_reasons}")

    missing_m2_for_eligible = int(
        candidates.loc[candidates["eligible_cohort"], "m2_logo_retention"].isna().sum()
    )
    require(
        missing_m2_for_eligible == 0,
        f"eligible rows contain missing m2_logo_retention (count={missing_m2_for_eligible})",
    )

    selected_from_candidates = sorted(
        candidates.loc[candidates["selected_for_plot"], "cohort_month"].astype(str).unique().tolist()
    )
    selected_count_candidates = int(len(selected_from_candidates))
    require(
        selected_count_candidates == selected_count,
        "selected count mismatch between candidates and scope receipts",
    )
    if not used_fallback:
        require(
            bool(candidates.loc[candidates["selected_for_plot"], "plot_floor_pass"].all()),
            "selected rows violate plot floor while used_fallback=False",
        )

    curves_required_cols = {"cohort_month", "eligible_cohort", "selected_for_plot"}
    missing_curves_cols = curves_required_cols - set(curves.columns)
    require(
        not missing_curves_cols,
        f"curves missing columns: {sorted(missing_curves_cols)}",
    )
    curves["selected_for_plot"] = curves["selected_for_plot"].astype(bool)
    curves["eligible_cohort"] = curves["eligible_cohort"].astype(bool)
    selected_from_curves = sorted(
        curves.loc[curves["selected_for_plot"], "cohort_month"].astype(str).unique().tolist()
    )
    require(
        bool(curves.loc[curves["selected_for_plot"], "eligible_cohort"].all()),
        "selected curves rows include non-eligible cohorts",
    )

    selected_from_receipts = sorted(selected_cohorts)
    require(
        selected_from_receipts == selected_from_candidates == selected_from_curves,
        "selected cohorts mismatch across receipts/candidates/curves",
    )

    selected_rows = candidates[candidates["selected_for_plot"]].copy()
    require(
        len(selected_rows) == len(selected_from_candidates),
        "selected candidates rows should be one row per selected cohort",
    )
    require(
        bool((selected_rows["selection_reason"] != "not_selected").all()),
        "selected rows must not have selection_reason='not_selected'",
    )

    print("validate_chart2_selection_artifacts=PASS")
    print(f"selected_cohorts={selected_from_receipts}")
    print(
        f"used_fallback={used_fallback}, plot_pool_count={plot_pool_count}, "
        f"selected_count={selected_count}"
    )


if __name__ == "__main__":
    main()

