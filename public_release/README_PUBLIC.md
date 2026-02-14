# Cohort Retention Decision Pack (DTC / eCommerce)

This repository publishes a public-safe export only.
Full pipeline + governance checks available on request.
Shopify-shaped; direct Shopify exports supported via adapter (see contract + demo artifacts).
Controls are intentionally minimal: added only where a reviewer would otherwise distrust the chart or memo.

## Executive Summary (90-second skim)
- Ask: which first-order families most need retention action.
- North Star: `M2 logo retention (cohort-weighted)`.
- Insight (descriptive): `Seasonal`, `Home_Fragrance`, and `Bags` under-index at M2; net-vs-logo gaps indicate value-quality risk.
- Decision: prioritize reversible experiments in those three families first.
- Alpha honesty: diagnostic baseline only; no measured intervention lift yet.

## What Shipped
- Public story HTML: `public_release/exports/cohort_retention_story.html`
- 1-page decision memo: `public_release/docs/DECISION_MEMO_1PAGE.md`
- Public audit-verified package: `exports/public_release_latest.zip`
- Case-study narrative: `public_release/case_study_readme.md`
- Adapter demo outputs: `public_demo/shopify_demo_output.png`, `public_demo/shopify_demo_summary.csv`
- Adapter contract: `docs/SHOPIFY_ADAPTER_CONTRACT.md`

## Start Here
1. Build public zip: `py -3 scripts/build_public_zip.py` -> `exports/public_release_latest.zip` (also writes `exports/public_release_<timestamp>.zip`)
2. Public story HTML: `public_release/exports/cohort_retention_story.html`
3. Public memo: `public_release/docs/DECISION_MEMO_1PAGE.md`
4. Public case study: `public_release/case_study_readme.md`
5. Hiring manager TL;DR: `public_release/docs/HIRING_MANAGER_TLDR.md`

## Business Question
Which first-order product families are underperforming on early retention, and what should be tested in the next two weeks to improve M2 outcomes without harming margin quality?

## What Was Delivered
- `public_release/exports/cohort_retention_story.html` with a 3-chart narrative.
- `public_release/docs/DECISION_MEMO_1PAGE.md` with target families and decision framing.
- `public_release/case_study_readme.md` with a week-by-week RevOps roadmap.
- `public_demo/demo_output.png` and `public_demo/demo_summary.csv` as a runnable demo slice.

## Story Screenshots (quick preview)
- `public_demo/story_chart_1.png`
- `public_demo/story_chart_2.png`
- `public_demo/story_chart_3.png`

## What We Found (Directional, Not Causal)
- Lowest M2 retention families: `Seasonal`, `Home_Fragrance`, `Bags`.
- Chart 2 net-retention curves provide expected value-retention trajectories for calibration.
- Recommended action: prioritize experiments in those three families first.

## Key Definitions (High-Level)
- Net retention proxy: monthly net value proxy divided by cohort month-0 gross baseline.
- Right-censoring policy: unobserved late months are shown as missing (not zero).
- Horizon: `H=6` months from first purchase (months `0..6`).

## Next 2 Weeks
- Week 1: define hypotheses and test slate by target family, with thresholds and guardrails.
- Week 2: launch controlled tests, run first readout, and decide to scale/pause.

## Success Thresholds + Guardrails
- Target M2 logo retention lift: `+X pp` vs control.
- Target M2 net proxy retention lift: `+Y pp`.
- Improve net-minus-logo gap toward `>= 0 pp` in at least 2 of 3 target families.
- Guardrails: margin proxy not worse than `-Z%`, stable cohort quality, no adverse credit-like-rate shift.

## Reviewer Checklist
- Open the story HTML and confirm exactly 3 charts are present.
- Confirm memo target families match the story conclusion.
- Check case-study roadmap has week-1 and week-2 actions.
- Verify screenshots match the 3 story charts at a glance.
- Use the public zip only; do not navigate private/internal project paths.
