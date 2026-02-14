# Technical Appendix

## Reviewer Map
- Start with `README.md` for business framing and artifact navigation.
- Use `docs/COHORT_DEFENSE_CARD.md` for frozen definitions and interpretation rules.
- Use `docs/EXPERIMENT_BRIEF_SAMPLE.md` and `docs/WEEK2_READOUT_TEMPLATE.md` for execution cadence artifacts.

## Scope
This appendix is the single technical reference for the decision pack.

## Data Scope
- Source sheets ingested: `Year 2009-2010`, `Year 2010-2011`
- Date span: 2009-12-01 to 2011-12-09
- Scope receipts: `data_processed/scope_receipts.json`

## Frozen Definitions (v1.2)
- Driver: `first_product_family` only.
- Cohort horizon: `H=6` months (`months_since_first` in `0..6`).
- Default valid purchase: `(order_gross > 0) & (is_cancel_invoice == 0)`.
- Credit-like: `is_cancel_invoice OR (order_net_proxy < 0)`.
- Right-censoring: unobserved months are shown as missing (`NA`), not `0`.

## Core Output Tables
- `data_processed/order_lines.csv`
- `data_processed/products.csv`
- `data_processed/orders.csv`
- `data_processed/transactions.csv`
- `data_processed/customers.csv`
- `data_processed/customer_month_activity.csv`

## Governance + Gates
- Gate A receipt: `data_processed/gate_a.json`
- Coverage report (Gate B): `docs/DRIVER_COVERAGE_REPORT.md`
- Confound table (Gate C): `data_processed/confound_m2_family_all_vs_retail.csv`
- QA checklist: `docs/QA_CHECKLIST.md`
- Expert summary: `docs/EXPERT_UPDATE.md`

## Story Contract
- Story artifact: `exports/cohort_retention_story.html`
- PDF reviewer artifact: `exports/cohort_retention_story.pdf`
- Chart count: exactly 3
- Contract checker: `scripts/verify_story_contract.py`

## Public-Safe Packaging
- Public release builder: `scripts/build_public_release.py`
- Public redaction audit: `scripts/public_audit.py`
- Public zip builder: `scripts/build_public_zip.py`
- Public output root: `public_release/`

## Related Narratives
- Case study: `case_study_readme.md`
- Public README: `README_PUBLIC.md`
- Experiment brief: `docs/EXPERIMENT_BRIEF_SAMPLE.md`
- Week-2 readout: `docs/WEEK2_READOUT_TEMPLATE.md`
- Supplementary docs index: `docs/archive/README.md`

## SQL Translation
- Cohort M2 metric query: `sql/cohort_m2_retention.sql`
