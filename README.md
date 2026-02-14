# Cohort Retention Decision Pack (DTC / eCommerce)

Outcome: this repo produces a decision-ready retention pack that identifies the first product families to test next (`Seasonal`, `Home_Fragrance`, `Bags`) and ships the artifacts needed for a scale/pause decision.

## Who This Is For (ICP)
- RevOps, Retention, and BI leaders who need a fast M2 retention prioritization read.
- Hiring managers reviewing decision quality, governance discipline, and operator readiness.
- ECommerce teams with Shopify-shaped exports that need a practical 2-week experiment plan.

## What It Outputs
- Public release ZIP: [`exports/public_release_latest.zip`](exports/public_release_latest.zip)
- Story artifacts:
  - HTML: [`public_release/exports/cohort_retention_story.html`](public_release/exports/cohort_retention_story.html)
  - PDF snapshot: [`exports/cohort_retention_story.pdf`](exports/cohort_retention_story.pdf)
- Decision artifacts:
  - Memo: [`public_release/docs/DECISION_MEMO_1PAGE.md`](public_release/docs/DECISION_MEMO_1PAGE.md)
  - Hiring manager TL;DR: [`public_release/docs/HIRING_MANAGER_TLDR.md`](public_release/docs/HIRING_MANAGER_TLDR.md)
  - Case study: [`public_release/case_study_readme.md`](public_release/case_study_readme.md)
- Operating decisions/tickets:
  - scale / pause / iterate recommendation structure in [`public_release/docs/DECISION_MEMO_1PAGE.md`](public_release/docs/DECISION_MEMO_1PAGE.md)
  - target-family prioritization handoff in [`public_release/docs/HIRING_MANAGER_TLDR.md`](public_release/docs/HIRING_MANAGER_TLDR.md)
- Shopify-operable proof path:
  - Adapter contract: [`docs/SHOPIFY_ADAPTER_CONTRACT.md`](docs/SHOPIFY_ADAPTER_CONTRACT.md)
  - Adapter proof outputs: [`public_demo/shopify_demo_summary.csv`](public_demo/shopify_demo_summary.csv), [`public_demo/shopify_demo_output.png`](public_demo/shopify_demo_output.png)

## Why Trust This
- Deterministic packaging: same commands produce the same release structure.
- Contracted chart narrative: fixed 3-chart story, decision-aligned memo.
- Quality gates:
  - `pytest -q`
  - public redaction scanner: `scripts/public_audit.py`
  - release bundler: `scripts/build_public_zip.py`
- Security/redaction controls:
  - public release built from allowlisted artifacts only
  - forbidden token/path scan before packaging
  - private internal work kept outside public release bundle

## Run (Minimal, Copy-Paste)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install -e ".[dev]"

py -3 -m pytest -q
py -3 scripts/public_audit.py
py -3 scripts/build_public_zip.py
```

## Proof (Current Repo)
- Tests: `pytest -q` (see latest run in terminal output below)
- Public audit: no forbidden paths/tokens in public bundle inputs
- Release artifact: [`exports/public_release_latest.zip`](exports/public_release_latest.zip)

### Visual Snapshot
![Chart 1 - Cohort Logo Retention](public_demo/story_chart_1.png)
![Chart 2 - Net Retention Proxy Curves](public_demo/story_chart_2.png)
![Chart 3 - M2 Retention by Family](public_demo/story_chart_3.png)

## Public vs Private
- Public-safe artifacts:
  - `public_release/`
  - `exports/public_release_latest.zip`
  - `README.md`, `case_study_readme.md`, decision docs linked above
- Private/internal working surfaces (not part of public release contract):
  - private working folders and internal notes
  - internal pipeline scratch/temp folders
  - raw input staging and local environment artifacts
- Redaction note: publish from the public bundle output, not from raw repo root.

## Additional Reviewer Docs
- Buyer-friction audit: [`docs/AUDIT_PUBLIC.md`](docs/AUDIT_PUBLIC.md)
- Release checklist: [`docs/SHIP_CHECKLIST.md`](docs/SHIP_CHECKLIST.md)
