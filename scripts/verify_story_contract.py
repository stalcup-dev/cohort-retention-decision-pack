from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retention.policies import HORIZON_H


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify story notebook/HTML chart contract")
    parser.add_argument(
        "--notebook",
        type=Path,
        default=Path("notebooks/cohort_retention_story.ipynb"),
        help="Story notebook path",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=Path("exports/cohort_retention_story.html"),
        help="Story HTML export path",
    )
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (REPO_ROOT / path)


def verify(notebook_path: Path, html_path: Path) -> None:
    if not notebook_path.exists():
        raise FileNotFoundError(f"Missing story notebook: {notebook_path}")
    if not html_path.exists():
        raise FileNotFoundError(f"Missing story HTML: {html_path}")
    curves_path = REPO_ROOT / "data_processed" / "chart2_net_proxy_curves.csv"
    if not curves_path.exists():
        raise FileNotFoundError(f"Missing chart2 curves table: {curves_path}")

    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    chart_cells = [
        c
        for c in nb.get("cells", [])
        if c.get("cell_type") == "code" and "chart" in c.get("metadata", {}).get("tags", [])
    ]
    story_chart_cells = len(chart_cells)
    if story_chart_cells != 3:
        raise AssertionError(f"story_chart_cells must be 3, found {story_chart_cells}")

    markdown_text = "\n".join(
        "".join(c.get("source", []))
        for c in nb.get("cells", [])
        if c.get("cell_type") == "markdown"
    )
    md_lower = markdown_text.lower()
    if "family impact scatter" in md_lower:
        raise AssertionError("Contract violation: notebook contains 'Family Impact Scatter'")
    if not ("chart 1" in md_lower and "heatmap" in md_lower):
        raise AssertionError("Missing required Chart 1 heatmap heading text")
    if "chart 2: net retention proxy curves" not in md_lower:
        raise AssertionError("Missing required Chart 2 net retention proxy curves heading text")
    if not ("chart 3" in md_lower and ("m2 retention by first_product_family" in md_lower or "m2 retention by family" in md_lower)):
        raise AssertionError("Missing required Chart 3 family retention heading text")

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    html_lower = html.lower()
    if "family impact scatter" in html_lower:
        raise AssertionError("Contract violation: story HTML contains 'Family Impact Scatter'")
    heading_pat = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", flags=re.IGNORECASE | re.DOTALL)

    def _clean_heading_text(raw: str) -> str:
        text = re.sub(r"<[^>]+>", "", raw)
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
        return re.sub(r"\s+", " ", text).strip()

    heading_matches = list(heading_pat.finditer(html))
    chart2_heading_matches = [
        m
        for m in heading_matches
        if _clean_heading_text(m.group(2))
        .lower()
        .startswith("chart 2: net retention proxy curves (3 cohorts max)")
    ]
    if len(chart2_heading_matches) != 1:
        raise AssertionError(
            "Contract violation: expected exactly one Chart 2 heading element, "
            f"found {len(chart2_heading_matches)}"
        )

    chart2_match = chart2_heading_matches[0]
    next_h2 = re.search(r"<h2[^>]*>", html[chart2_match.end() :], flags=re.IGNORECASE)
    region_end = chart2_match.end() + next_h2.start() if next_h2 else len(html)
    chart2_region = html[chart2_match.end() : region_end]
    chart2_region_lower = chart2_region.lower()

    selection_note_count = len(re.findall(r"\bselection note\b", chart2_region, flags=re.IGNORECASE))
    if selection_note_count != 1:
        raise AssertionError(
            "Contract violation: expected exactly one Selection Note in Chart 2 region, "
            f"found {selection_note_count}"
        )
    selected_table_count = len(
        re.findall(r"selected cohorts table \(min_cohort_n=", chart2_region_lower)
    )
    if selected_table_count != 1:
        raise AssertionError(
            "Contract violation: expected exactly one selected cohorts table label in Chart 2 region, "
            f"found {selected_table_count}"
        )
    if "used_fallback=" not in chart2_region_lower:
        raise AssertionError("Contract violation: Chart 2 region missing used_fallback visibility")
    if "plot_floor_pass" not in chart2_region_lower:
        raise AssertionError("Contract violation: Chart 2 region missing plot_floor_pass column")
    if "artifact_manifest_timestamp=" not in html_lower:
        raise AssertionError("Contract violation: story HTML missing artifact manifest timestamp marker")
    code_cell_headers = re.findall(r"<div class=\"jp-Cell jp-CodeCell[^\"]*\"", html)
    visible_code_cells = [cell for cell in code_cell_headers if "jp-mod-noInput" not in cell]
    if visible_code_cells:
        raise AssertionError("Story HTML appears to contain visible code input blocks")

    curves = pd.read_csv(curves_path)
    required_cols = {
        "cohort_month",
        "months_since_first",
        "n_customers_m0",
        "denom_month0_gross_valid",
        "net_revenue_proxy_total",
        "net_retention_proxy",
        "is_observed",
        "eligible_cohort",
        "selected_for_plot",
    }
    missing_cols = required_cols - set(curves.columns)
    if missing_cols:
        raise AssertionError(f"chart2 curves missing columns: {sorted(missing_cols)}")

    selected = curves[curves["selected_for_plot"].astype(bool)].copy()
    selected_count = int(selected["cohort_month"].nunique())
    if selected_count > 3:
        raise AssertionError(f"selected_for_plot cohort count > 3 ({selected_count})")
    if selected_count < 1:
        raise AssertionError("selected_for_plot cohort count must be >= 1")
    if not bool(selected["eligible_cohort"].astype(bool).all()):
        raise AssertionError("selected_for_plot contains non-eligible cohorts")

    for cohort, grp in selected.groupby("cohort_month", sort=False):
        months = sorted(grp["months_since_first"].astype(int).unique().tolist())
        if months != list(range(HORIZON_H + 1)):
            raise AssertionError(
                f"selected cohort missing horizon rows: cohort={cohort}, months={months}"
            )

    print(
        "verify_story_contract=PASS "
        f"(story_chart_cells={story_chart_cells}, titles=Chart1/2/3, html_no_code_blocks=True, selected_cohorts={selected_count})"
    )


def main() -> None:
    args = parse_args()
    verify(resolve(args.notebook), resolve(args.html))


if __name__ == "__main__":
    main()
