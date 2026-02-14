# Cohort Retention Decision Pack (DTC / eCommerce)

This repository publishes a public-safe export only.  
Shopify-shaped; direct Shopify exports supported via adapter artifacts.

## Executive Summary (90-second skim)
- Business ask: identify which first-order families to prioritize for early-retention improvement.
- North Star: `M2 logo retention (cohort-weighted)`.
- High-leverage signal (descriptive): `Seasonal`, `Home_Fragrance`, and `Bags` under-index at M2, with value-quality risk in net-vs-logo gaps.
- Decision: run reversible experiments in those three families first.
- Alpha honesty: this is diagnostic baseline work; no measured intervention lift yet.

## Start Here
1. Public bundle: [`exports/public_release_latest.zip`](exports/public_release_latest.zip)
2. Story (HTML): [`public_release/exports/cohort_retention_story.html`](public_release/exports/cohort_retention_story.html)
3. Memo (MD): [`public_release/docs/DECISION_MEMO_1PAGE.md`](public_release/docs/DECISION_MEMO_1PAGE.md)
4. Case study (MD): [`public_release/case_study_readme.md`](public_release/case_study_readme.md)
5. Hiring manager TL;DR: [`public_release/docs/HIRING_MANAGER_TLDR.md`](public_release/docs/HIRING_MANAGER_TLDR.md)

## What You Get
- Story artifact with 3 charts: [`public_release/exports/cohort_retention_story.html`](public_release/exports/cohort_retention_story.html)
- One-page decision memo: [`public_release/docs/DECISION_MEMO_1PAGE.md`](public_release/docs/DECISION_MEMO_1PAGE.md)
- Public case-study narrative: [`public_release/case_study_readme.md`](public_release/case_study_readme.md)
- Adapter contract: [`docs/SHOPIFY_ADAPTER_CONTRACT.md`](docs/SHOPIFY_ADAPTER_CONTRACT.md)
- Adapter proof outputs: [`public_demo/shopify_demo_output.png`](public_demo/shopify_demo_output.png), [`public_demo/shopify_demo_summary.csv`](public_demo/shopify_demo_summary.csv)

## Visual Snapshot
![Chart 1 - Cohort Logo Retention](public_demo/story_chart_1.png)
![Chart 2 - Net Retention Proxy Curves](public_demo/story_chart_2.png)
![Chart 3 - M2 Retention by Family](public_demo/story_chart_3.png)

## Reviewer Checklist
- Confirm target families are consistent across story and memo (`Seasonal`, `Home_Fragrance`, `Bags`).
- Confirm the narrative is directional and non-causal.
- Confirm thresholds and guardrails are explicit, numeric, and approved before launch.
- Confirm adapter path and proof artifacts are present and public-safe.
- Use the zip bundle as the canonical handoff artifact.
