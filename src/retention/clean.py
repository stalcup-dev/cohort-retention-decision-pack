import re
from typing import Any

import pandas as pd


NULL_STRINGS = {"", "nan", "none", "null", "na", "nat"}


def normalize_token(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def coerce_order_id(value: Any) -> str:
    token = normalize_token(value).upper()
    return token


def coerce_sku(value: Any) -> str:
    token = normalize_token(value).upper()
    return token


def coerce_customer_id(value: Any) -> str:
    token = normalize_token(value)
    if token.lower() in NULL_STRINGS:
        return "GUEST"

    numeric_like = re.fullmatch(r"[+-]?\d+(\.0+)?", token)
    if numeric_like:
        return str(int(float(token)))

    try:
        parsed = float(token)
        if parsed.is_integer():
            return str(int(parsed))
    except ValueError:
        pass

    return token


def safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def safe_to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def canonical_column_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())
