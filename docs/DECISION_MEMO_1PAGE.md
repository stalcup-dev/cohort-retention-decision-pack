# Decision Memo (1 Page)

## Decision / Recommendation
Prioritize retention experiments on the three weakest **first_product_family** groups at **M2** (from Chart 3), and use Chart 2 curves to calibrate expected value-retention trajectory.

**Initial targets:** `Seasonal`, `Home_Fragrance`, `Bags`  
**Decision thresholds:** logo `+X pp`, net proxy `+Y pp`, and improve net-minus-logo gap toward `>= 0 pp`  
**Guardrails:** margin proxy not worse than `-Z%`, no cohort-quality deterioration, no adverse credit-like / refund-like rate shift  
**Driver (frozen):** `first_product_family` (wholesale-like remains QA-only)

Chart 1 = who returns · Chart 2 = how much value remains · Chart 3 = where to act

## North Star Metric
**M2 logo retention (cohort-weighted):** customer-weighted share of cohort customers with ≥1 valid purchase in month 2.

## Single High-Leverage Insight (descriptive, not causal)
The largest M2 underperformance clusters in `Seasonal`, `Home_Fragrance`, and `Bags` — where early repeat and value-quality risk converge most clearly in the current baseline.

## Baseline Targets (from Chart 3)
| family_group | n_customers | m2_logo_retention | m2_net_proxy_retention | gap_pp |
|---|---:|---:|---:|---:|
| Seasonal | 233 | 0.1674 | 0.2069 | 3.9 |
| Home_Fragrance | 526 | 0.2072 | 0.2808 | 7.4 |
| Bags | 367 | 0.2207 | 0.2363 | 1.6 |

## Impact Model (scenario, not observed)
Alpha honesty: this release is diagnostic; **no measured intervention lift yet**.

If controlled tests improve M2 logo retention by **Δ = +X pp** among eligible new customers in the target families:
- Incremental repeat customers (M2) ≈ `Eligible_New_Customers_in_Targets * Δ`
- Incremental orders ≈ `Incremental_Repeat_Customers * Orders_per_Repeater_M2`
- Incremental revenue ≈ `Incremental_Orders * AOV`
- Guarded contribution ≈ `Incremental_Revenue * Gross_Margin` (must satisfy guardrails)

(Company-specific inputs come from Shopify exports via adapter: eligible new customers, AOV, margin proxy, refunds/chargebacks.)

## Tradeoffs
- Focus vs breadth: targeting 3 families improves actionability but defers lower-volume families.
- Speed vs certainty: 2-week cycles accelerate learning but do not replace full causal readout windows.
- Seasonality confound: family deltas can reflect acquisition-window mix and timing effects.
- Margin risk: repeat can rise while economics worsen if guardrails aren’t enforced.

## What we'd do next (2 weeks)
- **Week 1:** lock hypotheses + instrumentation, finalize thresholds (`+X pp`, `+Y pp`) and guardrails (`-Z%`, quality stability, risk stability), assign owners.
- **Week 2:** launch controlled tests per family; run interim readout; issue **scale / pause / iterate** decision and set next M2 checkpoint dates.

Appendix note: SKU drilldown exists for activation only (no new driver/segmentation/charts).  
Directional not causal: this memo is for prioritization + experiment design, not attribution.
