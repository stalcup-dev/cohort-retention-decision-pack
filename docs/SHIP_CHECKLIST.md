# Ship Checklist (Public Release)

## Before Publish
- Confirm no secrets or machine paths in public docs:
  - run `py -3 scripts/public_audit.py`
- Confirm all linked files exist and are repo-relative:
  - `README.md`
  - `public_release/README_PUBLIC.md`
  - story, memo, TL;DR, case study, adapter proof outputs
- Confirm latest story artifacts are present:
  - `public_release/exports/cohort_retention_story.html`
  - `exports/cohort_retention_story.pdf`
  - `public_demo/story_chart_1.png`, `public_demo/story_chart_2.png`, `public_demo/story_chart_3.png`
- Confirm release bundle builds:
  - run `py -3 scripts/build_public_zip.py`
  - confirm `exports/public_release_latest.zip` exists
- Confirm baseline quality gate:
  - run `py -3 -m pytest -q`

## Trust Signals Checklist
- Outcome statement is explicit and decision-focused.
- ICP is named (who should care and why).
- North Star metric is defined in plain language.
- Decision and target families are explicit.
- Guardrails and non-causal framing are explicit.
- Shopify-operable claim is linked to contract + proof outputs.
- Public vs private boundary is documented.
- Screenshots are visible in README for 90-second skim.
- Release artifact path is stable and clickable.
- Audit and test commands are documented and reproducible.

## Final Ship Receipt (Fill Per Release)
- Release date:
- Commit SHA:
- `pytest -q` result:
- `public_audit.py` result:
- `build_public_zip.py` result:
- Artifact: `exports/public_release_latest.zip`
