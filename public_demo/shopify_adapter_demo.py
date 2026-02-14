from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
INPUT_PATH = ROOT / "shopify_mock_orders.csv"
PLOT_PATH = ROOT / "shopify_demo_output.png"
SUMMARY_PATH = ROOT / "shopify_demo_summary.csv"


def to_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def main() -> None:
    orders = pd.read_csv(INPUT_PATH)
    orders["order_ts"] = pd.to_datetime(orders["created_at"], errors="coerce")
    orders["customer_id"] = orders["customer_id"].fillna("GUEST").astype(str).str.strip()
    orders["order_month_period"] = orders["order_ts"].dt.to_period("M")
    orders["order_month"] = orders["order_month_period"].astype(str)

    # Demo-valid purchase proxy aligned with public-safe narrative.
    orders["is_valid_purchase"] = (
        orders["total_price"].fillna(0).gt(0)
        & (~orders["financial_status"].fillna("").str.lower().isin(["refunded", "voided"]))
        & (orders["cancelled_at"].fillna("").eq(""))
    )

    valid = orders[(orders["customer_id"] != "GUEST") & (orders["is_valid_purchase"])].copy()

    first_valid = (
        valid.sort_values(["customer_id", "order_ts", "id"], kind="stable")
        .groupby("customer_id", as_index=False)
        .first()[["customer_id", "order_month_period"]]
        .rename(columns={"order_month_period": "cohort_month_period"})
    )
    first_valid["cohort_month"] = first_valid["cohort_month_period"].astype(str)

    customer_activity = (
        valid.groupby(["customer_id", "order_month_period"], as_index=False)["id"]
        .count()
        .rename(columns={"id": "orders_count_valid"})
    )

    activity = customer_activity.merge(first_valid, on="customer_id", how="inner")
    activity["months_since_first"] = (
        activity["order_month_period"] - activity["cohort_month_period"]
    ).apply(lambda offset: offset.n)
    activity["is_retained_logo"] = activity["orders_count_valid"].gt(0).astype(int)

    cohort_customers = (
        first_valid.groupby("cohort_month", as_index=False)["customer_id"]
        .nunique()
        .rename(columns={"customer_id": "cohort_customers"})
    )

    m2 = activity[activity["months_since_first"] == 2].copy()
    m2_summary = (
        m2.groupby("cohort_month", as_index=False)["is_retained_logo"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "m2_retained_customers", "count": "m2_observed_customers"})
    )
    m2_summary = m2_summary.merge(cohort_customers, on="cohort_month", how="left")
    m2_summary["m2_logo_retention"] = (
        m2_summary["m2_retained_customers"] / m2_summary["cohort_customers"]
    ).round(4)
    m2_summary = m2_summary.sort_values("cohort_month", kind="stable")
    m2_summary.to_csv(SUMMARY_PATH, index=False)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(m2_summary["cohort_month"], m2_summary["m2_logo_retention"], color="#2B6CB0")
    ax.set_title("Shopify Mock Adapter Demo: M2 Logo Retention Baseline")
    ax.set_xlabel("cohort_month")
    ax.set_ylabel("m2_logo_retention")
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(m2_summary["m2_logo_retention"]):
        ax.text(idx, value + 0.02, f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    plt.close(fig)

    print(
        "shopify_demo=PASS "
        f"plot={to_relative(PLOT_PATH)} "
        f"summary={to_relative(SUMMARY_PATH)}"
    )


if __name__ == "__main__":
    main()
