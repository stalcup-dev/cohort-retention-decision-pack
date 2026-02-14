from __future__ import annotations

import json
import re
from pathlib import Path
import sys
import hashlib

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retention.policies import MIN_COHORT_N, MIN_SKU_N, TOPK_SKUS_PER_FAMILY

SCOPE_PATH = REPO_ROOT / "data_processed" / "scope_receipts.json"
GATE_A_PATH = REPO_ROOT / "data_processed" / "gate_a.json"
COVERAGE_PATH = REPO_ROOT / "docs" / "DRIVER_COVERAGE_REPORT.md"
CHART3_PATH = REPO_ROOT / "data_processed" / "chart3_m2_by_family.csv"
CHART2_CANDIDATES_PATH = REPO_ROOT / "data_processed" / "chart2_selection_candidates.csv"
MANIFEST_PATH = REPO_ROOT / "data_processed" / "artifact_manifest.json"
APPENDIX_PATH = REPO_ROOT / "data_processed" / "appendix_top_products_in_chart3_targets.csv"
MEMO_PATH = REPO_ROOT / "docs" / "DECISION_MEMO_1PAGE.md"


def parse_pct(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return float(match.group(1))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    for path in [SCOPE_PATH, GATE_A_PATH, COVERAGE_PATH, CHART3_PATH, MEMO_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Missing required receipt: {path}")

    scope = json.loads(SCOPE_PATH.read_text(encoding="ascii"))
    gate_a = json.loads(GATE_A_PATH.read_text(encoding="ascii"))
    coverage_text = COVERAGE_PATH.read_text(encoding="utf-8")
    chart3 = pd.read_csv(CHART3_PATH)

    status = str(scope.get("reconcile_status", ""))
    if status.startswith("MISMATCH_"):
        print(f"STOP: reconcile_status={status}")
        raise SystemExit(1)

    required_chart2_receipt_fields = [
        "chart2_plot_pool_count",
        "chart2_used_fallback",
        "chart2_selected_cohorts",
        "chart2_selected_min_n0",
        "chart2_policy",
    ]
    missing_chart2_receipt_fields = [
        key for key in required_chart2_receipt_fields if key not in scope
    ]
    if missing_chart2_receipt_fields:
        print(
            "STOP: scope_receipts missing Chart2 selection fields: "
            + ", ".join(missing_chart2_receipt_fields)
        )
        raise SystemExit(1)

    chart2_policy = scope.get("chart2_policy", {})
    required_policy_fields = [
        "MIN_COHORT_N",
        "MIN_PLOT_COHORT_N",
        "H",
        "RIGHT_CENSOR_MODE",
        "OBSERVED_ONLY",
    ]
    missing_policy_fields = [
        key for key in required_policy_fields if key not in chart2_policy
    ]
    if missing_policy_fields:
        print(
            "STOP: scope_receipts.chart2_policy missing fields: "
            + ", ".join(missing_policy_fields)
        )
        raise SystemExit(1)

    selected_cohorts = scope.get("chart2_selected_cohorts", [])
    if not isinstance(selected_cohorts, list):
        print("STOP: chart2_selected_cohorts must be a list")
        raise SystemExit(1)
    selected_count = int(len(selected_cohorts))
    if selected_count == 0 or selected_count > 3:
        print(f"STOP: chart2_selected_count out of contract bounds ({selected_count})")
        raise SystemExit(1)
    selected_count_receipt = int(scope.get("chart2_selected_count", selected_count))

    gate_b_gross = parse_pct(
        r"% gross revenue mapped to non-Other families:\s*([0-9]+\.?[0-9]*)%",
        coverage_text,
    )
    gate_b_customer = parse_pct(
        r"% customers with non-Other first_product_family:\s*([0-9]+\.?[0-9]*)%",
        coverage_text,
    )

    print("Evidence Pack")
    print(
        f"Sheets ingested: {', '.join(scope.get('sheets_detected', []))} | "
        f"raw_sum_rows={scope.get('raw_sum_rows')}"
    )
    print(f"Raw date range: {scope.get('raw_min_date')} -> {scope.get('raw_max_date')}")
    print(
        f"order_lines rows={scope.get('processed_order_lines_rows')} | "
        f"reconcile_status={status}"
    )
    print(
        "Gate A: "
        f"pct_nonpositive_net={gate_a.get('gate_a_pct_valid_nonpositive_net'):.4f}% | "
        f"trigger_fired={gate_a.get('trigger_fired')}"
    )
    print(
        "Gate B: "
        f"gross_non_other_pct={gate_b_gross if gate_b_gross is not None else 'NA'}% | "
        f"customer_non_other_pct={gate_b_customer if gate_b_customer is not None else 'NA'}%"
    )
    print(
        "Gate C: "
        f"confound_rows={scope.get('confound_rows')} | "
        f"material_count={scope.get('gate_c_material_count')}"
    )
    print(
        "Chart 2 selection: bottom/mid/top by M2 logo retention among eligible cohorts"
    )
    print(
        "Chart 2 plot pool: "
        f"plot_pool_count={scope.get('chart2_plot_pool_count')}, "
        f"MIN_PLOT_COHORT_N={chart2_policy.get('MIN_PLOT_COHORT_N')}, "
        f"used_fallback={scope.get('chart2_used_fallback')}"
    )
    print(
        "Chart 2 selected cohorts: "
        f"{selected_cohorts} (min_n0={scope.get('chart2_selected_min_n0')})"
    )
    print(
        "Chart 2 policy: "
        f"observed_only={chart2_policy.get('OBSERVED_ONLY')}, "
        f"right_censored_missing={chart2_policy.get('RIGHT_CENSOR_MODE') == 'missing_not_zero'}, "
        f"MIN_COHORT_N={chart2_policy.get('MIN_COHORT_N')}, H={chart2_policy.get('H')}"
    )

    failures: list[str] = []
    if not CHART2_CANDIDATES_PATH.exists():
        print(f"Chart2 candidates file: FAIL (missing {CHART2_CANDIDATES_PATH})")
        raise SystemExit(1)

    candidates = pd.read_csv(CHART2_CANDIDATES_PATH)
    required_candidate_cols = {
        "cohort_month",
        "n0",
        "denom_month0_gross_valid",
        "m2_logo_retention",
        "plot_floor_pass",
        "eligible_cohort",
        "selected_for_plot",
        "rank_logo_m2",
    }
    missing_candidate_cols = required_candidate_cols - set(candidates.columns)
    if missing_candidate_cols:
        print(f"STOP: chart2 candidates missing columns: {sorted(missing_candidate_cols)}")
        raise SystemExit(1)

    candidates["selected_for_plot"] = candidates["selected_for_plot"].astype(bool)
    candidates["plot_floor_pass"] = candidates["plot_floor_pass"].astype(bool)
    selected_rows_with_reason = candidates.loc[
        candidates["selected_for_plot"], ["cohort_month", "selection_reason"]
    ].copy()
    selected_rows_with_reason["cohort_month"] = selected_rows_with_reason["cohort_month"].astype(str)
    selected_rows_with_reason = selected_rows_with_reason.sort_values(
        ["cohort_month"], ascending=[True], kind="stable"
    )
    selected_with_reason = selected_rows_with_reason.to_dict(orient="records")
    candidates_selected = sorted(
        selected_rows_with_reason["cohort_month"].astype(str).unique().tolist()
    )
    selected_count_candidates = int(len(candidates_selected))
    used_fallback = bool(scope.get("chart2_used_fallback"))

    check_candidate_count = selected_count_candidates == selected_count_receipt
    if used_fallback:
        check_plot_floor = True
    else:
        check_plot_floor = bool(
            candidates.loc[candidates["selected_for_plot"], "plot_floor_pass"].all()
        )
    check_selected_match = candidates_selected == sorted(selected_cohorts)

    print(
        "Chart2 candidates file: "
        f"{'PASS' if len(candidates) > 0 else 'FAIL'} "
        f"(rows={len(candidates)}, selected={candidates_selected})"
    )
    print(
        "Chart2 candidates selected-count coherence: "
        f"{'PASS' if check_candidate_count else 'FAIL'} "
        f"(candidates={selected_count_candidates}, receipts={selected_count_receipt})"
    )
    print(
        "Chart2 candidates floor rule coherence: "
        f"{'PASS' if check_plot_floor else 'FAIL'} "
        f"(used_fallback={used_fallback})"
    )
    print(
        "Chart2 candidates selected-list coherence: "
        f"{'PASS' if check_selected_match else 'FAIL'} "
        f"(candidates={candidates_selected}, receipts={sorted(selected_cohorts)})"
    )
    print(
        "Chart2 selected reasons: "
        + ", ".join(
            f"{item['cohort_month']}:{item['selection_reason']}" for item in selected_with_reason
        )
    )
    if len(candidates) == 0:
        failures.append("chart2 candidates file empty")
    if not check_candidate_count:
        failures.append("chart2 selected count mismatch (candidates vs receipts)")
    if not check_plot_floor:
        failures.append("chart2 selected cohorts violate plot floor while used_fallback=False")
    if not check_selected_match:
        failures.append("chart2 selected cohorts mismatch (candidates vs receipts)")

    chart3_targets = (
        chart3[chart3["family_group"].astype(str) != "Other"]
        .loc[lambda d: d["n_customers"] >= MIN_COHORT_N]
        .sort_values(
            ["m2_logo_retention", "m2_net_proxy_retention", "n_customers", "family_group"],
            ascending=[True, True, False, True],
            kind="stable",
        )
        .head(3)["family_group"]
        .astype(str)
        .tolist()
    )
    memo_text = MEMO_PATH.read_text(encoding="utf-8")
    memo_has_selection_line = "selected_cohorts=" in memo_text
    print(
        "Memo chart2-selection line: "
        f"{'PASS' if memo_has_selection_line else 'FAIL'}"
    )
    if not memo_has_selection_line:
        failures.append("memo missing selected_cohorts line")
    memo_matches = re.findall(r"- `#\d+\s+([^`]+)`:", memo_text)
    target_families = memo_matches if memo_matches else chart3_targets
    appendix_exists = APPENDIX_PATH.exists()
    if appendix_exists:
        appendix = pd.read_csv(APPENDIX_PATH)
        appendix_rows = int(len(appendix))
        appendix_min_n = int(appendix["n_customers_m0"].min()) if appendix_rows else None
        appendix_max_n = int(appendix["n_customers_m0"].max()) if appendix_rows else None
        fam_set = set(appendix["first_product_family"].astype(str).unique().tolist()) if appendix_rows else set()
    else:
        appendix_rows = 0
        appendix_min_n = None
        appendix_max_n = None
        fam_set = set()

    check_exists = appendix_exists
    check_rows = appendix_rows <= (3 * TOPK_SKUS_PER_FAMILY)
    check_min_n = (appendix_min_n is not None and appendix_min_n >= MIN_SKU_N) if appendix_exists and appendix_rows else False
    check_family_set = fam_set == set(target_families)

    print(
        "Appendix integrity (file+rows): "
        f"{'PASS' if check_exists and check_rows else 'FAIL'} "
        f"(exists={appendix_exists}, rows={appendix_rows}, max_allowed={3 * TOPK_SKUS_PER_FAMILY})"
    )
    print(
        "Appendix integrity (n_customers_m0 min/max): "
        f"{'PASS' if check_min_n else 'FAIL'} "
        f"(min={appendix_min_n}, max={appendix_max_n}, policy_min={MIN_SKU_N})"
    )
    print(
        "Appendix family-set match: "
        f"{'PASS' if check_family_set else 'FAIL'} "
        f"(appendix={sorted(fam_set)}, memo_targets={sorted(target_families)})"
    )

    if not check_exists:
        failures.append("appendix file missing")
    if not check_rows:
        failures.append("appendix row count exceeds 3*TOPK")
    if not check_min_n:
        failures.append("appendix n_customers_m0 violates MIN_SKU_N")
    if not check_family_set:
        failures.append("appendix family set != chart2 top3 families")

    print("Reviewer artifact: exports/cohort_retention_story.html")
    print("Reviewer artifact: docs/DECISION_MEMO_1PAGE.md")
    print("Reviewer artifact: docs/QA_CHECKLIST.md")
    print("Reviewer artifact: docs/DRIVER_COVERAGE_REPORT.md")

    if not MANIFEST_PATH.exists():
        failures.append("artifact_manifest.json missing")
    else:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="ascii"))
        manifest_rows = manifest.get("artifacts", [])
        required_paths = {
            "data_processed/chart2_net_proxy_curves.csv",
            "data_processed/chart2_selection_candidates.csv",
            "data_processed/scope_receipts.json",
            "docs/DECISION_MEMO_1PAGE.md",
            "exports/cohort_retention_story.html",
        }
        manifest_paths = {row.get("path") for row in manifest_rows if isinstance(row, dict)}
        manifest_path_ok = required_paths.issubset(manifest_paths)
        manifest_hash_ok = True
        for row in manifest_rows:
            if not isinstance(row, dict):
                manifest_hash_ok = False
                break
            rel = row.get("path")
            expected = row.get("sha256")
            if not isinstance(rel, str) or not isinstance(expected, str):
                manifest_hash_ok = False
                break
            path = REPO_ROOT / rel
            if not path.exists() or sha256_file(path) != expected:
                manifest_hash_ok = False
                break
        print(
            "Artifact manifest summary: "
            f"{'PASS' if manifest_path_ok and manifest_hash_ok else 'FAIL'} "
            f"(build_timestamp_utc={manifest.get('build_timestamp_utc')}, "
            f"artifacts={len(manifest_rows)})"
        )
        if not manifest_path_ok:
            failures.append("artifact manifest missing required paths")
        if not manifest_hash_ok:
            failures.append("artifact manifest hash mismatch")

    if failures:
        print("STOP: evidence checks failed -> " + "; ".join(failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
