# CHART TALK TRACKS

## Use This With
- Learning map: `docs/TEACHING_HUB.md`
- Caption quality check: `docs/TEACHING_ANSWER_KEY.md`
- Definition guardrails: `docs/COHORT_DEFENSE_CARD.md`
- Story artifact: `exports/cohort_retention_story.html`

## Chart 1: Logo Retention Heatmap
- Setup: This chart answers how repeat purchase propensity decays by cohort month over months 0..6.
- Observation template 1: "Cohort `[YYYY-MM]` is `[X%]` at M2 vs `[Y%]` for `[YYYY-MM]`, so repeat intensity differs by acquisition window."
- Observation template 2: "The sharpest drop is M`[a]` to M`[b]`, so early lifecycle is the highest-leverage save window."
- Caveat: Directional, not causal; cohort composition can explain part of the gap.
- Next action: Prioritize lifecycle intervention timing where decay is steepest.

## Chart 2: Family Impact Scatter (M2)
- Setup: This chart answers which first-order families combine weak repeat (x) and weak value after credits (y) at month 2.
- Observation template 1: "`[Family]` sits bottom-right (high logo, low net proxy), signaling refund drag despite repeat intent."
- Observation template 2: "`[Family]` sits top-left (low logo, decent net proxy), signaling repeat weakness more than value loss."
- Caveat: Directional, not causal; points use observed M2 only and suppress tiny-n families (`n<50`).
- Next action: Pick 2-3 bottom-left / bottom-right families for returns-mitigation + replenishment tests.
- Memo bridge: `docs/DECISION_MEMO_1PAGE.md` -> `## Plays`.

## Chart 3: M2 Retention by first_product_family
- Setup: This chart answers which first-order families over/under-index at month 2 and whether sample sizes are decision-safe.
- Observation template 1: "`[TopFamily]` at `[X%]` vs `[BottomFamily]` at `[Y%]` yields a `[Delta pp]` prioritization gap."
- Observation template 2: "`[FamilyName]` has `n=[N]`; confidence is higher/lower depending on sample size."
- Caveat: Directional, not causal; family differences may reflect unobserved mix effects.
- Next action: Start tests in high-volume, low-M2 families first.
- Memo bridge: `docs/DECISION_MEMO_1PAGE.md` -> `## Top 3 Target Families`.
