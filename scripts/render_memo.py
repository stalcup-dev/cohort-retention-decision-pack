from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retention.policies import MIN_COHORT_N

CHART3_PATH = REPO_ROOT / "data_processed" / "chart3_m2_by_family.csv"
CHART2_CURVES_PATH = REPO_ROOT / "data_processed" / "chart2_net_proxy_curves.csv"
SCOPE_PATH = REPO_ROOT / "data_processed" / "scope_receipts.json"
GATE_A_PATH = REPO_ROOT / "data_processed" / "gate_a.json"
CONFOUND_PATH = REPO_ROOT / "data_processed" / "confound_m2_family_all_vs_retail.csv"
APPENDIX_PATH = REPO_ROOT / "data_processed" / "appendix_top_products_in_chart3_targets.csv"
OUT_PATH = REPO_ROOT / "docs" / "DECISION_MEMO_1PAGE.md"


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def main() -> None:
    for path in [CHART3_PATH, CHART2_CURVES_PATH, SCOPE_PATH, GATE_A_PATH, CONFOUND_PATH, APPENDIX_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Missing required source file: {path}")

    chart3 = pd.read_csv(CHART3_PATH)
    curves = pd.read_csv(CHART2_CURVES_PATH)
    scope = json.loads(SCOPE_PATH.read_text(encoding="ascii"))
    gate_a = json.loads(GATE_A_PATH.read_text(encoding="ascii"))
    confound = pd.read_csv(CONFOUND_PATH)
    appendix = pd.read_csv(APPENDIX_PATH)

    if chart3.empty:
        raise AssertionError("chart3_m2_by_family.csv is empty")
    if curves.empty:
        raise AssertionError("chart2_net_proxy_curves.csv is empty")

    ranked = chart3.copy()
    ranked = ranked[ranked["family_group"].astype(str) != "Other"].copy()
    ranked = ranked[ranked["n_customers"] >= MIN_COHORT_N].copy()
    ranked = ranked.sort_values(
        ["m2_logo_retention", "m2_net_proxy_retention", "n_customers", "family_group"],
        ascending=[True, True, False, True],
        kind="stable",
    ).reset_index(drop=True)
    targets = ranked.head(3).copy()
    if len(targets) < 3:
        raise AssertionError("Need at least 3 target families from chart3_m2_by_family.csv")
    targets["rank_priority"] = range(1, len(targets) + 1)
    target_names = targets["family_group"].astype(str).tolist()

    # Curve pattern note from selected cohorts only.
    curves_local = curves.copy()
    curves_local["selected_for_plot"] = curves_local["selected_for_plot"].astype(bool)
    curves_local["eligible_cohort"] = curves_local["eligible_cohort"].astype(bool)
    curves_local["is_observed"] = curves_local["is_observed"].astype(bool)
    plot_curves = curves_local[curves_local["selected_for_plot"] & curves_local["eligible_cohort"]].copy()
    plot_curves.loc[~plot_curves["is_observed"], "net_retention_proxy"] = pd.NA

    selected_cohorts = sorted(plot_curves["cohort_month"].astype(str).unique().tolist())
    selected_from_scope = sorted([str(x) for x in scope.get("chart2_selected_cohorts", [])])
    if selected_from_scope and selected_cohorts != selected_from_scope:
        raise AssertionError(
            f"Chart2 selected cohorts mismatch between curves and scope receipts: "
            f"curves={selected_cohorts}, scope={selected_from_scope}"
        )
    chart2_policy = scope.get("chart2_policy", {})
    policy_min_n = chart2_policy.get("MIN_COHORT_N", MIN_COHORT_N)
    policy_plot_n = chart2_policy.get("MIN_PLOT_COHORT_N", None)
    policy_h = chart2_policy.get("H", None)
    used_fallback = scope.get("chart2_used_fallback")
    plot_pool_count = scope.get("chart2_plot_pool_count")
    m2_vals = pd.to_numeric(
        plot_curves.loc[plot_curves["months_since_first"] == 2, "net_retention_proxy"],
        errors="coerce",
    ).dropna()
    m6_vals = pd.to_numeric(
        plot_curves.loc[plot_curves["months_since_first"] == 6, "net_retention_proxy"],
        errors="coerce",
    ).dropna()
    curve_m2_med = float(m2_vals.median()) if len(m2_vals) else None
    curve_m6_med = float(m6_vals.median()) if len(m6_vals) else None

    total_n = int(chart3["n_customers"].sum())
    other_n = int(chart3.loc[chart3["family_group"].astype(str) == "Other", "n_customers"].sum())
    non_other_share = ((total_n - other_n) / total_n) if total_n > 0 else 0.0

    confound_material_count = (
        int(confound["material_sensitivity"].sum())
        if "material_sensitivity" in confound.columns and len(confound)
        else 0
    )

    target_lines: list[str] = []
    target_table_rows: list[str] = []
    for _, row in targets.iterrows():
        gap_pp = (float(row["m2_net_proxy_retention"]) - float(row["m2_logo_retention"])) * 100.0
        target_lines.append(
            f"- `#{int(row['rank_priority'])} {row['family_group']}`: "
            f"M2 logo {pct(float(row['m2_logo_retention']))}, "
            f"M2 net proxy {pct(float(row['m2_net_proxy_retention']))}, "
            f"n={int(row['n_customers'])}"
        )
        target_table_rows.append(
            "| "
            f"{row['family_group']} | "
            f"{int(row['n_customers'])} | "
            f"{float(row['m2_logo_retention']):.4f} | "
            f"{float(row['m2_net_proxy_retention']):.4f} | "
            f"{gap_pp:.1f} |"
        )

    worst_family = str(targets.iloc[0]["family_group"])
    ranked_with_gap = targets.copy()
    ranked_with_gap["net_minus_logo"] = (
        ranked_with_gap["m2_net_proxy_retention"] - ranked_with_gap["m2_logo_retention"]
    )
    refund_drag_family = str(
        ranked_with_gap.sort_values(["net_minus_logo", "n_customers"], ascending=[True, False], kind="stable")
        .iloc[0]["family_group"]
    )

    sku_callouts: list[str] = []
    for _, fam_row in targets.iterrows():
        fam = str(fam_row["family_group"])
        fam_df = appendix[appendix["first_product_family"].astype(str) == fam].copy()
        if fam_df.empty:
            sku_callouts.append(f"- `{fam}`: appendix table has no eligible SKU rows under current policy.")
            continue
        fam_df = fam_df.sort_values(
            ["delta_net_proxy_vs_family_pp", "m0_gross_valid", "sku"],
            ascending=[True, False, True],
            kind="stable",
        )
        drag = fam_df.head(2)["sku"].astype(str).tolist()
        lift_df = fam_df.sort_values(
            ["delta_net_proxy_vs_family_pp", "m0_gross_valid", "sku"],
            ascending=[False, False, True],
            kind="stable",
        )
        lift_sku = str(lift_df.iloc[0]["sku"])
        sku_callouts.append(
            f"- `{fam}`: test drag SKUs `{drag[0]}`"
            + (f", `{drag[1]}`" if len(drag) > 1 else "")
            + f"; optional lift SKU `{lift_sku}`."
        )

    curve_note = (
        f"- Chart 2 curve pattern (selected cohorts: {', '.join(selected_cohorts)}): "
        f"median net proxy at M2={pct(curve_m2_med) if curve_m2_med is not None else 'NA'}, "
        f"M6={pct(curve_m6_med) if curve_m6_med is not None else 'NA'}."
    )

    text = "\n".join(
        [
            "# Decision Memo (1 Page)",
            "",
            "## Decision / Recommendation",
            (
                "Prioritize retention experiments on the three weakest first_product_family groups at M2 "
                "(selected from Chart 3), then use Chart 2 curves to calibrate value-retention expectations."
            ),
            f"Initial targets: `{target_names[0]}`, `{target_names[1]}`, `{target_names[2]}`.",
            "Success criteria (decision thresholds): logo `+X pp`, net proxy `+Y pp`, and gap improvement toward `>= 0 pp`.",
            "Guardrails: margin proxy not worse than `-Z%`, no cohort quality deterioration, and no adverse credit-like rate shift.",
            "",
            "Chart 1 = who returns; Chart 2 = how much value remains over months; Chart 3 = where to act.",
            "",
            "## North Star Metric",
            "M2 logo retention (cohort-weighted): the customer-weighted share of cohort customers with at least one valid purchase in month 2.",
            "",
            "## Single High-Leverage Insight",
            (
                f"The largest descriptive underperformance at M2 is concentrated in `{target_names[0]}`, "
                f"`{target_names[1]}`, and `{target_names[2]}`; this is where early repeat and value-quality "
                "risk converge most clearly in the current baseline."
            ),
            "",
            "## Impact Definition",
            "- Success means the target families clear logo `+X pp`, net proxy `+Y pp`, and improve net-minus-logo gap toward `>= 0 pp`.",
            "- Baseline reference remains the current Chart 3 snapshot in this memo (descriptive, not causal).",
            "",
            "## Tradeoffs",
            f"- Focus vs breadth: prioritizing `{target_names[0]}`, `{target_names[1]}`, `{target_names[2]}` increases execution speed but defers lower-volume families.",
            "- Speed vs certainty: rapid test cycles improve learning velocity but do not replace full causal readout windows.",
            "- Seasonality confound: family-level differences can partially reflect acquisition-window mix and timing effects.",
            "- Margin risk: aggressive retention levers can lift repeat while harming economics if guardrails are not enforced.",
            "",
            "## What we'd do next (2 weeks)",
            "- Week 1: lock hypotheses, finalize experiment design, and confirm thresholds plus guardrails with owners.",
            "- Week 2: launch controlled tests, run first operational readout, and issue scale/pause/iterate decisions with next M2 checkpoint dates.",
            "",
            "## Top 3 Target Families",
            *target_lines,
            "",
            "Targets sourced from `chart3_m2_by_family.csv` using lowest M2 logo retention (tie-break: lower M2 net proxy).",
            "| family_group | n_customers | m2_logo_retention | m2_net_proxy_retention | gap_pp |",
            "|---|---:|---:|---:|---:|",
            *target_table_rows,
            "",
            "## Success criteria",
            "- Raise M2 logo retention in each target family by `+X pp` vs control.",
            "- Improve M2 net proxy retention in each target family by `+Y pp` vs control.",
            "- Close net-minus-logo gap (`gap_pp`) toward `>= 0 pp` for at least 2 of 3 targets.",
            "",
            "## Guardrails",
            "- Guardrails: margin proxy not worse than `-Z%`, no decline in cohort size quality (`n_customers`), and no adverse shift in credit-like rate.",
            "",
            "## Why Now",
            (
                f"- Family-universe context (chart3 table): non-Other customer share = "
                f"{non_other_share * 100:.1f}% (Other share = {(1 - non_other_share) * 100:.1f}%)."
            ),
            curve_note,
            (
                "- Chart 2 metric definition: "
                "net_retention_proxy(c,t) = net_revenue_proxy_total(c,t) / denom_month0_gross_valid(c); "
                "denom guard requires denom_month0_gross_valid > 0."
            ),
            "- Chart 2 cohort selection (source: scope_receipts.json):",
            f"  selected_cohorts={selected_cohorts}",
            f"  used_fallback={used_fallback}, plot_pool_count={plot_pool_count}",
            f"  MIN_COHORT_N={policy_min_n}, MIN_PLOT_COHORT_N={policy_plot_n}, H={policy_h}",
            (
                f"- Gate C confound note: material sensitivity count = {confound_material_count} "
                "(All vs Retail-only family M2 comparison)."
            ),
            (
                f"- Gate A validity guardrail: {gate_a['gate_a_pct_valid_nonpositive_net']:.4f}% "
                f"valid purchases with non-positive net; trigger_fired={gate_a['trigger_fired']}."
            ),
            "",
            "## Plays",
            f"1. Replenishment nudge play: start with `{worst_family}`-like profiles; measure M2 logo lift and holdout gap.",
            f"2. Returns/credits mitigation play: start with `{refund_drag_family}`-like profiles; measure net proxy stabilization at M2.",
            "",
            "## What To Test First (SKU Callouts)",
            "Source: `data_processed/appendix_top_products_in_chart3_targets.csv`.",
            *sku_callouts,
            "",
            "Directional not causal: this memo is for prioritization and experiment design, not causal attribution.",
            "NonMerch exclusion: `*_NonMerch` families are excluded from first_product_family assignment competition by design.",
            "",
        ]
    )

    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
