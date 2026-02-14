# Public Buyer-Friction Audit

## Purpose
Identify what a recruiter, hiring manager, or buyer could misunderstand in under 90 seconds, then remove doubt with explicit fixes.

## Top 10 Confusion Risks + Fixes
1. Risk: "What is the concrete outcome?" is not obvious.
   Fix: put one-sentence outcome at top of `README.md`.
2. Risk: reviewer cannot tell who this is for.
   Fix: add explicit ICP section (RevOps, Retention, BI, hiring managers).
3. Risk: outputs are scattered and unclear.
   Fix: add one "What It Outputs" section with clickable paths for ZIP, HTML/PDF, memo, TL;DR, case study.
4. Risk: confidence is weak without trust signals.
   Fix: list deterministic run commands, tests, audit gate, and packaging gate.
5. Risk: "demo" language sounds like toy work.
   Fix: change narrative wording to "proof outputs" while preserving existing file names.
6. Risk: unclear what is public-safe vs internal.
   Fix: add explicit "Public vs Private" section with redaction note in `README.md`.
7. Risk: run instructions are long or ambiguous.
   Fix: provide a minimal copy-paste run block only for shipping gates.
8. Risk: buyer cannot verify visuals quickly.
   Fix: keep three chart screenshots directly in README.
9. Risk: "Shopify-operable" claim is vague.
   Fix: link contract and adapter proof outputs directly in public docs.
10. Risk: release process is not future-proof.
    Fix: add `docs/SHIP_CHECKLIST.md` with pre-publish and trust-signal checks.

## What Changed Today (and Why)
- Rewrote `README.md` to be decision-first and hiring-manager skimmable.
  Why: convert repo entry point from project log to buyer collateral.
- Updated public narrative wording in `README_PUBLIC.md`.
  Why: remove learner-tone words and tighten credibility.
- Updated `case_study_readme.md` public artifact reference.
  Why: point reviewers to adapter proof artifact directly.
- Updated `docs/HIRING_MANAGER_TLDR.md` Shopify-operable line.
  Why: make claim evidence-linked, not generic.
- Added `docs/SHIP_CHECKLIST.md`.
  Why: standardize publish discipline and trust signals release-over-release.

## Residual Risks (Not Changed in This Slice)
- Some template docs still intentionally include scaffold language (`EXPERIMENT_BRIEF_SAMPLE.md`, `WEEK2_READOUT_TEMPLATE.md`).
- Public and private narratives coexist in the same repo root, which requires disciplined use of the packaging scripts.
