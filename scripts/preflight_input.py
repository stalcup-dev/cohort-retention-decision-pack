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

from retention.io import COLUMN_ALIASES, resolve_input_path
from retention.clean import canonical_column_key


REQUIRED_KEYS = [
    "order",
    "sku",
    "description",
    "quantity",
    "order_ts",
    "unit_price",
    "customer_id",
]


def normalize_columns(df: pd.DataFrame) -> dict[str, str]:
    return {canonical_column_key(col): col for col in df.columns}


def resolve_columns(df: pd.DataFrame) -> dict[str, str]:
    normalized = normalize_columns(df)
    resolved: dict[str, str] = {}

    for key in REQUIRED_KEYS:
        found = None
        for alias in COLUMN_ALIASES[key]:
            alias_key = canonical_column_key(alias)
            if alias_key in normalized:
                found = normalized[alias_key]
                break
        if found is None:
            raise KeyError(f"Missing required column for {key}. Aliases: {COLUMN_ALIASES[key]}")
        resolved[key] = found

    # Country is optional.
    country_resolved = None
    for alias in COLUMN_ALIASES["country"]:
        alias_key = canonical_column_key(alias)
        if alias_key in normalized:
            country_resolved = normalized[alias_key]
            break
    resolved["country"] = country_resolved if country_resolved is not None else "(missing)"

    return resolved


def choose_excel_sheet(path: Path) -> tuple[str, pd.DataFrame, list[str], dict[str, list[str]]]:
    sheets = pd.read_excel(path, sheet_name=None)
    detected = list(sheets.keys())
    if not detected:
        raise ValueError("Workbook has no sheets.")

    missing_by_sheet: dict[str, list[str]] = {}
    for sheet_name, frame in sheets.items():
        normalized = normalize_columns(frame)
        missing = []
        for key in REQUIRED_KEYS:
            aliases = [canonical_column_key(a) for a in COLUMN_ALIASES[key]]
            if not any(a in normalized for a in aliases):
                missing.append(key)
        if not missing:
            return sheet_name, frame, detected, missing_by_sheet
        missing_by_sheet[sheet_name] = missing

    problems = "; ".join([f"{k}: missing {v}" for k, v in missing_by_sheet.items()])
    raise KeyError(f"No sheet has required columns. {problems}")


def load_preflight_frame(input_path: Path) -> tuple[pd.DataFrame, str, list[str], str]:
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(input_path)
        return frame, "CSV", ["CSV"], "CSV"

    if suffix in {".xlsx", ".xls"}:
        chosen_sheet, frame, detected_sheets, _ = choose_excel_sheet(input_path)
        return frame, chosen_sheet, detected_sheets, "EXCEL"

    raise ValueError(f"Unsupported input file type: {input_path}")


def build_preflight(input_path: Path) -> dict[str, Any]:
    frame, chosen_sheet, detected_sheets, source_type = load_preflight_frame(input_path)
    mapping = resolve_columns(frame)

    order_ts = pd.to_datetime(frame[mapping["order_ts"]], errors="coerce")
    null_customer_rate_pct = float(frame[mapping["customer_id"]].isna().mean() * 100.0)
    nat_invoice_date_pct = float(order_ts.isna().mean() * 100.0)

    min_date = order_ts.min()
    max_date = order_ts.max()

    payload: dict[str, Any] = {
        "input_path": str(input_path),
        "source_type": source_type,
        "detected_sheets": detected_sheets,
        "chosen_sheet": chosen_sheet,
        "resolved_columns": mapping,
        "row_count": int(len(frame)),
        "null_customer_rate_pct": null_customer_rate_pct,
        "nat_invoice_date_pct": nat_invoice_date_pct,
        "min_invoice_date": min_date.isoformat() if pd.notna(min_date) else None,
        "max_invoice_date": max_date.isoformat() if pd.notna(max_date) else None,
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight OnlineRetailII input")
    parser.add_argument("--input", type=Path, default=None, help="Input file path (.xlsx/.xls/.csv)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    resolved_input = resolve_input_path(REPO_ROOT / "data_raw", args.input)

    payload = build_preflight(resolved_input)

    out_dir = REPO_ROOT / "data_processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ingest_preflight.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="ascii")

    print(f"Input: {payload['input_path']}")
    print(f"Detected sheets: {payload['detected_sheets']}")
    print(f"Chosen sheet: {payload['chosen_sheet']}")
    print(f"Resolved columns: {json.dumps(payload['resolved_columns'])}")
    print(
        "Preflight stats: "
        f"row_count={payload['row_count']}, "
        f"null_customer_rate_pct={payload['null_customer_rate_pct']:.4f}%, "
        f"nat_invoice_date_pct={payload['nat_invoice_date_pct']:.4f}%, "
        f"min_date={payload['min_invoice_date']}, "
        f"max_date={payload['max_invoice_date']}"
    )
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
