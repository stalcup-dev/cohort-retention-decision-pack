# Case Study: Cohort Retention Decision Pack (DTC / eCommerce)

This is the public narrative companion to the publishable bundle.

## Company Scenario
A direct-to-consumer retailer asked for a cohort-based answer to one operational question:
which product families should be prioritized first to improve early retention and protect value retention.

## What We Found (Directional, Not Causal)
- Weakest M2 retention families: `Seasonal`, `Home_Fragrance`, `Bags`.
- Chart 2 net-retention curves provide trajectory calibration for realistic lift expectations.
- Decision direction: focus early experiments on those three families.

## Two-Week RevOps Roadmap

### Week 1: Diagnose and Design
- Break down retention by promo intensity, basket-size proxy, and new/returning mix where available.
- Audit merchandising and lifecycle touchpoints for `Seasonal`, `Home_Fragrance`, and `Bags`.
- Build a ranked hypothesis slate (2-3 tests per family) with expected lift ranges.
- Define measurement rules before launch:
- M2 logo retention target: pre-agreed percentage-point lift vs control.
- M2 net proxy retention target: pre-agreed percentage-point lift vs control.
- Net-minus-logo gap target: toward `>= 0 pp` in at least 2 of 3 families.

### Week 2: Launch, Read, Decide
- Run controlled tests per family (offer/bundle, post-purchase flows, cross-sell/attach).
- Monitor guardrails in parallel:
- margin proxy not worse than the finance-approved floor
- no cohort-quality deterioration
- no adverse credit-like-rate shift
- Deliver a Week-2 readout with `scale`, `pause`, or `iterate` recommendations.

## Metric Notes
- Net retention proxy is used for directional value tracking.
- Right-censored months are treated as missing (`NA`), not zeros.
- The retention horizon is `H=6` months (`0..6`).

## Public Artifacts
- `public_release/exports/cohort_retention_story.html`
- `public_release/docs/DECISION_MEMO_1PAGE.md`
- `public_demo/shopify_demo_output.png`
