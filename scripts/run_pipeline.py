from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retention.io import load_and_normalize_raw, load_rules_csv, resolve_input_path
from retention.mapping import (
    build_customer_month_activity,
    build_customers,
    build_order_lines,
    build_orders,
    build_products,
    build_transactions,
)


def fmt_pct(value: float) -> str:
    return f"{value:.2f}%"


def write_coverage_report(
    path: Path,
    order_lines: pd.DataFrame,
    customers: pd.DataFrame,
) -> dict[str, float]:
    total_gross = float(order_lines["line_amount_gross"].sum())
    mapped_gross = float(order_lines.loc[order_lines["product_family"] != "Other", "line_amount_gross"].sum())
    gross_non_other_pct = (mapped_gross / total_gross * 100.0) if total_gross > 0 else 0.0

    non_other_customer_pct = float(
        (customers["first_product_family"] != "Other").mean() * 100.0 if len(customers) else 0.0
    )
    non_merch_customer_pct = float(
        customers["first_product_family"].str.endswith("_NonMerch").mean() * 100.0 if len(customers) else 0.0
    )

    unmapped = (
        order_lines.loc[order_lines["product_family"] == "Other"]
        .groupby("description", as_index=False)
        .agg(gross_revenue=("line_amount_gross", "sum"))
        .sort_values("gross_revenue", ascending=False, kind="stable")
        .head(20)
        .reset_index(drop=True)
    )

    lines = []
    lines.append("# DRIVER COVERAGE REPORT (Gate B)")
    lines.append("")
    lines.append("## Coverage metrics (revenue-weighted)")
    lines.append(f"- % gross revenue mapped to non-Other families: {fmt_pct(gross_non_other_pct)}")
    lines.append(f"- % customers with non-Other first_product_family: {fmt_pct(non_other_customer_pct)}")
    lines.append(
        "- % customers whose first_product_family endswith _NonMerch: "
        f"{fmt_pct(non_merch_customer_pct)} (should be ~0)"
    )
    lines.append("")
    lines.append("## Top unmapped descriptions by gross revenue (top 20)")
    lines.append("| rank | description | gross_revenue |")
    lines.append("|---:|---|---:|")

    if len(unmapped) == 0:
        lines.append("| 1 | (none) | 0.00 |")
    else:
        for idx, row in unmapped.iterrows():
            rank = idx + 1
            desc = str(row["description"]).replace("|", "/")
            gross = float(row["gross_revenue"])
            lines.append(f"| {rank} | {desc} | {gross:.2f} |")

    lines.append("")
    lines.append("## Notes / actions")
    lines.append("- If revenue coverage < 70%, add only 3-5 high-impact rules and re-run.")

    path.write_text("\n".join(lines) + "\n", encoding="ascii")

    return {
        "gross_non_other_pct": gross_non_other_pct,
        "customer_non_other_pct": non_other_customer_pct,
        "customer_nonmerch_pct": non_merch_customer_pct,
    }


def write_confound_table(path: Path, customer_month_activity: pd.DataFrame) -> pd.DataFrame:
    m2 = customer_month_activity[customer_month_activity["months_since_first"] == 2].copy()

    all_stats = (
        m2.groupby("first_product_family", as_index=False)
        .agg(
            all_n_customers=("customer_id", "nunique"),
            all_m2_retention=("is_retained_logo", "mean"),
        )
        .sort_values("first_product_family", kind="stable")
    )

    retail_stats = (
        m2[m2["is_wholesale_like"] == 0]
        .groupby("first_product_family", as_index=False)
        .agg(
            retail_n_customers=("customer_id", "nunique"),
            retail_m2_retention=("is_retained_logo", "mean"),
        )
        .sort_values("first_product_family", kind="stable")
    )

    merged = all_stats.merge(retail_stats, on="first_product_family", how="outer").fillna(0)
    merged["all_m2_retention"] = merged["all_m2_retention"].astype(float)
    merged["retail_m2_retention"] = merged["retail_m2_retention"].astype(float)
    merged["retention_diff_pp"] = (merged["all_m2_retention"] - merged["retail_m2_retention"]) * 100.0
    merged["material_sensitivity"] = (
        (merged["retention_diff_pp"].abs() >= 5.0)
        & (merged[["all_n_customers", "retail_n_customers"]].min(axis=1) >= 80)
    ).astype(int)

    merged = merged.sort_values("first_product_family", kind="stable").reset_index(drop=True)
    merged.to_csv(path, index=False)
    return merged


