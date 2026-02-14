# Decision Memo (1 Page)

## Decision / Recommendation
Prioritize retention experiments on the three weakest first_product_family groups at M2 (selected from Chart 3), then use Chart 2 curves to calibrate value-retention expectations.
Initial targets: `Seasonal`, `Home_Fragrance`, `Bags`.
Success criteria (decision thresholds): logo `+X pp`, net proxy `+Y pp`, and gap improvement toward `>= 0 pp`.
Guardrails: margin proxy not worse than `-Z%`, no cohort quality deterioration, and no adverse credit-like rate shift.

Chart 1 = who returns; Chart 2 = how much value remains over months; Chart 3 = where to act.

## Top 3 Target Families
- `#1 Seasonal`: M2 logo 16.7%, M2 net proxy 20.7%, n=233
- `#2 Home_Fragrance`: M2 logo 20.7%, M2 net proxy 28.1%, n=526
- `#3 Bags`: M2 logo 22.1%, M2 net proxy 23.6%, n=367

Targets sourced from `chart3_m2_by_family.csv` using lowest M2 logo retention (tie-break: lower M2 net proxy).
| family_group | n_customers | m2_logo_retention | m2_net_proxy_retention | gap_pp |
|---|---:|---:|---:|---:|
| Seasonal | 233 | 0.1674 | 0.2069 | 3.9 |
| Home_Fragrance | 526 | 0.2072 | 0.2808 | 7.4 |
| Bags | 367 | 0.2207 | 0.2363 | 1.6 |

## Success criteria
- Raise M2 logo retention in each target family by `+X pp` vs control.
- Improve M2 net proxy retention in each target family by `+Y pp` vs control.
- Close net-minus-logo gap (`gap_pp`) toward `>= 0 pp` for at least 2 of 3 targets.

## Guardrails
- Guardrails: margin proxy not worse than `-Z%`, no decline in cohort size quality (`n_customers`), and no adverse shift in credit-like rate.

## Why Now
- Family-universe context (chart3 table): non-Other customer share = 46.2% (Other share = 53.8%).
- Chart 2 curve pattern (selected cohorts: 2009-12, 2010-02, 2010-11): median net proxy at M2=30.8%, M6=21.9%.
- Chart 2 metric definition: net_retention_proxy(c,t) = net_revenue_proxy_total(c,t) / denom_month0_gross_valid(c); denom guard requires denom_month0_gross_valid > 0.
- Chart 2 cohort selection (source: scope_receipts.json):
  selected_cohorts=['2009-12', '2010-02', '2010-11']
  used_fallback=False, plot_pool_count=10
  MIN_COHORT_N=50, MIN_PLOT_COHORT_N=200, H=6
- Gate C confound note: material sensitivity count = 0 (All vs Retail-only family M2 comparison).
- Gate A validity guardrail: 0.0000% valid purchases with non-positive net; trigger_fired=False.

## Plays
1. Replenishment nudge play: start with `Seasonal`-like profiles; measure M2 logo lift and holdout gap.
2. Returns/credits mitigation play: start with `Bags`-like profiles; measure net proxy stabilization at M2.

## What To Test First (SKU Callouts)
Source: `data_processed/appendix_top_products_in_chart3_targets.csv`.
- `Seasonal`: test drag SKUs `22952`, `22910`; optional lift SKU `22086`.
- `Home_Fragrance`: test drag SKUs `21124`, `72741`; optional lift SKU `85123A`.
- `Bags`: test drag SKUs `20728`, `22411`; optional lift SKU `85099F`.

Directional not causal: this memo is for prioritization and experiment design, not causal attribution.
NonMerch exclusion: `*_NonMerch` families are excluded from first_product_family assignment competition by design.
