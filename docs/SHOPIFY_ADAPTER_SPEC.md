# Shopify Adapter Spec (Public-Safe, No Implementation)

## Purpose
Define a minimal adapter contract that maps Shopify exports into this project’s cohort-retention model without changing existing analytics logic.

## Required Shopify Export Files (MVP)
1. Orders export (`orders.csv`)
2. Customers export (`customers.csv`)
3. Products export (`products.csv`)

## MVP Field List

### Orders export (required)
- `id` (order identifier)
- `created_at` (order timestamp)
- `customer_id`
- `financial_status`
- `cancelled_at`
- `lineitem_sku`
- `lineitem_name`
- `lineitem_quantity`
- `lineitem_price`
- `total_price`

### Customers export (required)
- `id` (customer identifier)
- `created_at`
- `default_address_country` (optional for segmentation later)

### Products export (required)
- `id` (product identifier)
- `handle`
- `title`
- `variant_sku`
- `product_type`

## Mapping Table (Shopify -> Existing Model)
| Shopify source field(s) | Target/derived field | Mapping rule (high-level) | Notes |
|---|---|---|---|
| `orders.id` | `order_id` | String normalize (trim/uppercase if needed) | Must remain unique per order |
| `orders.customer_id` | `customer_id` | Coerce to stable string ID; null -> `GUEST` | `GUEST` excluded from cohort denominators |
| `orders.created_at` | `order_ts` | Parse to timestamp; derive month period | Month used for cohort and activity math |
| `orders.cancelled_at`, `orders.financial_status` | `is_credit_like` | Credit/refund/cancel indicators map to credit-like flag | Align with existing paid vs credit treatment |
| `lineitem_quantity`, `lineitem_price` | `line_amount_gross` | Positive quantity x positive price proxy | Used for gross-valid baseline |
| `lineitem_quantity`, `lineitem_price`, status flags | `line_amount_net_proxy` | Refund-aware proxy at line/order level | Directional value signal, not accounting profit |
| `lineitem_sku`, `lineitem_name` | `sku`, `description` | Normalize text keys | Inputs to family mapping rules |
| mapped family from SKU/description | `first_product_family` | Determine from first valid order family mix | NonMerch exclusion remains unchanged |
| customer first valid purchase month | `cohort_month` | Earliest valid order month per customer | Format `YYYY-MM` |
| activity month - cohort month | `months_since_first` | Month difference on period basis | Horizon remains `H=6` in main model |

## Validation Checks (Adapter QA)
- Row-count sanity:
  - Orders rows and line-item rows reconcile to export totals within expected variance.
- Timestamp sanity:
  - `min(created_at)` and `max(created_at)` are non-null and within expected business window.
- Null-rate checks:
  - `% null customer_id`, `% unparseable created_at`, `% missing sku`.
- Key checks:
  - `order_id` uniqueness at order grain.
  - `customer_id` coercion has no float-like tails (for example `.0` suffix).
- Cohort checks:
  - Derived `cohort_month` exists for non-guest customers with valid purchases.
  - `months_since_first` is integer month math from period differences.

## MVP vs Nice-to-Have

### MVP ingestion
- Orders + customers + products exports with fields above.
- Cohort outputs:
  - `cohort_month`
  - `months_since_first`
  - M2 logo retention baseline
  - net proxy directional baseline

### Nice-to-have later
- Refund reason codes
- Channel attribution fields
- Discount code detail
- Fulfillment latency detail

## Beta Outcome (What Becomes Possible)
- Directly ingest Shopify exports into the existing cohort decision framework.
- Regenerate the same decision artifacts (story + memo + public package) from Shopify-shaped source data.
- Compare baseline retention by first-order family before testing interventions.