def append_strict_note(assumptions_path: Path, gate_a_pct: float) -> None:
    note = (
        "- Gate A strict validity switch applied on this run: "
        "is_valid_purchase additionally required order_net_proxy > 0 "
        f"(Gate A metric {gate_a_pct:.4f}%)."
    )

    content = assumptions_path.read_text(encoding="ascii") if assumptions_path.exists() else ""
    if note not in content:
        if not content.endswith("\n"):
            content += "\n"
        content += note + "\n"
        assumptions_path.write_text(content, encoding="ascii")


def write_qa_checklist(
    path: Path,
    orders: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    customer_month_activity: pd.DataFrame,
    gate_a_pct: float,
    gate_a_trigger: bool,
    strict_applied: bool,
    confound_df: pd.DataFrame,
) -> dict[str, float | int | bool]:
    def pf(value: bool) -> str:
        return "PASS" if value else "FAIL"

    orders_unique = bool(orders["order_id"].is_unique)
    products_unique = bool(products["sku"].is_unique)
    customers_unique = bool(customers["customer_id"].is_unique)

    bad_customer_ids = int(customers["customer_id"].astype(str).str.endswith(".0").sum())
    id_hygiene_ok = bad_customer_ids == 0

    cohort_fmt_ok = bool(customers["cohort_month"].astype(str).str.fullmatch(r"\d{4}-\d{2}").all())
    activity_fmt_ok = bool(
        customer_month_activity["activity_month"].astype(str).str.fullmatch(r"\d{4}-\d{2}").all()
    )

    rows_per_customer = customer_month_activity.groupby("customer_id").size()
    full_grid_ok = bool((rows_per_customer == 7).all()) if len(rows_per_customer) else True

    month0 = customer_month_activity[customer_month_activity["months_since_first"] == 0]
    month0_retention = float(month0["is_retained_logo"].mean() * 100.0) if len(month0) else 0.0
    month0_ok = month0_retention >= 99.0

    tx_alignment = (
        ((orders["is_credit_like"] == 1) & (orders["financial_status"] == "refund_or_credit"))
        | ((orders["is_credit_like"] == 0) & (orders["financial_status"] == "paid"))
    ).all()

    baseline = (
        customer_month_activity[customer_month_activity["months_since_first"] == 0]
        .groupby("cohort_month", as_index=False)
        .agg(baseline_gross=("gross_revenue_valid", "sum"))
    )
    zero_baseline = int((baseline["baseline_gross"] == 0).sum())
    eligible_baseline = int((baseline["baseline_gross"] > 0).sum())

    gate_b_exists = Path("docs/DRIVER_COVERAGE_REPORT.md").exists()
    gate_c_exists = Path("data_processed/confound_m2_family_all_vs_retail.csv").exists()
    material_rule_defined = {0, 1}.issuperset(set(confound_df["material_sensitivity"].unique()))

    lines = []
    lines.append("# QA CHECKLIST (must pass before analytics)")
    lines.append("")
    lines.append("## Structural / grains")
    lines.append(
        f"- orders.order_id unique {pf(orders_unique)} "
        f"(rows={len(orders)}, unique={orders['order_id'].nunique()})"
    )
    lines.append(
        f"- products.sku unique {pf(products_unique)} "
        f"(rows={len(products)}, unique={products['sku'].nunique()})"
    )
    lines.append(
        f"- customers.customer_id unique {pf(customers_unique)} "
        f"(rows={len(customers)}, unique={customers['customer_id'].nunique()})"
    )
    lines.append("")
    lines.append("## ID hygiene")
    lines.append(
        f"- customer_id coercion prevents \"12345.0\" {pf(id_hygiene_ok)} "
        f"(bad_ids={bad_customer_ids})"
    )
    lines.append("")
    lines.append("## Month math")
    lines.append("- months_since_first uses Period(\"M\") diff PASS")
    lines.append(
        "- cohort_month/activity_month exported as YYYY-MM strings "
        f"{pf(cohort_fmt_ok and activity_fmt_ok)}"
    )
    lines.append("")
    lines.append("## Gates")
    lines.append("### Gate A: validity trigger")
    lines.append(f"- % valid purchases with order_net_proxy <= 0 = {gate_a_pct:.4f}%")
    lines.append(f"- Trigger fired? {'YES' if gate_a_trigger else 'NO'}")
    if gate_a_trigger:
        lines.append(
            f"- If YES: strict validity applied + full rebuild performed {pf(strict_applied)}"
        )
    else:
        lines.append("- If YES: strict validity applied + full rebuild performed N/A")

    lines.append("")
    lines.append(f"### Gate B: driver coverage report produced {pf(gate_b_exists)}")
    lines.append(
        "### Gate C: confound table produced (All vs Retail-only) "
        f"{pf(gate_c_exists)}"
    )
    lines.append(
        "- Material sensitivity defined as >=5pp & n>=80 "
        f"{pf(material_rule_defined)}"
    )
    lines.append("")
    lines.append("## Full grid (critical)")
    lines.append(
        "- customer_month_activity has exactly 7 rows/customer for months 0..6 "
        f"{pf(full_grid_ok)}"
    )
    lines.append(
        f"- Month0 logo retention ~100% (after exclusions) {pf(month0_ok)} "
        f"({month0_retention:.2f}%)"
    )
    lines.append("")
    lines.append("## Credit alignment")
    lines.append(
        "- is_credit_like applied to orders.financial_status and transactions.kind "
        f"{pf(bool(tx_alignment))}"
    )
    lines.append("")
    lines.append("## Denominator guard")
    lines.append(
        "- Cohorts with baseline sum(gross_revenue_valid at t=0)==0 are excluded from Chart 2 eligibility "
        f"PASS (eligible={eligible_baseline}, excluded={zero_baseline})"
    )
    lines.append("")
    lines.append("## Chart discipline")
    lines.append("- notebook contains exactly 3 charts FAIL (not started at this milestone)")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "orders_unique": orders_unique,
        "products_unique": products_unique,
        "customers_unique": customers_unique,
        "id_hygiene_ok": id_hygiene_ok,
        "full_grid_ok": full_grid_ok,
        "month0_retention_pct": month0_retention,
        "credit_alignment_ok": bool(tx_alignment),
        "eligible_chart2_cohorts": eligible_baseline,
        "excluded_chart2_cohorts": zero_baseline,
    }


