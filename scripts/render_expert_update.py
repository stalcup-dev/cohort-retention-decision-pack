from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = REPO_ROOT / "data_processed" / "scope_receipts.json"
EXPERT_PATH = REPO_ROOT / "docs" / "EXPERT_UPDATE.md"
BLOCKED_PATH = REPO_ROOT / "docs" / "EXPERT_UPDATE_BLOCKED.md"


def pct_delta(raw: int, processed: int) -> float:
    if raw == 0:
        return 0.0
    return (processed - raw) / raw * 100.0


def main() -> None:
    if not SCOPE_PATH.exists():
        raise FileNotFoundError(f"Missing scope receipts: {SCOPE_PATH}")

    scope = json.loads(SCOPE_PATH.read_text(encoding="ascii"))
    status = str(scope.get("reconcile_status", ""))

    raw_sum = int(scope.get("raw_sum_rows", 0) or 0)
    processed_order_lines = scope.get("processed_order_lines_rows")
    processed_order_lines = int(processed_order_lines) if processed_order_lines is not None else 0
    delta = pct_delta(raw_sum, processed_order_lines)

    sheets = scope.get("sheets_detected", [])
    sheets_line = ", ".join(sheets) if sheets else "(none)"

    if status.startswith("MISMATCH_"):
        blocked = [
            "# EXPERT UPDATE BLOCKED",
            "",
            "Scope reconciliation failed. Expert update generation stopped.",
            "",
            f"- reconcile_status: {status}",
            f"- raw_sum_rows: {raw_sum}",
            f"- processed_order_lines_rows: {processed_order_lines}",
            f"- delta_pct: {delta:.2f}% (expected within +/-1% for pass)",
            f"- sheets_ingested: {sheets_line}",
            "",
            "Resolve scope contradiction before publishing expert narrative.",
        ]
        BLOCKED_PATH.write_text("\n".join(blocked) + "\n", encoding="utf-8")
        print("STOP: scope mismatch")
        print(f"Wrote {BLOCKED_PATH}")
        raise SystemExit(1)

    expert = [
        "# EXPERT UPDATE",
        "",
        f"- Sheets ingested: {sheets_line}",
        f"- Raw total rows (Excel): {raw_sum}",
        f"- Processed order_lines rows: {processed_order_lines}",
        f"- Line-item sanity: order_lines rows ~= raw_sum_rows +/-1% (delta={delta:.2f}%)",
        f"- Raw date span: {scope.get('raw_min_date')} to {scope.get('raw_max_date')}",
        f"- Processed orders rows: {scope.get('processed_orders_rows')}",
        f"- Processed customers rows: {scope.get('processed_customers_rows')}",
        "- Driver (frozen): first_product_family (wholesale-like remains QA-only)",
        "- Appendix: drilldown-only for activation (no new driver/segmentation/charts)",
        (
            "- Chart 2 contract: Net retention proxy curves (3 cohorts max), "
            "formula net_retention_proxy(c,t)=net_revenue_proxy_total(c,t)/denom_month0_gross_valid(c), "
            "denominator guard required."
        ),
        (
            "- Chart 2 policy: observed-only="
            f"{scope.get('chart2_observed_only')}, "
            f"right-censored missing={scope.get('chart2_right_censored_missing')}, "
            f"n>={scope.get('MIN_COHORT_N')}, H={scope.get('H')}."
        ),
        (
            "- Chart 2 cohort selection (source: scope_receipts.json): "
            f"selected_cohorts={scope.get('chart2_selected_cohorts', [])}, "
            f"used_fallback={scope.get('chart2_used_fallback')}, "
            f"plot_pool_count={scope.get('chart2_plot_pool_count')}"
        ),
        (
            "- Chart 2 selection policy params: "
            f"MIN_COHORT_N={scope.get('chart2_policy', {}).get('MIN_COHORT_N')}, "
            f"MIN_PLOT_COHORT_N={scope.get('chart2_policy', {}).get('MIN_PLOT_COHORT_N')}, "
            f"H={scope.get('chart2_policy', {}).get('H')}"
        ),
        "- H=6 grid exists; right-censored months are masked in chart (NA), not treated as 0.",
        f"- Reconcile status: {status}",
    ]
    EXPERT_PATH.write_text("\n".join(expert) + "\n", encoding="utf-8")
    print(f"Wrote {EXPERT_PATH}")


if __name__ == "__main__":
    main()
