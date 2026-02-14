from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORDERS = REPO_ROOT / "public_demo" / "shopify_mock_orders.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "public_demo"

REQUIRED_ORDER_COLUMNS = [
    "id",
    "created_at",
    "customer_id",
    "financial_status",
    "cancelled_at",
    "lineitem_sku",
    "lineitem_name",
    "lineitem_quantity",
    "lineitem_price",
    "total_price",
]


def to_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def fail(message: str) -> None:
    raise SystemExit(f"ingest_shopify=FAIL {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Shopify CSV export into canonical demo tables.")
    parser.add_argument("--orders", type=Path, default=DEFAULT_ORDERS, help="Path to Shopify orders.csv")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory")
    return parser.parse_args()


def validate_required_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_ORDER_COLUMNS if column not in frame.columns]
    if missing:
        fail(f"missing_required_columns={missing}")


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    validated = frame.copy()

    validated["order_ts"] = pd.to_datetime(validated["created_at"], errors="coerce")
    bad_ts = int(validated["order_ts"].isna().sum())
    if bad_ts > 0:
        fail(f"bad_created_at_rows={bad_ts}")

    dup_count = int(validated["id"].astype(str).duplicated().sum())
    if dup_count > 0:
        fail(f"duplicate_order_ids={dup_count}")

    qty_num = pd.to_numeric(validated["lineitem_quantity"], errors="coerce")
    price_num = pd.to_numeric(validated["lineitem_price"], errors="coerce")
    non_numeric = int((qty_num.isna() | price_num.isna()).sum())
    if non_numeric > 0:
        fail(f"non_numeric_quantity_or_price_rows={non_numeric}")

    validated["lineitem_quantity"] = qty_num
    validated["lineitem_price"] = price_num

    total_price_num = pd.to_numeric(validated["total_price"], errors="coerce").fillna(0.0)
    non_positive_total_price_pct = float((total_price_num <= 0).mean() * 100.0)
    if non_positive_total_price_pct > 20.0:
        fail(f"non_positive_total_price_pct={non_positive_total_price_pct:.2f}")

    return validated


def build_canonical_order_lines(frame: pd.DataFrame) -> pd.DataFrame:
    canonical = pd.DataFrame()
    canonical["order_id"] = frame["id"].astype(str).str.strip().str.upper()
    canonical["order_ts"] = frame["order_ts"]
    canonical["customer_id"] = (
        frame["customer_id"].fillna("GUEST").astype(str).str.strip().replace("", "GUEST")
    )
    canonical["sku"] = frame["lineitem_sku"].fillna("").astype(str).str.strip().str.upper()
    canonical["description"] = frame["lineitem_name"].fillna("").astype(str).str.strip()
    canonical["quantity"] = frame["lineitem_quantity"].astype(float)
    canonical["unit_price"] = frame["lineitem_price"].astype(float)
    canonical["line_amount_gross"] = canonical["quantity"].clip(lower=0) * canonical["unit_price"].clip(lower=0)
    canonical["line_amount_net_proxy"] = canonical["quantity"] * canonical["unit_price"]

    status = frame["financial_status"].fillna("").astype(str).str.lower().str.strip()
    cancelled_flag = frame["cancelled_at"].fillna("").astype(str).str.strip().ne("")
    canonical["is_cancel_invoice"] = (cancelled_flag | status.isin(["refunded", "voided"])).astype(int)
    canonical["is_valid_purchase"] = (
        (canonical["line_amount_gross"] > 0) & (canonical["is_cancel_invoice"] == 0)
    ).astype(int)
    canonical["order_month"] = canonical["order_ts"].dt.to_period("M").astype(str)
    return canonical


