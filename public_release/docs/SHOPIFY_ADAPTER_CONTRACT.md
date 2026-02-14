# Shopify Adapter Contract (BETA, Public-Safe)

## Purpose
Define the minimum ingestion contract to make this project Shopify-operable without changing existing analytics logic.

## Required Shopify CSVs

### MVP minimum
1. `orders.csv` (required)

### Recommended for fuller parity
2. `customers.csv` (optional in beta)
3. `products.csv` (optional in beta)

This beta adapter runs from `orders.csv` only and derives a cohort baseline.

## Required Columns (orders.csv)
- `id`
- `created_at`
- `customer_id`
- `financial_status`
- `cancelled_at`
- `lineitem_sku`
- `lineitem_name`
- `lineitem_quantity`
- `lineitem_price`
- `total_price`

## Accepted Formats + Assumptions
- File format: UTF-8 CSV with header row.
- `created_at`: parseable ISO-like datetime string (timezone accepted if parseable by pandas).
- `id`: unique per order row at export grain.
- `lineitem_quantity`, `lineitem_price`, `total_price`: numeric-coercible values.
- Missing `customer_id` is allowed and mapped to `GUEST` for exclusion from cohort denominators.
- Status assumption for beta mapping:
  - `financial_status in {voided, refunded}` or non-empty `cancelled_at` -> cancellation/credit-like behavior.

## Canonical Mapping (orders.csv -> adapter outputs)
| Shopify column | Canonical field | Rule |
|---|---|---|
| `id` | `order_id` | Trim, uppercase string |
| `created_at` | `order_ts` | Parse datetime (`errors=coerce`, fail if any NaT) |
| `customer_id` | `customer_id` | Null/blank -> `GUEST`; else stable string ID |
| `lineitem_sku` | `sku` | Trim, uppercase |
| `lineitem_name` | `description` | Trim string |
| `lineitem_quantity` | `quantity` | Numeric conversion required |
| `lineitem_price` | `unit_price` | Numeric conversion required |
| `lineitem_quantity`, `lineitem_price` | `line_amount_gross` | `max(quantity,0) * max(unit_price,0)` |
| `lineitem_quantity`, `lineitem_price` | `line_amount_net_proxy` | `quantity * unit_price` |
| `cancelled_at`, `financial_status` | `is_cancel_invoice` | True if cancelled or status in `{voided, refunded}` |
| derived from valid non-guest first order month | `cohort_month` | `YYYY-MM` |
| activity month - cohort month | `months_since_first` | Period month difference |

## Adapter Outputs (deterministic)
The ingest script writes repo-relative outputs under `public_demo/`:
- `shopify_order_lines_canonical.csv`
- `shopify_customer_month_activity.csv`
- `shopify_demo_summary.csv`
- `shopify_demo_output.png`

## What Gets Produced
- Canonical line-level table for downstream parity checks: `shopify_order_lines_canonical.csv`
- Customer-month activity baseline with cohort derivations: `shopify_customer_month_activity.csv`
- M2 logo retention baseline summary: `shopify_demo_summary.csv`
- Visual sanity check chart: `shopify_demo_output.png`

## Validation Rules and Failure Messages
1. Missing required columns
   - Failure message format:
   - `ingest_shopify=FAIL missing_required_columns=['col_a','col_b']`
2. Unparseable timestamps in `created_at`
   - Failure message format:
   - `ingest_shopify=FAIL bad_created_at_rows={count}`
3. Duplicate `id` values
   - Failure message format:
   - `ingest_shopify=FAIL duplicate_order_ids={count}`
4. Non-numeric quantity or price
   - Failure message format:
   - `ingest_shopify=FAIL non_numeric_quantity_or_price_rows={count}`
5. Non-positive `total_price` share over threshold (beta warning gate)
   - Failure threshold: >20%
   - Failure message format:
   - `ingest_shopify=FAIL non_positive_total_price_pct={pct}`

## Success Contract
On success, script prints repo-relative paths only:
- `ingest_shopify=PASS canonical=public_demo/shopify_order_lines_canonical.csv activity=public_demo/shopify_customer_month_activity.csv summary=public_demo/shopify_demo_summary.csv plot=public_demo/shopify_demo_output.png`
