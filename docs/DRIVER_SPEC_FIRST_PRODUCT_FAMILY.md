# DRIVER SPEC ? first_product_family (v1.2 binding)

## Cohort universe
Non-guest customers with >=1 valid purchase.

## Frozen rules
- H=6 (months_since_first 0..6)
- is_valid_purchase = (order_gross > 0) & (is_cancel_invoice == 0)
- is_credit_like = (is_cancel_invoice==1) OR (order_net_proxy < 0)
- NonMerch families: Fees_NonMerch, Adjustments_NonMerch
- Exclude *_NonMerch from first_product_family competition unless no alternatives exist (fallback Other)

## Definition
For each non-guest customer:
1) Find first valid order (tie-break: earliest order_ts then smallest order_id).
2) Compute gross revenue by product_family within that order using line_amount_gross.
3) Exclude *_NonMerch families from competition unless no other families exist.
4) first_product_family = family with max gross.
   Tie-break: higher items_count within family, else alphabetical.

## Chart 3 formula (explicit)
M2 retention by first_product_family =
mean(is_retained_logo) where months_since_first == 2, grouped by family
(top 8 by unique customers + Other), annotate n_customers.
