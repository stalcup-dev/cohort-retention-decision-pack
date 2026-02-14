# Shopify Adapter Proof Run

## Purpose
Show a public-safe proof run from Shopify-shaped orders export to canonical outputs used by this decision pack.

## Input
- `public_demo/shopify_mock_orders.csv`

## Command
```powershell
py -3 scripts/ingest_shopify_exports.py --orders public_demo/shopify_mock_orders.csv --out-dir public_demo
```

## Expected PASS Signature
```text
ingest_shopify=PASS canonical=public_demo/shopify_order_lines_canonical.csv activity=public_demo/shopify_customer_month_activity.csv summary=public_demo/shopify_demo_summary.csv plot=public_demo/shopify_demo_output.png
```

## Expected Outputs
- `public_demo/shopify_order_lines_canonical.csv`
- `public_demo/shopify_customer_month_activity.csv`
- `public_demo/shopify_demo_summary.csv`
- `public_demo/shopify_demo_output.png`

## Decision Relevance
These outputs demonstrate that Shopify-shaped exports can be normalized into the same decision artifacts used by the cohort retention pack.
