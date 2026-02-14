from __future__ import annotations

HORIZON_H = 6
MIN_COHORT_N = 50
MIN_PLOT_COHORT_N = 200
MIN_SKU_N = 30
TOPK_SKUS_PER_FAMILY = 10
RIGHT_CENSOR_MODE = "missing_not_zero"
OBSERVED_ONLY = True

# Family priority scoring defaults for decision ranking.
PRIORITY_W1 = 0.5  # logo retention gap weight
PRIORITY_W2 = 0.5  # net proxy retention gap weight
