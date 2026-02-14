# PUBLIC RELEASE PLAN

## Goal
Publish a portfolio-safe subset of this project without exposing private implementation details, raw data, or internal tooling.

## Public Assets To Keep (`KEEP_PUBLIC`)
- `README_PUBLIC.md`
- `case_study_readme.md`
- `docs/DECISION_MEMO_1PAGE.md`
- `exports/cohort_retention_story.html`
- `public_demo/**`

## Private Assets To Keep Internal (`PRIVATE_ONLY`)
- `data_raw/**`
- `data_processed/**`
- `scripts/**` (except optional public packager scripts used only to create `public_release/`)
- `tests/**`
- `.github/**`
- `.tmp*/**`
- `.venv/**`
- `*.zip` (internal bundles)

## Redaction Targets (`REDACT`)
- Remove machine/user paths (`C:\Users\...`) from public docs/artifacts.
- Remove environment/proxy diagnostics (`PIP_NO_INDEX`, `HTTPS_PROXY`).
- Remove lock/host troubleshooting text (`index.lock`, ACL/reset details).
- Remove internal ticket/process references (`CA-`, internal gate harness naming).

## DO NOT PUBLISH Rules
Do not publish these paths:
- `data_raw/**`
- `data_processed/**`
- `scripts/**`
- `tests/**`
- `.github/**`
- `.tmp*/**`

Do not publish files containing these strings:
- `C:\Users\`
- `PIP_NO_INDEX`
- `HTTPS_PROXY`
- `index.lock`
- `CA-`

## Proposed Public Tree
```text
public_release/
  README_PUBLIC.md
  case_study_readme.md
  docs/
    DECISION_MEMO_1PAGE.md
  exports/
    cohort_retention_story.html
  public_demo/
    README.md
    demo.py
    demo_data.csv
    demo_output.png
    demo_summary.csv
```

## Public Branch Strategy Recommendation
Recommended approach: `public_release/` export folder in this repo, then publish that folder to a separate public repo.

Why:
- Avoids accidental exposure from mixed private/public history.
- Keeps private working tree intact.
- Makes release deterministic (`build_public_release.py` can rebuild exactly).

Alternatives considered:
- Public branch in same repo: higher risk of accidental merge/backflow.
- Manual copy per release: error-prone and non-repeatable.