def build_customer_month_activity(order_lines: pd.DataFrame) -> pd.DataFrame:
    valid_non_guest = order_lines[
        (order_lines["is_valid_purchase"] == 1) & (order_lines["customer_id"] != "GUEST")
    ].copy()
    if valid_non_guest.empty:
        fail("no_valid_non_guest_orders=1")

    valid_non_guest["order_month_period"] = valid_non_guest["order_ts"].dt.to_period("M")

    first_valid = (
        valid_non_guest.sort_values(["customer_id", "order_ts", "order_id"], kind="stable")
        .groupby("customer_id", as_index=False)
        .first()[["customer_id", "order_month_period"]]
        .rename(columns={"order_month_period": "cohort_month_period"})
    )
    first_valid["cohort_month"] = first_valid["cohort_month_period"].astype(str)

    customer_month = (
        valid_non_guest.groupby(["customer_id", "order_month_period"], as_index=False)["order_id"]
        .nunique()
        .rename(columns={"order_id": "orders_count_valid"})
    )
    customer_month["is_retained_logo"] = (customer_month["orders_count_valid"] > 0).astype(int)

    activity = customer_month.merge(first_valid, on="customer_id", how="inner")
    activity["months_since_first"] = (
        activity["order_month_period"] - activity["cohort_month_period"]
    ).apply(lambda offset: offset.n)
    activity["cohort_month"] = activity["cohort_month_period"].astype(str)
    activity["activity_month"] = activity["order_month_period"].astype(str)

    return activity[
        [
            "customer_id",
            "cohort_month",
            "activity_month",
            "months_since_first",
            "orders_count_valid",
            "is_retained_logo",
        ]
    ].sort_values(["cohort_month", "customer_id", "months_since_first"], kind="stable")


def build_m2_summary(activity: pd.DataFrame) -> pd.DataFrame:
    cohort_size = (
        activity[activity["months_since_first"] == 0]
        .groupby("cohort_month", as_index=False)["customer_id"]
        .nunique()
        .rename(columns={"customer_id": "n_customers_m0"})
    )
    m2 = activity[activity["months_since_first"] == 2]
    m2_logo = (
        m2.groupby("cohort_month", as_index=False)["is_retained_logo"]
        .mean()
        .rename(columns={"is_retained_logo": "m2_logo_retention"})
    )

    summary = cohort_size.merge(m2_logo, on="cohort_month", how="left")
    summary["m2_logo_retention"] = summary["m2_logo_retention"].fillna(0.0)
    summary = summary.sort_values("cohort_month", kind="stable")
    return summary


def write_plot(summary: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(summary["cohort_month"], summary["m2_logo_retention"], color="#2B6CB0")
    ax.set_title("Shopify Adapter Demo: M2 Logo Retention Baseline")
    ax.set_xlabel("cohort_month")
    ax.set_ylabel("m2_logo_retention")
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(summary["m2_logo_retention"]):
        ax.text(idx, value + 0.02, f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    orders_path = args.orders if args.orders.is_absolute() else (REPO_ROOT / args.orders)
    out_dir = args.out_dir if args.out_dir.is_absolute() else (REPO_ROOT / args.out_dir)

    if not orders_path.exists():
        fail(f"orders_file_not_found={orders_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    orders = pd.read_csv(orders_path)
    validate_required_columns(orders)
    validated = validate_frame(orders)

    canonical = build_canonical_order_lines(validated)
    activity = build_customer_month_activity(canonical)
    summary = build_m2_summary(activity)

    canonical_path = out_dir / "shopify_order_lines_canonical.csv"
    activity_path = out_dir / "shopify_customer_month_activity.csv"
    summary_path = out_dir / "shopify_demo_summary.csv"
    plot_path = out_dir / "shopify_demo_output.png"

    canonical.to_csv(canonical_path, index=False)
    activity.to_csv(activity_path, index=False)
    summary.to_csv(summary_path, index=False)
    write_plot(summary, plot_path)

    print(
        "ingest_shopify=PASS "
        f"canonical={to_rel(canonical_path)} "
        f"activity={to_rel(activity_path)} "
        f"summary={to_rel(summary_path)} "
        f"plot={to_rel(plot_path)}"
    )


if __name__ == "__main__":
    main()
