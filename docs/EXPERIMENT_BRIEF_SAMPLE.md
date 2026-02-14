# Experiment Brief - Target Family Retention Lift

## Purpose
Standardize how each family-level retention test is framed so RevOps can make a scale/pause decision quickly.

## Audience
- RevOps owner
- Lifecycle/CRM owner
- Analytics owner
- Finance reviewer (guardrail sign-off)

## Decision Context
- Priority families from the decision pack: `Seasonal`, `Home_Fragrance`, `Bags`.
- Run one brief per family and keep treatment logic reversible.

## Objective
Improve month-2 repeat behavior and value retention for one target `first_product_family` without degrading economics.

## Hypothesis
If a family-specific post-purchase intervention is applied, then M2 logo retention and M2 net proxy retention should improve versus control while guardrails remain stable.

## Population
- Eligible cohort: new customers whose first order maps to the selected family.
- Exclusions: guest, invalid, and credit-only cohort edge cases.
- Randomization unit: `customer_id`.
- Assignment split: 50/50 treatment vs control.

## Intervention
- Treatment:
  - Family-specific winback and replenishment message sequence.
  - Offer or bundle variation aligned to family behavior.
- Control:
  - Business-as-usual lifecycle flow.

## Measurement Window
- Exposure window: fixed launch-to-stop dates approved by RevOps.
- Primary readout: month-2 cohort outcome.
- Interim readout: week-1 directional indicators (non-decisive).

## Metrics
- Primary KPI:
  - `M2_logo_retention = mean(is_retained_logo) where months_since_first = 2`
- Secondary KPI:
  - `M2_net_proxy_retention = sum(net_revenue_proxy_total at m2) / sum(gross_revenue_valid at m0)`
- Support metric:
  - `net_minus_logo_gap_pp = (M2_net_proxy_retention - M2_logo_retention) * 100`

## Success Criteria
- M2 logo retention improves vs control at the pre-agreed threshold.
- M2 net proxy retention improves vs control at the pre-agreed threshold.
- Net-minus-logo gap moves toward `>= 0 pp`.

## Guardrails
- Margin proxy remains above the finance-approved floor.
- Cohort quality (`n_customers`) remains stable.
- Credit-like/refund proxy does not shift adversely.

## Decision Rule
- `Scale`: KPI thresholds met and all guardrails hold.
- `Iterate`: directional KPI improvement but thresholds not met, guardrails hold.
- `Pause`: any critical guardrail fails or KPI deltas are adverse.

## Owners + Cadence
- RevOps owner: accountable for decision call.
- Analytics owner: accountable for readout integrity.
- Finance reviewer: accountable for guardrail acceptance.
- Checkpoints:
  - Day 7 directional readout.
  - Day 14+ scale/pause/iterate recommendation package.
