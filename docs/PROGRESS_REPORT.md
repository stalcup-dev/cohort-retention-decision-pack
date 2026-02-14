# Progress Report - Public Release Status

## Current State
- Decision pack artifacts are generated and publishable.
- Public release bundle is available at `exports/public_release_latest.zip`.
- Governance checks and packaging checks are runnable from local commands.

## Delivered Artifacts
- Story: `public_release/exports/cohort_retention_story.html`
- Memo: `public_release/docs/DECISION_MEMO_1PAGE.md`
- Hiring summary: `public_release/docs/HIRING_MANAGER_TLDR.md`
- Case narrative: `public_release/case_study_readme.md`
- Adapter contract and proof outputs: `docs/SHOPIFY_ADAPTER_CONTRACT.md`, `public_demo/shopify_demo_summary.csv`, `public_demo/shopify_demo_output.png`

## Verification Signals
- `pytest -q` for regression safety.
- `scripts/public_audit.py` for public redaction checks.
- `scripts/build_public_zip.py` for deterministic release packaging.

## Open Items
- Maintain release cadence with explicit changelog notes per bundle refresh.
- Keep public docs aligned with latest artifact paths and proof outputs.
- Continue documenting known limitations as scope changes.
