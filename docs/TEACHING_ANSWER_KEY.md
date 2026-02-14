# TEACHING ANSWER KEY

## Use This With
- Learning map: `docs/TEACHING_HUB.md`
- Practice scripts: `docs/CHART_TALK_TRACKS.md`
- Source visuals: `exports/cohort_retention_story.html`
- Deep walkthrough: `docs/TEACHING_REPORT.md`

## Chart 1: Logo Retention Heatmap
- Perfect caption: "Logo retention starts at ~100% in month 0 by cohort construction, then decays at different speeds across cohorts; the steepest early declines indicate where lifecycle recovery interventions should be timed."
- Common wrong interpretation 1: "Darker cells mean larger cohorts." (Wrong: color here encodes retention rate, not cohort size.)
- Common wrong interpretation 2: "Month-0 values prove campaign success." (Wrong: month 0 is structurally high by cohort definition.)
- Correct caveat: "Interpret differences as directional cohort patterns, not causal effects."

## Chart 2: Net Retention Proxy Curves
- Perfect caption: "Net retention proxy compares refund-aware monthly value to each cohort's fixed month-0 gross baseline, revealing whether value holds or erodes after accounting for credits."
- Common wrong interpretation 1: "A line below 1.0 means negative profit." (Wrong: it means lower net proxy vs baseline, not profit statement.)
- Common wrong interpretation 2: "Excluded cohorts are poor performers." (Wrong: they are excluded only because denominator equals zero.)
- Correct caveat: "This is a proxy ratio under frozen definitions, directional for prioritization."
- Memo link: Chart 2 supports `docs/DECISION_MEMO_1PAGE.md` -> `## Plays` (refund drag / returns mitigation).

## Chart 3: M2 Retention by first_product_family
- Perfect caption: "Month-2 logo retention differs by first_product_family, and n-labels identify which family gaps are reliable enough to prioritize for test sequencing."
- Common wrong interpretation 1: "Highest bar means guaranteed causal lift if we push that family." (Wrong: descriptive segmentation only.)
- Common wrong interpretation 2: "Small-n families with high bars should be top priority." (Wrong: low sample sizes reduce decision confidence.)
- Correct caveat: "Use family gaps as directional targeting signals and validate via experiments."
- Memo link: Chart 3 supports `docs/DECISION_MEMO_1PAGE.md` -> `## Top 3 Target Families`.
