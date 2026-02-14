# Chart 2 Selection Contract (v1.2)

## Scope
This contract defines how `Chart 2: Net retention proxy curves (3 cohorts max)` selects cohorts for plotting.

## Eligibility Rules
- Source table: `data_processed/chart2_net_proxy_curves.csv`.
- Cohort eligibility requires:
  - `n_customers_m0 >= MIN_COHORT_N`
  - `denom_month0_gross_valid > 0`
  - cohort month has full H window eligibility from the build step.
- Cohorts with null `m2_logo_retention` are excluded from ranking.

## Plot-Floor Preference + Fallback
- Preferred pool: eligible cohorts with `n0 >= MIN_PLOT_COHORT_N`.
- If preferred pool has at least 3 cohorts: select from preferred pool.
- If preferred pool has fewer than 3 cohorts: `used_fallback=True` and select from all eligible cohorts.

## Ranking + Tie-Breakers
- Ranking signal: ascending `m2_logo_retention`.
- Deterministic tie-breaker: ascending `cohort_month`.
- Selection strategy from ranked list: `bottom`, `mid`, `top`.
- If fewer than 3 cohorts are available, select all available in ranked order.

## Selection Outputs
- Receipts summary (`data_processed/scope_receipts.json`):
  - `chart2_selected_cohorts`
  - `chart2_selected_count`
  - `chart2_used_fallback`
  - `chart2_plot_pool_count`
  - `chart2_selected_min_n0`
  - `chart2_policy`
- Candidate table (`data_processed/chart2_selection_candidates.csv`):
  - `cohort_month, n0, denom_month0_gross_valid, m2_logo_retention`
  - `plot_floor_pass, eligible_cohort, selected_for_plot, selection_reason, rank_logo_m2`

## Invariants Enforced
- `selected_count` is between 1 and 3.
- Selected cohorts are a subset of eligible cohorts.
- If `used_fallback=False`, all selected rows have `plot_floor_pass=True`.
- Selected cohort lists match across:
  - `scope_receipts.json`
  - `chart2_selection_candidates.csv`
  - `chart2_net_proxy_curves.csv`

## Validators
- Artifact validator: `scripts/validate_chart2_selection_artifacts.py`
- Story contract checker: `scripts/verify_story_contract.py`

