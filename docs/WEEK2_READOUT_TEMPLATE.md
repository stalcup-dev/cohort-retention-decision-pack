# Week 2 Readout - Retention Experiment Decision

## Purpose
Provide a single, decision-ready format for week-2 experiment review across target families.

## Audience
- RevOps decision owner
- Analytics readout owner
- Finance guardrail approver

## Executive Summary (Required)
- Recommendation: `Scale`, `Iterate`, or `Pause`
- Decision basis: M2 logo retention, M2 net proxy retention, and guardrail status
- Confidence level: `High`, `Medium`, or `Low` with one-sentence rationale

## Experiment Snapshot (Required Fields)
- Family tested
- Variant name
- Control cohort size (`control_n`)
- Treatment cohort size (`treatment_n`)
- Run status (`RUNNING` or `COMPLETE`)

## KPI Readout (Required Fields)
- M2 logo retention:
  - control value
  - treatment value
  - delta
  - threshold
  - pass/fail
- M2 net proxy retention:
  - control value
  - treatment value
  - delta
  - threshold
  - pass/fail
- Net-minus-logo gap (pp):
  - control value
  - treatment value
  - delta
  - direction toward `>= 0 pp`
  - pass/fail

## Guardrail Check (Required Fields)
- Margin proxy:
  - control value
  - treatment value
  - pass/fail
- Cohort quality (`n_customers`):
  - control value
  - treatment value
  - pass/fail
- Credit-like/refund proxy:
  - control value
  - treatment value
  - pass/fail

## Decision Logic
- `Scale` when KPI thresholds are met and all guardrails pass.
- `Iterate` when directional improvement exists but thresholds are not met and guardrails pass.
- `Pause` when any critical guardrail fails or KPI deltas are adverse.

## Next Actions
- If `Scale`: expand audience in controlled increments and keep holdout.
- If `Iterate`: adjust one lever only (offer, timing, or creative) and rerun.
- If `Pause`: stop exposure and document failure mode for the next cycle.

## Week-2 Readout Output Bundle
- Updated recommendation line in decision memo.
- KPI/guardrail evidence table attached in the experiment ticket.
- Next checkpoint date and owner assignment logged.
