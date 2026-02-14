from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = REPO_ROOT / "data_processed"
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retention.policies import (
    HORIZON_H,
    MIN_COHORT_N,
    MIN_PLOT_COHORT_N,
    MIN_SKU_N,
    OBSERVED_ONLY,
    PRIORITY_W1,
    PRIORITY_W2,
    RIGHT_CENSOR_MODE,
    TOPK_SKUS_PER_FAMILY,
)
from retention.chart2_selection import select_chart2_cohorts


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")


def build_chart1(cma: pd.DataFrame) -> pd.DataFrame:
    out = (
        cma.groupby(["cohort_month", "months_since_first"], as_index=False)
        .agg(
            logo_retention=("is_retained_logo", "mean"),
            n_customers=("customer_id", "nunique"),
        )
        .sort_values(["cohort_month", "months_since_first"], kind="stable")
        .reset_index(drop=True)
    )
    out["months_since_first"] = out["months_since_first"].astype(int)
    return out


def apply_continuity_rule(
    df: pd.DataFrame,
    *,
    group_col: str,
    time_col: str,
    value_col: str,
    time_values: list[int],
) -> pd.DataFrame:
    out = df.copy()
    out[time_col] = out[time_col].astype(int)
    out = out.sort_values([group_col, time_col], kind="stable")

    def fix_group(g: pd.DataFrame) -> pd.DataFrame:
        # Require full horizon rows already present; do not create new rows here.
        present = g[time_col].tolist()
        expected = time_values
        if present != expected:
            raise AssertionError(
                f"Continuity rule requires full horizon rows per group. "
                f"group={g[group_col].iloc[0]} present={present} expected={expected}"
            )

        saw_missing = False
        for idx in range(len(g)):
            if saw_missing:
                g.iloc[idx, g.columns.get_loc(value_col)] = np.nan
                continue
            if pd.isna(g.iloc[idx][value_col]):
                saw_missing = True
        return g

    fixed = []
    for _, grp in out.groupby(group_col, sort=False):
        fixed.append(fix_group(grp.reset_index(drop=True)))
    return pd.concat(fixed, ignore_index=True)


def load_max_observed_month(receipts_path: Path) -> tuple[pd.Period, str]:
    require_file(receipts_path)
    receipts = json.loads(receipts_path.read_text(encoding="ascii"))
    raw_max_date = receipts.get("raw_max_date")
    if raw_max_date is None:
        raise ValueError(f"scope receipts missing raw_max_date: {receipts_path}")

    parsed_max = pd.to_datetime(raw_max_date, errors="coerce")
    if pd.isna(parsed_max):
        raise ValueError(
            f"scope receipts raw_max_date is not parseable: raw_max_date={raw_max_date}"
        )

    max_observed_month = parsed_max.to_period("M")
    print(
        "Observability anchor: "
        f"max_observed_month={max_observed_month} (from raw_max_date={raw_max_date})"
    )
    return max_observed_month, str(raw_max_date)


def format_month_span(months: list[int]) -> str:
    if not months:
        return "none"
    if months == list(range(min(months), max(months) + 1)):
        return f"{min(months)}..{max(months)}"
    return ",".join(str(m) for m in months)


