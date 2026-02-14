# COHORT DEFENSE CARD

## Use This With
- Learning map: `docs/TEACHING_HUB.md`
- Talk tracks: `docs/CHART_TALK_TRACKS.md`
- Teaching walkthrough: `docs/TEACHING_REPORT.md`
- Source QA evidence: `docs/QA_CHECKLIST.md`

## Dataset Scope (from receipts)
- Input workbook: `data_raw/OnlineRetailII.xlsx`
- Sheets ingested: `Year 2009-2010` (525,461 rows), `Year 2010-2011` (541,910 rows)
- Raw combined rows: 1,067,371
- Date range (global): 2009-12-01T07:45:00 to 2011-12-09T12:50:00
- Reconciliation status: `OK_BOTH_SHEETS` (`order_lines.csv` rows = 1,067,371)

## Frozen Definitions (v1.2)
- `valid_purchase_default`: `(order_gross > 0) & (is_cancel_invoice == 0)`.
- `valid_purchase` (effective): equals `valid_purchase_default` unless Gate A triggers; if triggered, strict validity adds `(order_net_proxy > 0)` and rebuilds cohorts/activity from scratch.
- Guest handling: null/invalid `customer_id` is coerced to `GUEST`; `GUEST` is excluded from cohort-universe retention denominators.
- `is_credit_like`: `is_cancel_invoice OR (order_net_proxy < 0)`; this drives `orders.financial_status` and `transactions.kind` so negative amounts are not labeled as sales.
- Net proxy + denominator guard: monthly numerator is `sum(net_revenue_proxy_total)`; denominator is cohort month-0 `sum(gross_revenue_valid)`. Month-0 gross is stable for comparability; cohorts with denominator `0` are excluded from Chart 2.
- H=6 full grid: each cohort customer has `months_since_first` in `{0,1,2,3,4,5,6}` (exactly 7 rows/customer in `customer_month_activity.csv`).

## Gate Results
- Gate A: `% valid purchases with order_net_proxy <= 0 = 0.0000%`; trigger fired = `NO`; strict validity applied = `NO`.
- Gate B: `% gross revenue mapped to non-Other families = 79.70%`; `% customers with non-Other first_product_family = 59.08%`; `% first_product_family ending with _NonMerch = 0.00%`.
- Gate C: confound sensitivity (`All` vs `Retail-only`, material if `>=5pp` and `n>=80`) flagged 0 families.

## 3 Charts = 3 Questions
### Chart 1: Logo Retention Heatmap
- Question answered: How does repeat purchase propensity decay by cohort month across lifecycle months 0..6?
- How to read it:
  - Read each row left-to-right to see one cohort's retention slope.
  - Compare rows to see whether newer cohorts retain better/worse at the same month index.
- Common pitfall: comparing absolute cohort sizes from color intensity alone instead of using retention rate values.

### Chart 2: Family Impact Scatter (M2)
- Question answered: Which first-order families combine weak repeat behavior (logo retention) and weak refund-aware value (net proxy) at M2?
- How to read it:
  - X axis is M2 logo retention by family; Y axis is M2 net retention proxy by family.
  - Bottom-right indicates refund drag (repeat ok, value weak); top-left indicates repeat weakness (value ok, repeat weak).
  - Point size/labels reflect `n_customers`; tiny-n families are suppressed (`n<MIN_COHORT_N`).
- Metric definition in-chart: `net_retention_proxy(M2) = sum(net_revenue_proxy_total at M2) / sum(gross_revenue_valid at M0)` within a family (monthly, not cumulative).
- Policy line in-chart: observed-only (`OBSERVED_ONLY=True`), right-censored months excluded (`RIGHT_CENSOR_MODE=missing_not_zero`).
- Common pitfall: reading a low Y as \"profit loss\"; it is a revenue proxy ratio, directional for prioritization.

### Chart 3: M2 Retention by first_product_family
- Question answered: Which first-order families over/under-index on month-2 logo retention, with what sample size?
- How to read it:
  - Bar height is M2 logo retention; higher bars indicate stronger month-2 repeat behavior.
  - `n` labels indicate sample reliability; treat very small groups cautiously.
- Common pitfall: ranking tiny families as strategic priorities without n-threshold context.

## If Asked (Interview Answers)
- Why `first_product_family` as driver: it is fixed at acquisition, deterministic from first valid order line mix, and directly maps to first-order merchandising decisions.
- Why exclude `*_NonMerch`: postage/fees/adjustments are operational artifacts, not customer preference signals; keeping them in competition would contaminate the driver.
- Why "directional not causal": this is observational cohort segmentation, so differences can reflect underlying mix effects even when QA checks pass.
- What Gate B coverage means and why 70%: it quantifies how much gross revenue is mapped to specific non-Other families; the 70% threshold is a minimum usefulness bar so the driver is not dominated by residual `Other`.
- What Gate C confound test does: it compares M2 family retention in `All` customers vs `Retail-only` (`is_wholesale_like==0`) and flags material sensitivity (`>=5pp` with `n>=80`) to detect segment-driven instability.
