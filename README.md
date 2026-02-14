# Cohort Retention Decision Pack (DTC / eCommerce)

## Decision This Supports
Which first-order product families should be prioritized first to improve M2 retention and value retention, without harming margin quality?

## Open First (Reviewer Path)
1. Story (PDF): `exports/cohort_retention_story.pdf`
2. Story (HTML): `exports/cohort_retention_story.html`
3. Decision memo: `docs/DECISION_MEMO_1PAGE.md`
4. Case study narrative: `case_study_readme.md`

## 60-Second Review Flow
- Read the decision + targets in `docs/DECISION_MEMO_1PAGE.md`.
- Use `exports/cohort_retention_story.pdf` for GitHub-visible charts.
- Open `exports/cohort_retention_story.html` for the full rendered artifact.
- Check `docs/EXPERT_UPDATE.md` for scope and sanity receipts.

## One Command: Zero -> Decision Pack
Prerequisites:
- Place raw input at `data_raw/OnlineRetailII.xlsx`.
- Install dependencies once:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install -e ".[dev]"
```

Run full flow:
```powershell
py -3 scripts/run_zero_to_decision.py --input data_raw/OnlineRetailII.xlsx
```

This command:
- runs pipeline generation (`scripts/run_pipeline.py`)
- runs full smoke validation (`scripts/smoke_pipeline.py`)
- builds final pack (`scripts/build_final_pack.py`)
- prints elapsed minutes + key output paths

## Key Artifacts
- Story PDF: `exports/cohort_retention_story.pdf`
- Story HTML: `exports/cohort_retention_story.html`
- Memo: `docs/DECISION_MEMO_1PAGE.md`
- QA checklist: `docs/QA_CHECKLIST.md`
- Coverage report: `docs/DRIVER_COVERAGE_REPORT.md`
- Expert update: `docs/EXPERT_UPDATE.md`
- Final pack folder: `exports/final_decision_pack_v1`
- Experiment brief sample: `docs/EXPERIMENT_BRIEF_SAMPLE.md`
- Week-2 readout template: `docs/WEEK2_READOUT_TEMPLATE.md`

## Teaching Path
- Teaching hub (all learning docs mapped): `docs/TEACHING_HUB.md`
- Teaching notebook export: `exports/cohort_retention_teaching.html`
- Private teaching hub: `private_teaching/index.html`

## Technical Detail
Single technical appendix: `docs/TECHNICAL_APPENDIX.md`

## Optional Deep Dives
Supplementary document index: `docs/archive/README.md`
