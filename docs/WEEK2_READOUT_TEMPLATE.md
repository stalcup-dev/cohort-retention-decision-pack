# Week 2 Readout Template - Retention Experiment Decision

## Use This With
- Learning map: `docs/TEACHING_HUB.md`
- Experiment setup: `docs/EXPERIMENT_BRIEF_SAMPLE.md`
- Teaching module: `private_teaching/module_experiment_readout_sql.html`

## Executive Summary
- Recommendation: `Scale` / `Pause` / `Iterate`
- Basis: M2 logo retention, M2 net proxy retention, and guardrails
- Confidence: `High` / `Medium` / `Low`

## Experiment Snapshot
| family | variant | control_n | treatment_n | status |
|---|---|---:|---:|---|
| `<TARGET_FAMILY>` | `<VARIANT_NAME>` | `<N_CTRL>` | `<N_TRT>` | `<RUNNING/COMPLETE>` |

## KPI Readout (Control vs Treatment)
| metric | control | treatment | delta | threshold | pass |
|---|---:|---:|---:|---:|---|
| M2 logo retention | `<C_LOGO>` | `<T_LOGO>` | `<DELTA_LOGO>` | `+X pp` | `<Y/N>` |
| M2 net proxy retention | `<C_NET>` | `<T_NET>` | `<DELTA_NET>` | `+Y pp` | `<Y/N>` |
| net-minus-logo gap (pp) | `<C_GAP>` | `<T_GAP>` | `<DELTA_GAP>` | `toward >= 0` | `<Y/N>` |

## Guardrail Check
| guardrail | control | treatment | status |
|---|---:|---:|---|
| margin proxy | `<C_MARGIN>` | `<T_MARGIN>` | `<PASS/FAIL>` |
| cohort quality (`n_customers`) | `<C_QUAL>` | `<T_QUAL>` | `<PASS/FAIL>` |
| credit-like/refund proxy | `<C_CREDIT>` | `<T_CREDIT>` | `<PASS/FAIL>` |

## Decision Logic
- `Scale` when KPI thresholds are met and all guardrails pass.
- `Iterate` when directional improvement exists but thresholds are not met and guardrails pass.
- `Pause` when any critical guardrail fails or KPI deltas are adverse.

## Next Actions
- If `Scale`: expand audience to `<PERCENT>%`, keep holdout.
- If `Iterate`: apply one change only (`offer`, `timing`, or `creative`) and rerun.
- If `Pause`: stop exposure and document failure mode.

## Example Filled Row (Illustrative)
| family | variant | control_n | treatment_n | status |
|---|---|---:|---:|---|
| Seasonal | Bundle + winback v1 | 220 | 227 | COMPLETE |
