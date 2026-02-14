# Hiring Manager TL;DR (60-90 seconds)

## Problem
A DTC/eCommerce business needs a fast answer to: **which first-order product families should we prioritize first** to improve early retention and value quality.

## North Star
**M2 logo retention (cohort-weighted)** = customer-weighted share of new customers who place >=1 valid purchase in month 2.

## One Insight (descriptive, not causal)
The weakest early-retention signal clusters in **`Seasonal`, `Home_Fragrance`, and `Bags`**. This is **prioritization**, not proof of causality.

## Decision
Prioritize these three families for **reversible retention tests** (fast, controlled), while guarding against **margin degradation** and **credit-like risk shifts**.

## Impact Model (scenario, not observed)
**Alpha honesty:** no measured intervention lift yet - this is a diagnostic pack + test plan.

If we run tests that improve M2 logo retention by a pre-agreed **Delta** among eligible new customers in the target families, then:

- Incremental repeat customers (Month 2) ~= `Eligible_New_Customers * Delta`
- Incremental orders ~= `Incremental_Repeat_Customers * Orders_per_Repeater_M2`
- Incremental revenue ~= `Incremental_Orders * AOV`
- Guarded contribution ~= `Incremental_Revenue * Gross_Margin` (must meet guardrails)

**Assumptions to fill from the company's Shopify exports:**
`Eligible_New_Customers`, `Orders_per_Repeater_M2`, `AOV`, `Gross_Margin`, and refund/chargeback rates.

## Experiment Design Snapshot (2-week operating cycle)
**Unit:** customer-level randomization (new customers whose first order is in target family)  
**Arms:** Control vs Test (offer/messaging/merch treatment per family)  
**Primary success:** M2 logo retention lift vs control at a pre-agreed threshold  
**Secondary success:** M2 net retention proxy lift vs control; close `net-minus-logo gap` toward >=0 pp  
**Guardrails (must hold):** margin proxy above a finance-approved floor, no cohort quality deterioration, no adverse shift in credit-like/refund/chargeback rate  
**Cadence:** Week 1 finalize hypothesis + instrumentation + thresholds; Week 2 launch + interim readout + scale/pause decision

## What Shipped
- Story artifact: `public_release/exports/cohort_retention_story.html`
- Decision memo: `public_release/docs/DECISION_MEMO_1PAGE.md`
- Case-study narrative: `public_release/case_study_readme.md`
- Public zip: `exports/public_release_latest.zip`

## How To View
1. Open `public_release/exports/cohort_retention_story.html`
2. Read `public_release/docs/DECISION_MEMO_1PAGE.md`
3. Skim `public_release/case_study_readme.md`

## Shopify-operable path
Shopify-shaped cohort analysis with **direct export ingestion supported via adapter artifacts** (see `public_demo/` + `SHOPIFY_ADAPTER_CONTRACT.md`).