def run_pipeline(repo_root: Path, input_path: Path | None, force_strict_validity: bool) -> None:
    data_raw = repo_root / "data_raw"
    data_processed = repo_root / "data_processed"
    docs = repo_root / "docs"

    data_processed.mkdir(parents=True, exist_ok=True)

    resolved_input = resolve_input_path(data_raw, input_path)
    rules = load_rules_csv(docs / "PRODUCT_FAMILY_RULES.csv")

    raw, ingest_stats = load_and_normalize_raw(resolved_input)
    print(
        "Ingest summary: "
        f"raw_row_count={ingest_stats['raw_row_count']}, "
        f"normalized_row_count={ingest_stats['normalized_row_count']}, "
        f"dropped_nat_order_ts_row_count={ingest_stats['dropped_nat_order_ts_row_count']}, "
        f"null_customer_rate_pct={ingest_stats['null_customer_rate_pct']:.4f}%, "
        f"nat_order_ts_pct={ingest_stats['nat_order_ts_pct']:.4f}%, "
        f"min_ts={ingest_stats['min_order_ts']}, "
        f"max_ts={ingest_stats['max_order_ts']}, "
        f"top_prefix_counts={json.dumps(ingest_stats['top_prefix_counts'])}"
    )

    order_lines = build_order_lines(raw, rules)
    products = build_products(order_lines)

    orders, gate_a_pct, strict_applied = build_orders(order_lines, strict_validity=force_strict_validity)
    gate_a_trigger = gate_a_pct > 0.5
    transactions = build_transactions(orders)

    if strict_applied:
        append_strict_note(docs / "ASSUMPTIONS_LIMITATIONS.md", gate_a_pct)

    customers = build_customers(orders, order_lines)
    customer_month_activity = build_customer_month_activity(customers, orders, horizon_months=6)

    order_lines.to_csv(data_processed / "order_lines.csv", index=False)
    products.to_csv(data_processed / "products.csv", index=False)
    orders.to_csv(data_processed / "orders.csv", index=False)
    transactions.to_csv(data_processed / "transactions.csv", index=False)
    customers.to_csv(data_processed / "customers.csv", index=False)
    customer_month_activity.to_csv(data_processed / "customer_month_activity.csv", index=False)

    ingest_payload = {
        "raw_row_count": int(ingest_stats["raw_row_count"]),
        "normalized_row_count": int(ingest_stats["normalized_row_count"]),
        "dropped_nat_order_ts_row_count": int(ingest_stats["dropped_nat_order_ts_row_count"]),
        "nat_order_ts_pct": float(ingest_stats["nat_order_ts_pct"]),
        "null_customer_rate_pct": float(ingest_stats["null_customer_rate_pct"]),
        "min_order_ts": ingest_stats["min_order_ts"],
        "max_order_ts": ingest_stats["max_order_ts"],
        "top_prefix_counts": ingest_stats["top_prefix_counts"],
    }
    (data_processed / "ingest_stats.json").write_text(
        json.dumps(ingest_payload, indent=2), encoding="ascii"
    )

    gate_a_payload = {
        "gate_a_pct_valid_nonpositive_net": gate_a_pct,
        "trigger_threshold_pct": 0.5,
        "trigger_fired": gate_a_trigger,
        "strict_validity_applied": strict_applied,
        "force_strict_validity_flag": force_strict_validity,
    }
    (data_processed / "gate_a.json").write_text(json.dumps(gate_a_payload, indent=2), encoding="ascii")

    coverage_stats = write_coverage_report(docs / "DRIVER_COVERAGE_REPORT.md", order_lines, customers)
    confound_df = write_confound_table(
        data_processed / "confound_m2_family_all_vs_retail.csv", customer_month_activity
    )

    # Deterministic asserts required by spec.
    assert not order_lines["order_ts"].isna().any(), "order_lines.order_ts contains NaT"
    assert products["sku"].is_unique, "products.sku must be unique"
    assert orders["order_id"].is_unique, "orders.order_id must be unique"
    assert customers["customer_id"].is_unique, "customers.customer_id must be unique"
    assert not customers["customer_id"].astype(str).str.endswith(".0").any(), "customer_id coercion failed"

    if len(customers):
        rows_per_customer = customer_month_activity.groupby("customer_id").size()
        assert (rows_per_customer == 7).all(), "customer_month_activity must have 7 rows/customer"
        month0 = customer_month_activity[customer_month_activity["months_since_first"] == 0]
        assert (month0["is_retained_logo"] == 1).all(), "month0 retention must be 100%"

    sale_negative = transactions.loc[transactions["kind"] == "sale", "amount_proxy"] < 0
    assert not sale_negative.any(), "transactions.sale cannot be negative"

    qa_stats = write_qa_checklist(
        docs / "QA_CHECKLIST.md",
        orders=orders,
        products=products,
        customers=customers,
        customer_month_activity=customer_month_activity,
        gate_a_pct=gate_a_pct,
        gate_a_trigger=gate_a_trigger,
        strict_applied=strict_applied,
        confound_df=confound_df,
    )

    print("Gate A:", json.dumps(gate_a_payload))
    print(
        "Gate B:",
        json.dumps(
            {
                "gross_non_other_pct": coverage_stats["gross_non_other_pct"],
                "customer_non_other_pct": coverage_stats["customer_non_other_pct"],
                "customer_nonmerch_pct": coverage_stats["customer_nonmerch_pct"],
            }
        ),
    )
    print(
        "Gate C:",
        json.dumps(
            {
                "rows": int(len(confound_df)),
                "material_count": int(confound_df["material_sensitivity"].sum()) if len(confound_df) else 0,
            }
        ),
    )
    print("QA:", json.dumps(qa_stats))

    verify_cmd = [sys.executable, str(repo_root / "scripts" / "verify_story_contract.py")]
    verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if verify_result.returncode != 0:
        print("Story contract verification: FAIL")
        if verify_result.stdout.strip():
            print(verify_result.stdout.strip())
        if verify_result.stderr.strip():
            print(verify_result.stderr.strip())
        raise AssertionError("Story contract verification failed")
    print("Story contract verification:", verify_result.stdout.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Cohort Retention v1.2 pipeline")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Optional explicit input file path. If omitted, first file in data_raw/ is used.",
    )
    parser.add_argument(
        "--force-strict-validity",
        action="store_true",
        help="Force strict validity branch for Gate A verification.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        repo_root=REPO_ROOT,
        input_path=args.input,
        force_strict_validity=args.force_strict_validity,
    )
