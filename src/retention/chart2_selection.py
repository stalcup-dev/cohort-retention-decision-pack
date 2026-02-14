from __future__ import annotations

from typing import Any

import pandas as pd


def _pick_bottom_mid_top(cohorts: list[str]) -> list[str]:
    if len(cohorts) <= 3:
        return cohorts

    mid = len(cohorts) // 2
    selected = [cohorts[0], cohorts[mid], cohorts[-1]]
    selected = list(dict.fromkeys(selected))
    if len(selected) < 3:
        for cohort in cohorts:
            if cohort not in selected:
                selected.append(cohort)
            if len(selected) == 3:
                break
    return selected


def _selection_reason_map(selected: list[str]) -> dict[str, str]:
    if not selected:
        return {}
    if len(selected) == 1:
        return {selected[0]: "bottom"}
    if len(selected) == 2:
        return {selected[0]: "bottom", selected[1]: "top"}
    return {selected[0]: "bottom", selected[1]: "mid", selected[2]: "top"}


def select_chart2_cohorts(
    eligible_cohorts_df: pd.DataFrame,
    m2_logo_df: pd.DataFrame,
    *,
    min_cohort_n: int,
    min_plot_cohort_n: int,
) -> tuple[list[str], dict[str, Any]]:
    required_left = {"cohort_month", "n0", "denom_month0_gross_valid"}
    missing_left = required_left - set(eligible_cohorts_df.columns)
    if missing_left:
        raise ValueError(f"eligible_cohorts_df missing columns: {sorted(missing_left)}")

    required_right = {"cohort_month", "m2_logo_retention"}
    missing_right = required_right - set(m2_logo_df.columns)
    if missing_right:
        raise ValueError(f"m2_logo_df missing columns: {sorted(missing_right)}")

    left = eligible_cohorts_df.copy()
    if "eligible_cohort" not in left.columns:
        left["eligible_cohort"] = True
    left["eligible_cohort"] = left["eligible_cohort"].astype(bool)

    merged = left.merge(m2_logo_df.copy(), on="cohort_month", how="left")
    ranked = merged[
        (merged["eligible_cohort"])
        & (merged["n0"] >= int(min_cohort_n))
        & (merged["denom_month0_gross_valid"] > 0)
    ].copy()
    ranked = ranked.dropna(subset=["m2_logo_retention"]).copy()
    ranked["cohort_month"] = ranked["cohort_month"].astype(str)
    ranked = ranked.sort_values(
        ["m2_logo_retention", "cohort_month"],
        ascending=[True, True],
        kind="stable",
    ).reset_index(drop=True)
    ranked["rank_logo_m2"] = ranked.index + 1
    ranked["plot_floor_pass"] = ranked["n0"] >= int(min_plot_cohort_n)

    plot_pool = ranked[ranked["plot_floor_pass"]].copy()
    used_fallback = len(plot_pool) < 3
    selection_base = plot_pool if not used_fallback else ranked

    selected = _pick_bottom_mid_top(
        selection_base["cohort_month"].astype(str).tolist()
    )
    selected_set = set(selected)
    reason_map = _selection_reason_map(selected)
    candidates = ranked.copy()
    candidates["selected_for_plot"] = candidates["cohort_month"].isin(selected_set)
    candidates["selection_reason"] = candidates["cohort_month"].map(reason_map).fillna(
        "not_selected"
    )

    selected_rows = candidates[candidates["selected_for_plot"]].copy()
    selected_rows = selected_rows.sort_values(
        ["rank_logo_m2", "cohort_month"], ascending=[True, True], kind="stable"
    )
    selected_records = selected_rows[
        ["cohort_month", "n0", "denom_month0_gross_valid", "m2_logo_retention"]
    ].to_dict(orient="records")

    meta: dict[str, Any] = {
        "plot_pool_count": int(len(plot_pool)),
        "used_fallback": bool(used_fallback),
        "selected_cohorts": selected,
        "selected_count": int(len(selected)),
        "eligible_count": int(len(ranked)),
        "selected_min_n0": int(selected_rows["n0"].min()) if len(selected_rows) else None,
        "selection_candidates": candidates[
            [
                "cohort_month",
                "n0",
                "denom_month0_gross_valid",
                "m2_logo_retention",
                "plot_floor_pass",
                "eligible_cohort",
                "selected_for_plot",
                "selection_reason",
                "rank_logo_m2",
            ]
        ].to_dict(orient="records"),
        "selected_records": selected_records,
    }
    return selected, meta
