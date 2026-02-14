from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retention.clean import canonical_column_key
from retention.policies import HORIZON_H, MIN_COHORT_N, OBSERVED_ONLY, RIGHT_CENSOR_MODE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate dataset scope and row reconciliation receipts")
    parser.add_argument("--input", type=Path, required=True, help="Path to OnlineRetailII.xlsx")
    return parser.parse_args()


def choose_invoice_date_column(frame: pd.DataFrame) -> str | None:
    aliases = ["InvoiceDate", "OrderDate", "Date"]
    normalized = {canonical_column_key(col): col for col in frame.columns}
    for alias in aliases:
        key = canonical_column_key(alias)
        if key in normalized:
            return normalized[key]
    return None


def read_processed_count(path: Path) -> int | None:
    if not path.exists():
        return None
    return int(pd.read_csv(path).shape[0])


def read_chart2_receipt(path: Path) -> tuple[int | None, int | None]:
    if not path.exists():
        return None, None
    frame = pd.read_csv(path)
    if frame.empty:
        return 0, None
    family_count = int(frame["first_product_family"].nunique()) if "first_product_family" in frame.columns else int(len(frame))
    min_n = int(frame["n_customers"].min()) if "n_customers" in frame.columns and len(frame) else None
    return family_count, min_n


def read_confound_receipt(path: Path) -> tuple[int | None, int | None]:
    if not path.exists():
        return None, None
    frame = pd.read_csv(path)
    if frame.empty:
        return 0, 0
    material_count = (
        int(frame["material_sensitivity"].sum())
        if "material_sensitivity" in frame.columns
        else None
    )
    return int(len(frame)), material_count


def approx_raw_profile(raw_sum_rows: int) -> str:
    if 1_000_000 <= raw_sum_rows <= 1_120_000:
        return "BOTH"
    if 500_000 <= raw_sum_rows <= 560_000:
        return "SINGLE"
    return "UNKNOWN"


def reconcile_status(raw_sum_rows: int, processed_order_lines_rows: int | None, n_sheets: int) -> str:
    processed = int(processed_order_lines_rows or 0)

    if processed > raw_sum_rows * 1.05:
        return "MISMATCH_JOIN_EXPLOSION_SUSPECTED"
    if processed < raw_sum_rows * 0.95:
        return "MISMATCH_UNDERCOUNT"

    profile = approx_raw_profile(raw_sum_rows)
    if profile == "BOTH" or n_sheets >= 2:
        return "OK_BOTH_SHEETS"
    return "OK_SINGLE_SHEET"


def main() -> None:
    args = parse_args()
    input_path = args.input
    if not input_path.is_absolute():
        input_path = REPO_ROOT / input_path

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    sheets = pd.read_excel(input_path, sheet_name=None)

    sheets_detected = list(sheets.keys())
    sheet_rows: dict[str, int] = {}
    sheet_date_ranges: dict[str, dict[str, Any]] = {}
    global_dates = []

    for sheet_name, frame in sheets.items():
        sheet_rows[sheet_name] = int(len(frame))
        date_col = choose_invoice_date_column(frame)
        if date_col is None:
            sheet_date_ranges[sheet_name] = {
                "date_column": None,
                "min_date": None,
                "max_date": None,
                "nat_pct": None,
            }
            continue

        parsed = pd.to_datetime(frame[date_col], errors="coerce")
        nat_pct = float(parsed.isna().mean() * 100.0) if len(parsed) else 0.0
        min_dt = parsed.min()
        max_dt = parsed.max()
        if pd.notna(min_dt):
            global_dates.append(min_dt)
        if pd.notna(max_dt):
            global_dates.append(max_dt)

        sheet_date_ranges[sheet_name] = {
            "date_column": date_col,
            "min_date": min_dt.isoformat() if pd.notna(min_dt) else None,
            "max_date": max_dt.isoformat() if pd.notna(max_dt) else None,
            "nat_pct": nat_pct,
        }

    raw_sum_rows = int(sum(sheet_rows.values()))
    if global_dates:
        raw_min_date = min(global_dates).isoformat()
        raw_max_date = max(global_dates).isoformat()
    else:
        raw_min_date = None
        raw_max_date = None

    dp = REPO_ROOT / "data_processed"
    dp.mkdir(parents=True, exist_ok=True)

    processed_order_lines_rows = read_processed_count(dp / "order_lines.csv")
    processed_orders_rows = read_processed_count(dp / "orders.csv")
    processed_customers_rows = read_processed_count(dp / "customers.csv")
    chart2_family_count, chart2_min_n_customers = read_chart2_receipt(dp / "chart2_family_scatter.csv")
    confound_rows, gate_c_material_count = read_confound_receipt(
        dp / "confound_m2_family_all_vs_retail.csv"
    )

    status = reconcile_status(raw_sum_rows, processed_order_lines_rows, len(sheets_detected))

    payload = {
        "input_path": str(input_path),
        "sheets_detected": sheets_detected,
        "sheet_rows": sheet_rows,
        "sheet_date_ranges": sheet_date_ranges,
        "raw_sum_rows": raw_sum_rows,
        "raw_min_date": raw_min_date,
        "raw_max_date": raw_max_date,
        "processed_order_lines_rows": processed_order_lines_rows,
        "processed_orders_rows": processed_orders_rows,
        "processed_customers_rows": processed_customers_rows,
        "chart2_family_count": chart2_family_count,
        "chart2_min_n_customers": chart2_min_n_customers,
        "chart2_observed_only": bool(OBSERVED_ONLY),
        "chart2_right_censored_missing": RIGHT_CENSOR_MODE == "missing_not_zero",
        "H": int(HORIZON_H),
        "MIN_COHORT_N": int(MIN_COHORT_N),
        "confound_rows": confound_rows,
        "gate_c_material_count": gate_c_material_count,
        "reconcile_status": status,
    }

    out_path = dp / "scope_receipts.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="ascii")

    # 8-line human-readable summary.
    print("Scope Receipts Summary")
    print(f"Input file: {input_path}")
    print(f"Sheets detected ({len(sheets_detected)}): {', '.join(sheets_detected)}")
    print(f"Sheet rows: {json.dumps(sheet_rows)}")
    print(f"Raw rows total: {raw_sum_rows}")
    print(f"Raw date range: {raw_min_date} -> {raw_max_date}")
    print(
        "Processed rows: "
        f"order_lines={processed_order_lines_rows}, orders={processed_orders_rows}, customers={processed_customers_rows}"
    )
    print(f"Reconcile status: {status} | wrote {out_path}")


if __name__ == "__main__":
    main()
