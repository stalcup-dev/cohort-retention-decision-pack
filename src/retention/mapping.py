from __future__ import annotations

import re

import numpy as np
import pandas as pd


def map_product_families(descriptions: pd.Series, rules: pd.DataFrame) -> pd.Series:
    desc_upper = descriptions.fillna("UNKNOWN").astype(str).str.upper()
    families = pd.Series(index=desc_upper.index, data=None, dtype="object")

    for _, row in rules.sort_values("priority", kind="stable").iterrows():
        mask_open = families.isna()
        if not mask_open.any():
            break
        pattern = str(row["pattern"])
        family_label = str(row["family_label"])
        matched = desc_upper.str.contains(pattern, regex=True, flags=re.IGNORECASE, na=False)
        mask = mask_open & matched
        families.loc[mask] = family_label

    families = families.fillna("Other")
    return families


def build_order_lines(raw_df: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    lines = raw_df.copy()

    lines["unit_price_pos"] = lines["unit_price"].clip(lower=0)
    lines["qty_pos"] = lines["quantity"].clip(lower=0)
    lines["line_amount_gross"] = lines["qty_pos"] * lines["unit_price_pos"]
    lines["line_amount_net_proxy"] = lines["quantity"] * lines["unit_price"]

    lines["is_cancel_invoice"] = lines["order_id"].str.startswith("C").astype(int)
    lines["is_return_line"] = ((lines["quantity"] < 0) | (lines["is_cancel_invoice"] == 1)).astype(int)

    lines["product_family"] = map_product_families(lines["description"], rules)

    ordered_cols = [
        "order_id",
        "order_ts",
        "customer_id",
        "sku",
        "description",
        "country",
        "quantity",
        "unit_price",
        "qty_pos",
        "unit_price_pos",
        "line_amount_gross",
        "line_amount_net_proxy",
        "is_cancel_invoice",
        "is_return_line",
        "product_family",
    ]

    return lines[ordered_cols].sort_values(["order_ts", "order_id", "sku"], kind="stable")


def build_products(order_lines: pd.DataFrame) -> pd.DataFrame:
    agg = (
        order_lines.groupby(["sku", "description", "product_family"], as_index=False)
        .agg(
            gross_revenue=("line_amount_gross", "sum"),
            line_count=("order_id", "count"),
        )
        .sort_values(
            ["sku", "gross_revenue", "line_count", "description", "product_family"],
            ascending=[True, False, False, True, True],
            kind="stable",
        )
    )

    products = agg.drop_duplicates(subset=["sku"], keep="first").copy()
    products = products[["sku", "description", "product_family"]].reset_index(drop=True)
    return products


def build_orders(order_lines: pd.DataFrame, strict_validity: bool) -> tuple[pd.DataFrame, float, bool]:
    grouped = (
        order_lines.groupby("order_id", as_index=False)
        .agg(
            order_ts=("order_ts", "min"),
            customer_id=("customer_id", "first"),
            country=("country", "first"),
            items_count=("qty_pos", "sum"),
            order_gross=("line_amount_gross", "sum"),
            order_net_proxy=("line_amount_net_proxy", "sum"),
            is_cancel_invoice=("is_cancel_invoice", "max"),
        )
        .sort_values(["order_ts", "order_id"], kind="stable")
        .reset_index(drop=True)
    )

    grouped["is_credit_like"] = (
        (grouped["is_cancel_invoice"] == 1) | (grouped["order_net_proxy"] < 0)
    ).astype(int)
    grouped["financial_status"] = np.where(
        grouped["is_credit_like"] == 1, "refund_or_credit", "paid"
    )

    grouped["is_valid_purchase_default"] = (
        (grouped["order_gross"] > 0) & (grouped["is_cancel_invoice"] == 0)
    )

    default_valid = grouped[grouped["is_valid_purchase_default"]].copy()
    if len(default_valid) == 0:
        gate_a_pct = 0.0
    else:
        gate_a_pct = float((default_valid["order_net_proxy"] <= 0).mean() * 100.0)

    gate_a_trigger = gate_a_pct > 0.5
    strict_applied = strict_validity or gate_a_trigger

    if strict_applied:
        grouped["is_valid_purchase"] = (
            grouped["is_valid_purchase_default"] & (grouped["order_net_proxy"] > 0)
        )
    else:
        grouped["is_valid_purchase"] = grouped["is_valid_purchase_default"]

    grouped["is_valid_purchase"] = grouped["is_valid_purchase"].astype(int)

    return grouped, gate_a_pct, strict_applied


def build_transactions(orders: pd.DataFrame) -> pd.DataFrame:
    tx = orders[["order_id", "order_ts", "customer_id", "is_credit_like", "order_net_proxy"]].copy()
    tx["kind"] = np.where(tx["is_credit_like"] == 1, "credit_or_refund", "sale")
    tx["amount_proxy"] = np.where(
        tx["kind"] == "credit_or_refund",
        tx["order_net_proxy"].abs(),
        tx["order_net_proxy"].clip(lower=0),
    )
    tx["transaction_id"] = tx["order_id"]
    tx = tx[["transaction_id", "order_id", "order_ts", "customer_id", "kind", "amount_proxy"]]
    tx = tx.sort_values(["order_ts", "transaction_id"], kind="stable").reset_index(drop=True)
    return tx


def choose_first_product_family(first_order_lines: pd.DataFrame) -> pd.Series:
    if first_order_lines.empty:
        return pd.Series(dtype="object")

    family_agg = (
        first_order_lines.groupby(["customer_id", "product_family"], as_index=False)
        .agg(
            gross_revenue=("line_amount_gross", "sum"),
            items_count=("qty_pos", "sum"),
        )
        .sort_values(["customer_id", "product_family"], kind="stable")
    )

    selected_rows = []
    for customer_id, grp in family_agg.groupby("customer_id", sort=False):
        merch = grp[~grp["product_family"].str.endswith("_NonMerch")].copy()
        if merch.empty:
            selected_rows.append((customer_id, "Other"))
            continue
        top = merch.sort_values(
            ["gross_revenue", "items_count", "product_family"],
            ascending=[False, False, True],
            kind="stable",
        ).iloc[0]
        selected_rows.append((customer_id, str(top["product_family"])))

    return pd.Series(
        {customer_id: family for customer_id, family in selected_rows},
        name="first_product_family",
        dtype="object",
    )


def build_customers(orders: pd.DataFrame, order_lines: pd.DataFrame) -> pd.DataFrame:
    valid = orders[(orders["is_valid_purchase"] == 1) & (orders["customer_id"] != "GUEST")].copy()
    valid = valid.sort_values(["customer_id", "order_ts", "order_id"], kind="stable")

    first_orders = valid.drop_duplicates(subset=["customer_id"], keep="first").copy()
    first_orders = first_orders[
        ["customer_id", "order_id", "order_ts", "items_count", "order_gross"]
    ].rename(
        columns={
            "order_id": "first_order_id",
            "order_ts": "first_order_ts",
            "items_count": "first_order_items_count",
            "order_gross": "first_order_gross",
        }
    )

    first_orders["cohort_month"] = first_orders["first_order_ts"].dt.to_period("M").astype(str)

    if len(first_orders) > 0:
        items_thr = max(float(np.percentile(first_orders["first_order_items_count"], 99)), 100.0)
        gross_thr = max(float(np.percentile(first_orders["first_order_gross"], 99)), 1000.0)
    else:
        items_thr = 100.0
        gross_thr = 1000.0

    first_orders["is_wholesale_like"] = (
        (first_orders["first_order_items_count"] >= items_thr)
        | (first_orders["first_order_gross"] >= gross_thr)
    ).astype(int)

    first_order_lines = order_lines.merge(
        first_orders[["customer_id", "first_order_id"]],
        left_on=["customer_id", "order_id"],
        right_on=["customer_id", "first_order_id"],
        how="inner",
    )

    first_family = choose_first_product_family(first_order_lines)
    first_orders = first_orders.merge(
        first_family.rename_axis("customer_id").reset_index(),
        on="customer_id",
        how="left",
    )
    first_orders["first_product_family"] = first_orders["first_product_family"].fillna("Other")

    out = first_orders[
        [
            "customer_id",
            "first_order_id",
            "first_order_ts",
            "cohort_month",
            "first_order_items_count",
            "first_order_gross",
            "is_wholesale_like",
            "first_product_family",
        ]
    ].sort_values(["first_order_ts", "customer_id"], kind="stable")

    return out.reset_index(drop=True)


def build_customer_month_activity(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    horizon_months: int = 6,
) -> pd.DataFrame:
    if customers.empty:
        return pd.DataFrame(
            columns=[
                "customer_id",
                "cohort_month",
                "activity_month",
                "months_since_first",
                "orders_count_valid",
                "gross_revenue_valid",
                "net_revenue_proxy_total",
                "is_retained_logo",
                "first_product_family",
                "is_wholesale_like",
            ]
        )

    base = customers[["customer_id", "cohort_month", "first_product_family", "is_wholesale_like"]].copy()
    base["cohort_period"] = pd.PeriodIndex(base["cohort_month"], freq="M")

    repeated = base.loc[base.index.repeat(horizon_months + 1)].copy().reset_index(drop=True)
    repeated["months_since_first"] = np.tile(np.arange(horizon_months + 1), len(base))
    repeated["activity_period"] = repeated["cohort_period"] + repeated["months_since_first"]
    repeated["activity_month"] = repeated["activity_period"].astype(str)

    orders_scope = orders.merge(
        customers[["customer_id", "cohort_month"]], on="customer_id", how="inner"
    )
    orders_scope["order_period"] = orders_scope["order_ts"].dt.to_period("M")
    orders_scope["cohort_period"] = pd.PeriodIndex(orders_scope["cohort_month"], freq="M")
    period_delta = orders_scope["order_period"] - orders_scope["cohort_period"]
    if pd.api.types.is_integer_dtype(period_delta):
        orders_scope["months_since_first"] = period_delta.astype(int)
    else:
        # Pandas may return DateOffset-like deltas (e.g., MonthEnd); use integer month count.
        orders_scope["months_since_first"] = period_delta.map(
            lambda x: int(x.n) if hasattr(x, "n") else int(x)
        )

    orders_scope = orders_scope[
        (orders_scope["months_since_first"] >= 0)
        & (orders_scope["months_since_first"] <= horizon_months)
    ].copy()

    valid_month = (
        orders_scope[orders_scope["is_valid_purchase"] == 1]
        .groupby(["customer_id", "months_since_first"], as_index=False)
        .agg(
            orders_count_valid=("order_id", "nunique"),
            gross_revenue_valid=("order_gross", "sum"),
        )
    )

    total_month = (
        orders_scope.groupby(["customer_id", "months_since_first"], as_index=False)
        .agg(net_revenue_proxy_total=("order_net_proxy", "sum"))
    )

    activity = repeated.merge(
        valid_month,
        on=["customer_id", "months_since_first"],
        how="left",
    ).merge(
        total_month,
        on=["customer_id", "months_since_first"],
        how="left",
    )

    for col in ["orders_count_valid", "gross_revenue_valid", "net_revenue_proxy_total"]:
        activity[col] = activity[col].fillna(0)

    activity["orders_count_valid"] = activity["orders_count_valid"].astype(int)
    activity["is_retained_logo"] = (activity["orders_count_valid"] > 0).astype(int)

    out = activity[
        [
            "customer_id",
            "cohort_month",
            "activity_month",
            "months_since_first",
            "orders_count_valid",
            "gross_revenue_valid",
            "net_revenue_proxy_total",
            "is_retained_logo",
            "first_product_family",
            "is_wholesale_like",
        ]
    ].sort_values(["customer_id", "months_since_first"], kind="stable")

    return out.reset_index(drop=True)
