# Experiment Brief (Sample) - Target Family Retention Lift

## Use This With
- Learning map: `docs/TEACHING_HUB.md`
- Readout template: `docs/WEEK2_READOUT_TEMPLATE.md`
- SQL grounding: `private_teaching/module_experiment_readout_sql.html`

## Objective
Increase early retention quality for one target `first_product_family` cohort without degrading economics.

## Decision Context
- Target families from decision pack: `Seasonal`, `Home_Fragrance`, `Bags`.
- This sample brief is written for one family at a time; duplicate for each target.

## Hypothesis
If we apply a family-specific post-purchase retention intervention, then M2 logo retention and M2 net proxy retention will improve versus control.

## Population
- Eligibility:
  - First order family = `<TARGET_FAMILY>`
  - New cohort customers only
  - Exclude guest and invalid/credit-only cohort cases
- Randomization unit: `customer_id`
- Split: 50/50 treatment vs control

## Intervention
- Treatment:
  - Family-specific winback + replenishment message sequence
  - Offer/bundle variant aligned to family behavior
- Control:
  - Business-as-usual lifecycle flow

## Measurement Window
- Exposure start: `<YYYY-MM-DD>`
- Exposure end: `<YYYY-MM-DD>`
- Primary readout: month-2 cohort outcome
- Interim readout: week-1 directional indicators (non-decisive)

## Metrics
- Primary KPI:
  - `M2_logo_retention = mean(is_retained_logo) where months_since_first = 2`
- Secondary KPI:
  - `M2_net_proxy_retention = sum(net_revenue_proxy_total at m2) / sum(gross_revenue_valid at m0)`
- Support metric:
  - `net_minus_logo_gap_pp = (M2_net_proxy_retention - M2_logo_retention) * 100`

## Success Criteria (Template)
- `M2_logo_retention` lift >= `+X pp` vs control
- `M2_net_proxy_retention` lift >= `+Y pp` vs control
- `net_minus_logo_gap_pp` improves toward `>= 0 pp`

## Guardrails
- Margin proxy not worse than `-Z%`
- Cohort quality (`n_customers`) does not deteriorate materially
- Credit-like/refund proxy does not shift adversely

## Decision Rule
- `Scale`: both primary + secondary thresholds met, guardrails hold
- `Iterate`: one KPI improves but threshold not met, guardrails hold
- `Pause`: guardrail breach or both KPIs miss materially

## Owners + Cadence
- Owner: `<RevOps Owner>`
- Analytics owner: `<Analytics Owner>`
- Checkpoints:
  - Day 7: directional readout
  - Day 14+: recommendation package for scale/pause/iterate
