from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from .clean import (
    canonical_column_key,
    coerce_customer_id,
    coerce_order_id,
    coerce_sku,
    safe_to_datetime,
    safe_to_numeric,
)


COLUMN_ALIASES = {
    "order": ["InvoiceNo", "Invoice", "OrderID", "Order"],
    "sku": ["StockCode", "SKU", "ItemCode"],
    "description": ["Description", "ProductDescription", "ItemDescription"],
    "quantity": ["Quantity", "Qty"],
    "order_ts": ["InvoiceDate", "OrderDate", "Date"],
    "unit_price": ["UnitPrice", "Price", "Unit Price"],
    "customer_id": ["CustomerID", "Customer ID", "CustomerId", "Customer"],
    "country": ["Country"],
}


def resolve_input_path(data_raw_dir: Path, explicit_path: Optional[Path] = None) -> Path:
    if explicit_path is not None:
        return explicit_path

    candidates = sorted(
        [
            p
            for p in data_raw_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls"}
        ]
    )
    if not candidates:
        raise FileNotFoundError("No .csv/.xlsx/.xls file found under data_raw/")
    return candidates[0]


def _load_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None)
        frames = []
        for sheet_name, frame in sheets.items():
            local = frame.copy()
            local["__sheet_name"] = sheet_name
            frames.append(local)
        return pd.concat(frames, ignore_index=True)
    raise ValueError(f"Unsupported input file type: {path}")


def _choose_column(df: pd.DataFrame, aliases: list[str]) -> str:
    normalized = {canonical_column_key(col): col for col in df.columns}
    for alias in aliases:
        key = canonical_column_key(alias)
        if key in normalized:
            return normalized[key]
    raise KeyError(f"Missing required column from aliases: {aliases}")


def load_and_normalize_raw(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = _load_table(path)

    col_order = _choose_column(raw, COLUMN_ALIASES["order"])
    col_sku = _choose_column(raw, COLUMN_ALIASES["sku"])
    col_desc = _choose_column(raw, COLUMN_ALIASES["description"])
    col_qty = _choose_column(raw, COLUMN_ALIASES["quantity"])
    col_ts = _choose_column(raw, COLUMN_ALIASES["order_ts"])
    col_price = _choose_column(raw, COLUMN_ALIASES["unit_price"])
    col_customer = _choose_column(raw, COLUMN_ALIASES["customer_id"])

    col_country = None
    try:
        col_country = _choose_column(raw, COLUMN_ALIASES["country"])
    except KeyError:
        col_country = None

    null_customer_rate = float(raw[col_customer].isna().mean() * 100.0)

    normalized = pd.DataFrame(
        {
            "order_id": raw[col_order].map(coerce_order_id),
            "sku": raw[col_sku].map(coerce_sku),
            "description": raw[col_desc].fillna("UNKNOWN").astype(str).str.strip(),
            "quantity": safe_to_numeric(raw[col_qty]),
            "unit_price": safe_to_numeric(raw[col_price]),
            "order_ts": safe_to_datetime(raw[col_ts]),
            "customer_id": raw[col_customer].map(coerce_customer_id),
        }
    )

    if col_country is not None:
        normalized["country"] = raw[col_country].fillna("UNKNOWN").astype(str).str.strip()
    else:
        normalized["country"] = "UNKNOWN"

    normalized = normalized[normalized["order_id"].str.len() > 0].copy()
    normalized = normalized[normalized["sku"].str.len() > 0].copy()

    nat_order_ts_pct = float(normalized["order_ts"].isna().mean() * 100.0) if len(normalized) else 0.0
    dropped_nat_order_ts_row_count = int(normalized["order_ts"].isna().sum())
    normalized = normalized[normalized["order_ts"].notna()].copy()

    if len(normalized):
        min_order_ts = normalized["order_ts"].min().isoformat()
        max_order_ts = normalized["order_ts"].max().isoformat()
    else:
        min_order_ts = None
        max_order_ts = None

    prefix_counts = (
        normalized["order_id"]
        .str[0]
        .fillna("?")
        .value_counts(dropna=False)
        .head(5)
        .astype(int)
        .to_dict()
    )

    stats = {
        "raw_row_count": int(len(raw)),
        "normalized_row_count": int(len(normalized)),
        "dropped_nat_order_ts_row_count": dropped_nat_order_ts_row_count,
        "nat_order_ts_pct": nat_order_ts_pct,
        "null_customer_rate_pct": null_customer_rate,
        "min_order_ts": min_order_ts,
        "max_order_ts": max_order_ts,
        "top_prefix_counts": prefix_counts,
    }
    return normalized, stats


def load_rules_csv(path: Path) -> pd.DataFrame:
    rules = pd.read_csv(path)
    rules = rules.sort_values("priority", kind="stable").reset_index(drop=True)
    return rules
