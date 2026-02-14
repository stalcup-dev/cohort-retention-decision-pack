from __future__ import annotations

import pandas as pd

from retention.chart2_selection import select_chart2_cohorts


def test_select_chart2_cohorts_normal_pool_meets_floor() -> None:
    eligible = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04", "2010-05"],
            "n0": [240, 260, 300, 280, 320],
            "denom_month0_gross_valid": [1000, 1000, 1000, 1000, 1000],
            "eligible_cohort": [True, True, True, True, True],
        }
    )
    m2_logo = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04", "2010-05"],
            "m2_logo_retention": [0.10, 0.20, 0.30, 0.40, 0.50],
        }
    )

    selected, meta = select_chart2_cohorts(
        eligible, m2_logo, min_cohort_n=50, min_plot_cohort_n=200
    )

    assert meta["used_fallback"] is False
    assert meta["selected_count"] == 3
    assert selected == ["2010-01", "2010-03", "2010-05"]


def test_select_chart2_cohorts_fallback_when_plot_pool_too_small() -> None:
    eligible = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04", "2010-05"],
            "n0": [210, 180, 170, 220, 160],
            "denom_month0_gross_valid": [1000, 1000, 1000, 1000, 1000],
            "eligible_cohort": [True, True, True, True, True],
        }
    )
    m2_logo = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04", "2010-05"],
            "m2_logo_retention": [0.11, 0.22, 0.33, 0.44, 0.55],
        }
    )

    selected, meta = select_chart2_cohorts(
        eligible, m2_logo, min_cohort_n=50, min_plot_cohort_n=200
    )

    assert meta["used_fallback"] is True
    assert 1 <= meta["selected_count"] <= 3
    assert selected == ["2010-01", "2010-03", "2010-05"]


def test_select_chart2_cohorts_excludes_null_m2_logo() -> None:
    eligible = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04"],
            "n0": [220, 230, 240, 250],
            "denom_month0_gross_valid": [1000, 1000, 1000, 1000],
            "eligible_cohort": [True, True, True, True],
        }
    )
    m2_logo = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04"],
            "m2_logo_retention": [0.10, None, 0.30, 0.40],
        }
    )

    selected, meta = select_chart2_cohorts(
        eligible, m2_logo, min_cohort_n=50, min_plot_cohort_n=200
    )

    assert meta["eligible_count"] == 3
    assert "2010-02" not in selected


def test_select_chart2_cohorts_deterministic_tie_break_and_subset_contract() -> None:
    eligible = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04"],
            "n0": [300, 305, 310, 315],
            "denom_month0_gross_valid": [1000, 1000, 1000, 1000],
            "eligible_cohort": [True, True, True, True],
        }
    )
    m2_logo = pd.DataFrame(
        {
            "cohort_month": ["2010-01", "2010-02", "2010-03", "2010-04"],
            "m2_logo_retention": [0.20, 0.20, 0.35, 0.40],
        }
    )

    selected, meta = select_chart2_cohorts(
        eligible, m2_logo, min_cohort_n=50, min_plot_cohort_n=200
    )

    candidates = pd.DataFrame(meta["selection_candidates"])
    eligible_set = set(candidates.loc[candidates["eligible_cohort"], "cohort_month"].astype(str))
    assert set(selected).issubset(eligible_set)
    assert selected == ["2010-01", "2010-03", "2010-04"]