def build_chart2_curves(
    cma: pd.DataFrame, max_observed_month: pd.Period
) -> tuple[pd.DataFrame, dict[str, object], pd.DataFrame]:
    month0 = cma[cma["months_since_first"] == 0].copy()
    baseline = (
        month0.groupby("cohort_month", as_index=False)
        .agg(
            n_customers_m0=("customer_id", "nunique"),
            denom_month0_gross_valid=("gross_revenue_valid", "sum"),
        )
    )

    monthly = (
        cma.groupby(["cohort_month", "months_since_first"], as_index=False)
        .agg(net_revenue_proxy_total=("net_revenue_proxy_total", "sum"))
    )
    out = monthly.merge(baseline, on="cohort_month", how="left")

    out["months_since_first"] = out["months_since_first"].astype(int)
    out["cohort_period"] = pd.PeriodIndex(out["cohort_month"], freq="M")
    out["activity_period"] = out["cohort_period"] + out["months_since_first"]
    out["is_observed"] = out["activity_period"] <= max_observed_month

    horizon_cutoff = max_observed_month - HORIZON_H
    out["eligible_cohort"] = (
        (out["n_customers_m0"] >= MIN_COHORT_N)
        & (out["denom_month0_gross_valid"] > 0)
        & (out["cohort_period"] <= horizon_cutoff)
    )
    out["net_retention_proxy"] = (
        out["net_revenue_proxy_total"] / out["denom_month0_gross_valid"]
    )
    out.loc[~out["is_observed"], "net_retention_proxy"] = np.nan

    # Pick plotting cohorts (3 max): bottom/mid/top by M2 logo retention among eligible cohorts.
    m2_logo = (
        cma[cma["months_since_first"] == 2]
        .groupby("cohort_month", as_index=False)
        .agg(m2_logo_retention=("is_retained_logo", "mean"))
    )
    eligible_cohorts = (
        out[
            [
                "cohort_month",
                "n_customers_m0",
                "denom_month0_gross_valid",
                "eligible_cohort",
            ]
        ]
        .drop_duplicates()
        .rename(columns={"n_customers_m0": "n0"})
        .reset_index(drop=True)
    )
    selected, selection_meta = select_chart2_cohorts(
        eligible_cohorts,
        m2_logo,
        min_cohort_n=MIN_COHORT_N,
        min_plot_cohort_n=MIN_PLOT_COHORT_N,
    )
    plot_pool_count = int(selection_meta["plot_pool_count"])
    if bool(selection_meta["used_fallback"]):
        print(
            f"WARN: plot-size floor not met for >=3 cohorts (MIN_PLOT_COHORT_N={MIN_PLOT_COHORT_N}, "
            f"pool_count={plot_pool_count}); falling back to all eligible cohorts."
        )
    if int(selection_meta["eligible_count"]) < 3:
        print(
            f"WARN: eligible cohorts with non-null M2 logo retention < 3 "
            f"(eligible_count={selection_meta['eligible_count']}); selecting all eligible cohorts."
        )

    out["selected_for_plot"] = out["cohort_month"].astype(str).isin(selected)
    selected_subset_ok = bool(
        out.loc[out["selected_for_plot"], "eligible_cohort"].astype(bool).all()
    )
    if not selected_subset_ok:
        raise AssertionError("selected_for_plot contains non-eligible cohorts")
    selected_rows = pd.DataFrame(selection_meta.get("selected_records", []))
    if len(selected_rows):
        picked = selected_rows.to_dict(orient="records")
        print("Chart2 selected cohorts (bottom/mid/top by M2 logo retention):", json.dumps(picked))
    else:
        print("Chart2 selected cohorts (bottom/mid/top by M2 logo retention): []")
    candidate_cols = [
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
    candidates = pd.DataFrame(selection_meta.get("selection_candidates", []))
    candidates = candidates.reindex(columns=candidate_cols).copy()
    candidates = candidates.sort_values(
        ["m2_logo_retention", "cohort_month"],
        ascending=[True, True],
        kind="stable",
    ).reset_index(drop=True)

    out = out.drop(columns=["cohort_period", "activity_period"])
    out = out[
        [
            "cohort_month",
            "months_since_first",
            "n_customers_m0",
            "denom_month0_gross_valid",
            "net_revenue_proxy_total",
            "net_retention_proxy",
            "is_observed",
            "eligible_cohort",
            "selected_for_plot",
        ]
    ].copy()
    out = out.sort_values(["cohort_month", "months_since_first"], kind="stable").reset_index(drop=True)
    return out, selection_meta, candidates


def build_chart2_heatmap(cma: pd.DataFrame, max_observed_month: pd.Period) -> pd.DataFrame:
    month0 = cma[cma["months_since_first"] == 0].copy()
    baseline = (
        month0.groupby("cohort_month", as_index=False)
        .agg(
            baseline_gross_t0=("gross_revenue_valid", "sum"),
            n_customers_m0=("customer_id", "nunique"),
        )
    )

    monthly = (
        cma.groupby(["cohort_month", "months_since_first"], as_index=False)
        .agg(
            net_proxy_total=("net_revenue_proxy_total", "sum"),
        )
    )

    # Per-point effective n: customers with any activity signal in that month.
    cma_eff = cma.copy()
    cma_eff["has_any_activity"] = (cma_eff["orders_count_valid"] > 0) | (cma_eff["net_revenue_proxy_total"] != 0)
    eff = (
        cma_eff[cma_eff["has_any_activity"]]
        .groupby(["cohort_month", "months_since_first"], as_index=False)
        .agg(n_customers=("customer_id", "nunique"))
    )
    monthly = monthly.merge(eff, on=["cohort_month", "months_since_first"], how="left")
    monthly["n_customers"] = monthly["n_customers"].fillna(0).astype(int)

    out = monthly.merge(baseline, on="cohort_month", how="left")
    out["months_since_first"] = out["months_since_first"].astype(int)
    out["cohort_period"] = pd.PeriodIndex(out["cohort_month"], freq="M")
    out["activity_period"] = out["cohort_period"] + out["months_since_first"]
    out["activity_month"] = out["activity_period"].astype(str)
    out["is_observed"] = out["activity_period"] <= max_observed_month
    out["net_retention_proxy"] = out["net_proxy_total"] / out["baseline_gross_t0"]
    out.loc[~out["is_observed"], "net_retention_proxy"] = np.nan

    # Suppress tiny-n cells (keep as NaN so the heatmap shows missing, not zero).
    out.loc[out["n_customers"] < MIN_COHORT_N, "net_retention_proxy"] = np.nan

    # CA-59: summary row across all cohorts (weights = month-0 gross baseline).
    # For each month t, weighted ratio = sum(net_proxy_total_t) / sum(baseline_gross_t0),
    # restricting to cohorts where the cell is observed and not suppressed.
    elig = out[out["net_retention_proxy"].notna()].copy()
    weighted = (
        elig.groupby("months_since_first", as_index=False)
        .agg(
            net_proxy_total=("net_proxy_total", "sum"),
            baseline_gross_t0=("baseline_gross_t0", "sum"),
        )
    )
    weighted["net_retention_proxy"] = np.where(
        weighted["baseline_gross_t0"] > 0,
        weighted["net_proxy_total"] / weighted["baseline_gross_t0"],
        np.nan,
    )
    weighted["cohort_month"] = "ALL_WEIGHTED"
    weighted["n_customers"] = 0
    weighted["n_customers_m0"] = int(baseline["n_customers_m0"].sum()) if len(baseline) else 0
    # Continuity rule: if month t-1 is missing, month t must be missing.
    out = apply_continuity_rule(
        out,
        group_col="cohort_month",
        time_col="months_since_first",
        value_col="net_retention_proxy",
        time_values=list(range(HORIZON_H + 1)),
    )

    out = out.drop(columns=["cohort_period", "activity_period"])
    out = out.sort_values(["cohort_month", "months_since_first"], kind="stable").reset_index(drop=True)
    out = out[["cohort_month", "months_since_first", "net_retention_proxy", "n_customers", "n_customers_m0"]].copy()
    weighted = weighted[["cohort_month", "months_since_first", "net_retention_proxy", "n_customers", "n_customers_m0"]]
    out = pd.concat([weighted, out], ignore_index=True)
    out["months_since_first"] = out["months_since_first"].astype(int)
    out = out.sort_values(["cohort_month", "months_since_first"], kind="stable").reset_index(drop=True)
    return out


def filter_m2_observed_only(cma: pd.DataFrame, max_observed_month: pd.Period) -> pd.DataFrame:
    m2 = cma[cma["months_since_first"] == 2].copy()
    m2["cohort_period"] = pd.PeriodIndex(m2["cohort_month"], freq="M")
    m2["activity_period_m2"] = m2["cohort_period"] + 2
    return m2[m2["activity_period_m2"] <= max_observed_month].copy()


def build_chart3(cma: pd.DataFrame, max_observed_month: pd.Period) -> pd.DataFrame:
    m2 = filter_m2_observed_only(cma, max_observed_month=max_observed_month)
    fam = (
        m2.groupby("first_product_family", as_index=False)
        .agg(
            n_customers=("customer_id", "nunique"),
            m2_logo_retention=("is_retained_logo", "mean"),
        )
        .sort_values(["n_customers", "first_product_family"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )

    top8 = fam.head(8)["first_product_family"].tolist()
    m2["family_group"] = np.where(m2["first_product_family"].isin(top8), m2["first_product_family"], "Other")

    # Net proxy retention at M2 by family_group:
    # numerator = sum(net_revenue_proxy_total at M2) for customers in group
    # denominator = sum(gross_revenue_valid at M0) for those customers
    m2_customers = m2[["customer_id"]].drop_duplicates()
    m0 = cma[cma["months_since_first"] == 0][["customer_id", "gross_revenue_valid", "first_product_family"]].copy()
    m0["family_group"] = np.where(m0["first_product_family"].isin(top8), m0["first_product_family"], "Other")
    m0 = m0.merge(m2_customers, on="customer_id", how="inner")
    denom = (
        m0.groupby("family_group", as_index=False)
        .agg(gross_m0=("gross_revenue_valid", "sum"))
    )

    numer = (
        m2.groupby("family_group", as_index=False)
        .agg(net_proxy_m2=("net_revenue_proxy_total", "sum"))
    )

    out = (
        m2.groupby("family_group", as_index=False)
        .agg(
            n_customers=("customer_id", "nunique"),
            m2_logo_retention=("is_retained_logo", "mean"),
        )
        .merge(denom, on="family_group", how="left")
        .merge(numer, on="family_group", how="left")
    )
    out["gross_m0"] = out["gross_m0"].fillna(0.0).astype(float)
    out["net_proxy_m2"] = out["net_proxy_m2"].fillna(0.0).astype(float)
    out["m2_net_proxy_retention"] = np.where(
        out["gross_m0"] > 0,
        out["net_proxy_m2"] / out["gross_m0"],
        np.nan,
    )

    # Decision orientation: sort by weaker opportunity first (low logo, then low net proxy).
    out = out.sort_values(
        ["m2_logo_retention", "m2_net_proxy_retention", "n_customers", "family_group"],
        ascending=[True, True, False, True],
        kind="stable",
    ).reset_index(drop=True)
    return out[["family_group", "n_customers", "m2_logo_retention", "m2_net_proxy_retention"]]


def build_chart2_family_scatter(chart3: pd.DataFrame) -> pd.DataFrame:
    out = chart3.copy()
    out = out.rename(
        columns={
            "family_group": "first_product_family",
            "m2_logo_retention": "x_m2_logo_retention",
            "m2_net_proxy_retention": "y_m2_net_retention_proxy",
        }
    )
    out["x_m2_logo_retention"] = out["x_m2_logo_retention"].astype(float)
    out["y_m2_net_retention_proxy"] = out["y_m2_net_retention_proxy"].astype(float)
    out["n_customers"] = out["n_customers"].astype(int)

    weight = out["n_customers"].astype(float)
    weight_sum = float(weight.sum())
    if weight_sum > 0:
        overall_x = float((out["x_m2_logo_retention"] * weight).sum() / weight_sum)
        overall_y = float((out["y_m2_net_retention_proxy"] * weight).sum() / weight_sum)
    else:
        overall_x = float("nan")
        overall_y = float("nan")
    out["overall_x"] = overall_x
    out["overall_y"] = overall_y

    score_x = 1.0 - out["x_m2_logo_retention"].fillna(0.0)
    score_y = 1.0 - out["y_m2_net_retention_proxy"].fillna(0.0)
    out["priority_score"] = (score_x * PRIORITY_W1) + (score_y * PRIORITY_W2)
    out = out.sort_values(
        ["priority_score", "n_customers", "first_product_family"],
        ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)
    out["rank_priority"] = np.arange(1, len(out) + 1, dtype=int)
    return out[
        [
            "first_product_family",
            "n_customers",
            "x_m2_logo_retention",
            "y_m2_net_retention_proxy",
            "priority_score",
            "rank_priority",
            "overall_x",
            "overall_y",
        ]
    ]


def assert_family_set_match(chart2_scatter: pd.DataFrame, chart3: pd.DataFrame) -> bool:
    families_chart2 = set(chart2_scatter["first_product_family"].astype(str).tolist())
    families_chart3 = set(chart3["family_group"].astype(str).tolist())
    if families_chart2 != families_chart3:
        only_chart2 = sorted(families_chart2 - families_chart3)
        only_chart3 = sorted(families_chart3 - families_chart2)
        raise AssertionError(
            "Chart family-set mismatch: "
            f"only_in_chart2={only_chart2}, only_in_chart3={only_chart3}"
        )
    print("chart2_chart3_family_set_match=PASS")
    return True


def build_appendix_top_products(
    order_lines: pd.DataFrame,
    customers: pd.DataFrame,
    cma: pd.DataFrame,
    chart3: pd.DataFrame,
    max_observed_month: pd.Period,
) -> tuple[pd.DataFrame, dict[str, object]]:
    chart3_targets = chart3.copy()
    chart3_targets = chart3_targets[chart3_targets["family_group"].astype(str) != "Other"].copy()
    chart3_targets = chart3_targets[chart3_targets["n_customers"] >= MIN_COHORT_N].copy()
    chart3_targets = chart3_targets.sort_values(
        ["m2_logo_retention", "m2_net_proxy_retention", "n_customers", "family_group"],
        ascending=[True, True, False, True],
        kind="stable",
    )
    target_families = chart3_targets.head(3)["family_group"].astype(str).tolist()

    out_cols = [
        "first_product_family",
        "sku",
        "description",
        "n_customers_m0",
        "m0_gross_valid",
        "m2_logo_retention_observed",
        "m2_net_retention_proxy_observed",
        "delta_net_proxy_vs_family_pp",
        "share_of_family_m0_gross_pct",
    ]

    if not target_families:
        return pd.DataFrame(columns=out_cols), {
            "target_families": [],
            "min_sku_n": MIN_SKU_N,
            "topk_skus_per_family": TOPK_SKUS_PER_FAMILY,
            "observed_only": OBSERVED_ONLY,
            "right_censor_mode": RIGHT_CENSOR_MODE,
            "max_observed_month": str(max_observed_month),
            "rows_written": 0,
        }

    customers_local = customers.copy()
    customers_local["customer_id"] = customers_local["customer_id"].astype(str)
    customers_local["first_order_id"] = customers_local["first_order_id"].astype(str)

    order_lines_local = order_lines.copy()
    order_lines_local["customer_id"] = order_lines_local["customer_id"].astype(str)
    order_lines_local["order_id"] = order_lines_local["order_id"].astype(str)
    order_lines_local["sku"] = order_lines_local["sku"].astype(str)
    order_lines_local["description"] = (
        order_lines_local["description"]
        .fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    cust_target = customers_local[
        customers_local["first_product_family"].astype(str).isin(target_families)
    ][["customer_id", "first_order_id", "first_product_family"]].copy()

    first_lines = order_lines_local.merge(cust_target, on="customer_id", how="inner")
    first_lines = first_lines[first_lines["order_id"] == first_lines["first_order_id"]].copy()
    first_lines = first_lines[
        first_lines["product_family"].astype(str) == first_lines["first_product_family"].astype(str)
    ].copy()
    first_lines = first_lines[first_lines["line_amount_gross"] > 0].copy()

    if first_lines.empty:
        return pd.DataFrame(columns=out_cols), {
            "target_families": target_families,
            "min_sku_n": MIN_SKU_N,
            "topk_skus_per_family": TOPK_SKUS_PER_FAMILY,
            "observed_only": OBSERVED_ONLY,
            "right_censor_mode": RIGHT_CENSOR_MODE,
            "max_observed_month": str(max_observed_month),
            "rows_written": 0,
        }

    sku_base = (
        first_lines.groupby(["first_product_family", "sku"], as_index=False)
        .agg(
            n_customers_m0=("customer_id", "nunique"),
            m0_gross_valid=("line_amount_gross", "sum"),
        )
    )

    desc_rank = (
        first_lines.groupby(["first_product_family", "sku", "description"], as_index=False)
        .agg(desc_gross=("line_amount_gross", "sum"))
        .sort_values(
            ["first_product_family", "sku", "desc_gross", "description"],
            ascending=[True, True, False, True],
            kind="stable",
        )
    )
    desc_pick = desc_rank.drop_duplicates(subset=["first_product_family", "sku"], keep="first")
    sku_base = sku_base.merge(
        desc_pick[["first_product_family", "sku", "description"]],
        on=["first_product_family", "sku"],
        how="left",
    )

    sku_base = sku_base[sku_base["n_customers_m0"] >= MIN_SKU_N].copy()
    sku_base = (
        sku_base.sort_values(
            ["first_product_family", "m0_gross_valid", "sku"],
            ascending=[True, False, True],
            kind="stable",
        )
        .groupby("first_product_family", as_index=False, sort=False)
        .head(TOPK_SKUS_PER_FAMILY)
        .reset_index(drop=True)
    )

    if sku_base.empty:
        return pd.DataFrame(columns=out_cols), {
            "target_families": target_families,
            "min_sku_n": MIN_SKU_N,
            "topk_skus_per_family": TOPK_SKUS_PER_FAMILY,
            "observed_only": OBSERVED_ONLY,
            "right_censor_mode": RIGHT_CENSOR_MODE,
            "max_observed_month": str(max_observed_month),
            "rows_written": 0,
        }

    fam_m0 = (
        sku_base.groupby("first_product_family", as_index=False)
        .agg(family_m0_gross=("m0_gross_valid", "sum"))
    )
    sku_base = sku_base.merge(fam_m0, on="first_product_family", how="left")
    sku_base["share_of_family_m0_gross_pct"] = np.where(
        sku_base["family_m0_gross"] > 0,
        (sku_base["m0_gross_valid"] / sku_base["family_m0_gross"]) * 100.0,
        np.nan,
    )

    cma_local = cma.copy()
    cma_local["customer_id"] = cma_local["customer_id"].astype(str)
    cma_local["cohort_period"] = pd.PeriodIndex(cma_local["cohort_month"], freq="M")

    m2 = cma_local[cma_local["months_since_first"] == 2].copy()
    m2["activity_period_m2"] = m2["cohort_period"] + 2
    m2_obs = m2[m2["activity_period_m2"] <= max_observed_month][
        ["customer_id", "is_retained_logo", "net_revenue_proxy_total"]
    ].copy()

    m0 = cma_local[cma_local["months_since_first"] == 0][
        ["customer_id", "gross_revenue_valid"]
    ].copy()

    sku_customer = (
        first_lines[["first_product_family", "sku", "customer_id"]]
        .drop_duplicates()
        .merge(
            sku_base[["first_product_family", "sku"]],
            on=["first_product_family", "sku"],
            how="inner",
        )
    )
    sku_customer_obs = sku_customer.merge(
        m2_obs[["customer_id"]].drop_duplicates(),
        on="customer_id",
        how="inner",
    )

    m2_logo = (
        sku_customer_obs.merge(m2_obs, on="customer_id", how="left")
        .groupby(["first_product_family", "sku"], as_index=False)
        .agg(
            m2_logo_retention_observed=("is_retained_logo", "mean"),
            m2_net_numer=("net_revenue_proxy_total", "sum"),
        )
    )
    m2_denom = (
        sku_customer_obs.merge(m0, on="customer_id", how="left")
        .groupby(["first_product_family", "sku"], as_index=False)
        .agg(m2_net_denom=("gross_revenue_valid", "sum"))
    )
    m2_stats = m2_logo.merge(m2_denom, on=["first_product_family", "sku"], how="outer")
    m2_stats["m2_net_retention_proxy_observed"] = np.where(
        m2_stats["m2_net_denom"] > 0,
        m2_stats["m2_net_numer"] / m2_stats["m2_net_denom"],
        np.nan,
    )

    out = sku_base.merge(
        m2_stats[
            [
                "first_product_family",
                "sku",
                "m2_logo_retention_observed",
                "m2_net_retention_proxy_observed",
            ]
        ],
        on=["first_product_family", "sku"],
        how="left",
    )

    fam_net = chart3[
        ["family_group", "m2_net_proxy_retention"]
    ].rename(
        columns={
            "family_group": "first_product_family",
            "m2_net_proxy_retention": "family_m2_net_retention_proxy",
        }
    )
    out = out.merge(fam_net, on="first_product_family", how="left")
    out["delta_net_proxy_vs_family_pp"] = (
        out["m2_net_retention_proxy_observed"] - out["family_m2_net_retention_proxy"]
    ) * 100.0

    out["description"] = out["description"].fillna("").astype(str).str.slice(0, 120)
    out = out[
        [
            "first_product_family",
            "sku",
            "description",
            "n_customers_m0",
            "m0_gross_valid",
            "m2_logo_retention_observed",
            "m2_net_retention_proxy_observed",
            "delta_net_proxy_vs_family_pp",
            "share_of_family_m0_gross_pct",
        ]
    ].copy()
    out = out.sort_values(
        ["first_product_family", "m0_gross_valid", "sku"],
        ascending=[True, False, True],
        kind="stable",
    ).reset_index(drop=True)

    receipt = {
        "target_families": target_families,
        "min_sku_n": MIN_SKU_N,
        "topk_skus_per_family": TOPK_SKUS_PER_FAMILY,
        "observed_only": OBSERVED_ONLY,
        "right_censor_mode": RIGHT_CENSOR_MODE,
        "max_observed_month": str(max_observed_month),
        "rows_written": int(len(out)),
    }
    return out, receipt


def update_qa_right_censor_check(path: Path, cma: pd.DataFrame, chart2_curves: pd.DataFrame) -> bool:
    # Full-grid contract validated from customer_month_activity (customer x months 0..H).
    rows_per_customer = cma.groupby("customer_id").size()
    full_grid_customer_ok = bool((rows_per_customer == (HORIZON_H + 1)).all()) if len(rows_per_customer) else True

    # Render-layer masking validated from chart2_curves via is_observed -> NA.
    required_cols = {"cohort_month", "months_since_first", "is_observed", "net_retention_proxy"}
    if not required_cols.issubset(set(chart2_curves.columns)):
        raise AssertionError(
            f"Chart2 QA check missing required columns: {sorted(required_cols - set(chart2_curves.columns))}"
        )

    per_cohort_months = (
        chart2_curves.groupby("cohort_month")["months_since_first"]
        .apply(lambda s: sorted(s.astype(int).tolist()))
    )
    full_h_cohort_ok = bool(
        per_cohort_months.apply(lambda vals: vals == list(range(HORIZON_H + 1))).all()
    )
    mask_ok = bool(
        chart2_curves.loc[~chart2_curves["is_observed"].astype(bool), "net_retention_proxy"].isna().all()
    )
    right_censor_ok = full_grid_customer_ok and full_h_cohort_ok and mask_ok

    line_prefix = "- Chart2 right-censor applied (unobserved months are NaN, not 0): "
    line_value = (
        f"{line_prefix}{'PASS' if right_censor_ok else 'FAIL'} "
        f"(nan_cells={int(chart2_curves['net_retention_proxy'].isna().sum())}, "
        f"full_grid_customer_ok={full_grid_customer_ok}, full_h_cohort_ok={full_h_cohort_ok}, mask_ok={mask_ok})"
    )
    layer_prefix = "- H=6 grid exists; censoring applied only at chart render layer. "
    layer_value = f"{layer_prefix}{'PASS' if full_grid_customer_ok and mask_ok else 'FAIL'}"

    if not path.exists():
        return right_censor_ok

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    replaced = False
    for idx, line in enumerate(lines):
        if line.startswith(line_prefix):
            lines[idx] = line_value
            replaced = True
            break

    if not replaced:
        lines.append("")
        lines.append("## Right-censor sanity")
        lines.append(line_value)

    layer_replaced = False
    for idx, line in enumerate(lines):
        if line.startswith(layer_prefix):
            lines[idx] = layer_value
            layer_replaced = True
            break
    if not layer_replaced:
        if "## Right-censor sanity" not in lines:
            lines.append("")
            lines.append("## Right-censor sanity")
        lines.append(layer_value)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return right_censor_ok


def main() -> None:
    cma_path = DATA_PROCESSED / "customer_month_activity.csv"
    order_lines_path = DATA_PROCESSED / "order_lines.csv"
    customers_path = DATA_PROCESSED / "customers.csv"
    receipts_path = DATA_PROCESSED / "scope_receipts.json"
    require_file(cma_path)
    require_file(order_lines_path)
    require_file(customers_path)
    require_file(receipts_path)

    max_observed_month, raw_max_date = load_max_observed_month(receipts_path)

    cma = pd.read_csv(cma_path)
    order_lines = pd.read_csv(order_lines_path)
    customers = pd.read_csv(customers_path)

    chart1 = build_chart1(cma)
    chart2_heatmap = build_chart2_heatmap(cma, max_observed_month=max_observed_month)
    chart2_curves, chart2_selection_meta, chart2_candidates = build_chart2_curves(
        cma, max_observed_month=max_observed_month
    )
    chart3 = build_chart3(cma, max_observed_month=max_observed_month)
    chart2_scatter = build_chart2_family_scatter(chart3)
    family_set_match = assert_family_set_match(chart2_scatter, chart3)
    appendix, appendix_receipt = build_appendix_top_products(
        order_lines=order_lines,
        customers=customers,
        cma=cma,
        chart3=chart3,
        max_observed_month=max_observed_month,
    )

    out1 = DATA_PROCESSED / "chart1_logo_retention_heatmap.csv"
    out2 = DATA_PROCESSED / "chart2_net_proxy_heatmap.csv"
    out2c = DATA_PROCESSED / "chart2_net_proxy_curves.csv"
    out2cand = DATA_PROCESSED / "chart2_selection_candidates.csv"
    out2s = DATA_PROCESSED / "appendix_chart2_family_scatter.csv"
    out3 = DATA_PROCESSED / "chart3_m2_by_family.csv"
    out_appendix = DATA_PROCESSED / "appendix_top_products_in_chart3_targets.csv"
    out_appendix_receipt = DATA_PROCESSED / "appendix_top_products_in_chart3_targets_receipt.json"

    chart1.to_csv(out1, index=False)
    chart2_heatmap.to_csv(out2, index=False)
    chart2_curves.to_csv(out2c, index=False)
    chart2_candidates.to_csv(out2cand, index=False)
    chart2_scatter.to_csv(out2s, index=False)
    chart3.to_csv(out3, index=False)
    appendix.to_csv(out_appendix, index=False)
    out_appendix_receipt.write_text(json.dumps(appendix_receipt, indent=2), encoding="ascii")

    scope_payload = json.loads(receipts_path.read_text(encoding="ascii"))
    for stale_key in [
        "selection_candidates",
        "chart2_selection_candidates",
        "chart2_selected_records",
    ]:
        scope_payload.pop(stale_key, None)
    selected_cohorts = list(chart2_selection_meta.get("selected_cohorts", []))
    scope_payload.update(
        {
            "chart2_plot_pool_count": int(chart2_selection_meta.get("plot_pool_count", 0)),
            "chart2_used_fallback": bool(chart2_selection_meta.get("used_fallback", False)),
            "chart2_selected_cohorts": selected_cohorts,
            "chart2_selected_count": int(chart2_selection_meta.get("selected_count", len(selected_cohorts))),
            "chart2_selected_min_n0": chart2_selection_meta.get("selected_min_n0"),
            "chart2_policy": {
                "MIN_COHORT_N": int(MIN_COHORT_N),
                "MIN_PLOT_COHORT_N": int(MIN_PLOT_COHORT_N),
                "H": int(HORIZON_H),
                "RIGHT_CENSOR_MODE": RIGHT_CENSOR_MODE,
                "OBSERVED_ONLY": bool(OBSERVED_ONLY),
            },
        }
    )
    receipts_path.write_text(json.dumps(scope_payload, indent=2), encoding="ascii")

    qa_path = REPO_ROOT / "docs" / "QA_CHECKLIST.md"
    right_censor_ok = update_qa_right_censor_check(qa_path, cma, chart2_curves)

    print(
        "Chart policies: "
        f"H={HORIZON_H}, MIN_COHORT_N={MIN_COHORT_N}, "
        f"MIN_PLOT_COHORT_N={MIN_PLOT_COHORT_N}, "
        f"RIGHT_CENSOR_MODE={RIGHT_CENSOR_MODE}, OBSERVED_ONLY={OBSERVED_ONLY}, "
        f"PRIORITY_W1={PRIORITY_W1}, PRIORITY_W2={PRIORITY_W2}, "
        f"MIN_SKU_N={MIN_SKU_N}, TOPK_SKUS_PER_FAMILY={TOPK_SKUS_PER_FAMILY}"
    )

    summary = {
        "max_observed_month": str(max_observed_month),
        "raw_max_date": raw_max_date,
        "chart1_rows": int(len(chart1)),
        "chart1_unique_cohorts": int(chart1["cohort_month"].nunique()),
        "chart2_heatmap_rows": int(len(chart2_heatmap)),
        "chart2_curves_rows": int(len(chart2_curves)),
        "chart2_curves_unique_cohorts": int(chart2_curves["cohort_month"].nunique()),
        "chart2_curves_selected_cohorts": int(chart2_curves.loc[chart2_curves["selected_for_plot"], "cohort_month"].nunique()),
        "chart2_candidates_rows": int(len(chart2_candidates)),
        "chart3_rows": int(len(chart3)),
        "chart3_unique_families": int(chart3["family_group"].nunique()),
        "chart2_scatter_rows": int(len(chart2_scatter)),
        "appendix_rows": int(len(appendix)),
        "appendix_unique_families": int(appendix["first_product_family"].nunique()) if len(appendix) else 0,
        "chart2_chart3_family_set_match": family_set_match,
        "chart2_right_censor_check": right_censor_ok,
    }
    print("Chart table summary:", json.dumps(summary))


if __name__ == "__main__":
    main()
