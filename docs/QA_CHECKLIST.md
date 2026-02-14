# QA CHECKLIST (must pass before analytics)

## Structural / grains
- orders.order_id unique PASS (rows=53628, unique=53628)
- products.sku unique PASS (rows=5131, unique=5131)
- customers.customer_id unique PASS (rows=5878, unique=5878)

## ID hygiene
- customer_id coercion prevents "12345.0" PASS (bad_ids=0)

## Month math
- months_since_first uses Period("M") diff PASS
- cohort_month/activity_month exported as YYYY-MM strings PASS

## Gates
### Gate A: validity trigger
- % valid purchases with order_net_proxy <= 0 = 0.0000%
- Trigger fired? NO
- If YES: strict validity applied + full rebuild performed N/A

### Gate B: driver coverage report produced PASS
### Gate C: confound table produced (All vs Retail-only) PASS
- Material sensitivity defined as >=5pp & n>=80 PASS

## Full grid (critical)
- customer_month_activity has exactly 7 rows/customer for months 0..6 PASS
- Month0 logo retention ~100% (after exclusions) PASS (100.00%)

## Credit alignment
- is_credit_like applied to orders.financial_status and transactions.kind PASS

## Denominator guard
- Cohorts with baseline sum(gross_revenue_valid at t=0)==0 are excluded from Chart 2 eligibility PASS (eligible=25, excluded=0)

## Chart discipline
- notebook contains exactly 3 charts FAIL (not started at this milestone)

## Right-censor sanity
- Chart2 right-censor applied (unobserved months are NaN, not 0): PASS (nan_cells=21, full_grid_customer_ok=True, full_h_cohort_ok=True, mask_ok=True)
- H=6 grid exists; censoring applied only at chart render layer. PASS
