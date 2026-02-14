# Cohort Retention Decision Pack (DTC / eCommerce)

This repository delivers a decision-ready RevOps retention pack that identifies where to act first (`Seasonal`, `Home_Fragrance`, `Bags`) and provides release artifacts for a scale/pause decision.

## Who This Is For (ICP)
- RevOps and Retention leaders prioritizing early repeat growth without margin drift.
- BI and Analytics teams responsible for decision-ready operating readouts.
- Hiring managers evaluating decision quality, governance discipline, and execution readiness.

## 90-Second Start
1. Open the public bundle: [`exports/public_release_latest.zip`](exports/public_release_latest.zip)
2. Review the story: [`public_release/exports/cohort_retention_story.html`](public_release/exports/cohort_retention_story.html)
3. Read the one-page decision memo: [`public_release/docs/DECISION_MEMO_1PAGE.md`](public_release/docs/DECISION_MEMO_1PAGE.md)
4. Skim the hiring manager summary: [`public_release/docs/HIRING_MANAGER_TLDR.md`](public_release/docs/HIRING_MANAGER_TLDR.md)

## Outputs You Get
- Public release package:
  - ZIP: [`exports/public_release_latest.zip`](exports/public_release_latest.zip)
- Decision artifacts:
  - Story HTML: [`public_release/exports/cohort_retention_story.html`](public_release/exports/cohort_retention_story.html)
  - Story PDF: [`exports/cohort_retention_story.pdf`](exports/cohort_retention_story.pdf)
  - Memo: [`public_release/docs/DECISION_MEMO_1PAGE.md`](public_release/docs/DECISION_MEMO_1PAGE.md)
  - Hiring summary: [`public_release/docs/HIRING_MANAGER_TLDR.md`](public_release/docs/HIRING_MANAGER_TLDR.md)
  - Case narrative: [`public_release/case_study_readme.md`](public_release/case_study_readme.md)
- Shopify-operable proof path:
  - Adapter contract: [`docs/SHOPIFY_ADAPTER_CONTRACT.md`](docs/SHOPIFY_ADAPTER_CONTRACT.md)
  - Proof outputs: [`public_demo/shopify_demo_summary.csv`](public_demo/shopify_demo_summary.csv), [`public_demo/shopify_demo_output.png`](public_demo/shopify_demo_output.png)

## Trust Signals
- Deterministic release flow:
  - `scripts/public_audit.py` enforces public-safety checks
  - `scripts/build_public_zip.py` produces a stable latest release zip
- Reproducible quality gates:
  - `pytest -q`
  - `public_audit.py`
  - `build_public_zip.py`
- Explicit decision framing:
  - directional, non-causal baseline
  - defined guardrails for margin and credit-like risk

## Minimal Run Commands
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install -e ".[dev]"

py -3 -m pytest -q
py -3 scripts/public_audit.py
py -3 scripts/build_public_zip.py
```

## Proof of Output
- Latest verified gates (local):
  - `pytest -q`: pass
  - `public_audit.py`: pass
  - `build_public_release.py`: pass
- Primary output:
  - [`exports/public_release_latest.zip`](exports/public_release_latest.zip)

### Visual Snapshot
![Chart 1 - Cohort Logo Retention](public_demo/story_chart_1.png)
![Chart 2 - Net Retention Proxy Curves](public_demo/story_chart_2.png)
![Chart 3 - M2 Retention by Family](public_demo/story_chart_3.png)

## Public vs Private Scope
- Public-safe:
  - `public_release/`
  - `public_demo/` proof artifacts
  - docs linked in this README
- Private/internal working surfaces:
  - local scratch and temporary folders
  - raw input staging and environment-specific files
- Redaction rule:
  - publish from `exports/public_release_latest.zip`, not from ad hoc root selection

## Roadmap (Next Public Hardening Steps)
- Add explicit release changelog snapshots per public zip build.
- Tighten docs index so optional deep dives are clearly separated from reviewer-critical docs.
- Add link validation output artifact for each release run.

## Known Limitations
- Current outputs are diagnostic and prioritization-oriented, not causal lift measurement.
- Financial guardrails rely on finance-approved thresholds set before experiment launch.
- Public proof artifacts are CSV/PNG/Markdown outputs, not a hosted application.

## Additional Governance Docs
- Public clarity audit: [`docs/AUDIT_PUBLIC.md`](docs/AUDIT_PUBLIC.md)
- Public ship checklist: [`docs/SHIP_PUBLIC.md`](docs/SHIP_PUBLIC.md)
- Technical appendix: [`docs/TECHNICAL_APPENDIX.md`](docs/TECHNICAL_APPENDIX.md)
