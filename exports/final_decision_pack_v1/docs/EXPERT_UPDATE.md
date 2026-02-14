# EXPERT UPDATE

- Sheets ingested: Year 2009-2010, Year 2010-2011
- Raw total rows (Excel): 1067371
- Processed order_lines rows: 1067371
- Line-item sanity: order_lines rows ~= raw_sum_rows +/-1% (delta=0.00%)
- Raw date span: 2009-12-01T07:45:00 to 2011-12-09T12:50:00
- Processed orders rows: 53628
- Processed customers rows: 5878
- Driver (frozen): first_product_family (wholesale-like remains QA-only)
- Appendix: drilldown-only for activation (no new driver/segmentation/charts)
- Chart 2 contract: Net retention proxy curves (3 cohorts max), formula net_retention_proxy(c,t)=net_revenue_proxy_total(c,t)/denom_month0_gross_valid(c), denominator guard required.
- Chart 2 policy: observed-only=True, right-censored missing=True, n>=50, H=6.
- Chart 2 cohort selection (source: scope_receipts.json): selected_cohorts=['2010-11', '2010-02', '2009-12'], used_fallback=False, plot_pool_count=10
- Chart 2 selection policy params: MIN_COHORT_N=50, MIN_PLOT_COHORT_N=200, H=6
- H=6 grid exists; right-censored months are masked in chart (NA), not treated as 0.
- Reconcile status: OK_BOTH_SHEETS
