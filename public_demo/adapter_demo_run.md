# Shopify Adapter Demo Run (Public)

This demo shows a Shopify-operable ingestion path using mock export data only.

## Inputs
- `public_demo/shopify_mock_orders.csv`

## Run
```powershell
py -3 scripts/ingest_shopify_exports.py --orders public_demo/shopify_mock_orders.csv --out-dir public_demo
```

## Expected PASS line
```text
ingest_shopify=PASS canonical=public_demo/shopify_order_lines_canonical.csv activity=public_demo/shopify_customer_month_activity.csv summary=public_demo/shopify_demo_summary.csv plot=public_demo/shopify_demo_output.png
```

## Outputs
- `public_demo/shopify_order_lines_canonical.csv`
- `public_demo/shopify_customer_month_activity.csv`
- `public_demo/shopify_demo_summary.csv`
- `public_demo/shopify_demo_output.png`

All output paths are repo-relative.
