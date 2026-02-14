# CHART TALK TRACKS

## Use This With
- Definition guardrails: `docs/COHORT_DEFENSE_CARD.md`
- Story artifact: `exports/cohort_retention_story.html`
- Decision memo: `docs/DECISION_MEMO_1PAGE.md`

## Chart 1: Logo Retention Heatmap
- Setup: This chart answers how repeat purchase propensity decays by cohort month over months 0..6.
- Observation template 1: "Cohort `[YYYY-MM]` is `[X%]` at M2 vs `[Y%]` for `[YYYY-MM]`, so repeat intensity differs by acquisition window."
- Observation template 2: "The sharpest drop is M`[a]` to M`[b]`, so early lifecycle is the highest-leverage save window."
- Caveat: Directional, not causal; cohort composition can explain part of the gap.
- Next action: Prioritize lifecycle intervention timing where decay is steepest.

## Chart 2: Net Retention Proxy Curves (3 Cohorts)
- Setup: This chart answers how refund-aware value retention evolves across lifecycle months for representative cohorts.
- Observation template 1: "`[Cohort A]` starts at `[X]` and trends to `[Y]` by M6, indicating `[faster/slower]` value decay."
- Observation template 2: "Relative spread between `[cohort_low]` and `[cohort_high]` highlights expected volatility bands for planning."
- Caveat: Directional, not causal; curves are monthly proxy ratios with denominator guardrails and observed-month masking.
- Next action: Use curve trajectory to set realistic lift expectations and interim checkpoints.
- Memo bridge: `docs/DECISION_MEMO_1PAGE.md` -> `## Impact Model (scenario, not observed)`.

## Chart 3: M2 Retention by first_product_family
- Setup: This chart answers which first-order families over/under-index at month 2 and whether sample sizes are decision-safe.
- Observation template 1: "`[TopFamily]` at `[X%]` vs `[BottomFamily]` at `[Y%]` yields a `[Delta pp]` prioritization gap."
- Observation template 2: "`[FamilyName]` has `n=[N]`; confidence is higher/lower depending on sample size."
- Caveat: Directional, not causal; family differences may reflect unobserved mix effects.
- Next action: Start tests in high-volume, low-M2 families first.
- Memo bridge: `docs/DECISION_MEMO_1PAGE.md` -> `## Top 3 Target Families`.
