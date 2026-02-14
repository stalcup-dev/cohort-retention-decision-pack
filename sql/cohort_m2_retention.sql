-- Cohort M2 retention view by first_product_family
-- Assumes customer-month grain source compatible with customer_month_activity.csv fields.

with base as (
    select
        first_product_family,
        customer_id,
        months_since_first,
        is_retained_logo,
        gross_revenue_valid,
        net_revenue_proxy_total
    from analytics.customer_month_activity
    where months_since_first in (0, 2)
),
cohort_denominator as (
    select
        first_product_family,
        sum(case when months_since_first = 0 then gross_revenue_valid else 0 end) as denom_m0_gross
    from base
    group by 1
),
m2_logo as (
    select
        first_product_family,
        avg(case when months_since_first = 2 then cast(is_retained_logo as float) end) as m2_logo_retention,
        count(distinct case when months_since_first = 0 then customer_id end) as n_customers
    from base
    group by 1
),
m2_net as (
    select
        b.first_product_family,
        case
            when d.denom_m0_gross = 0 then null
            else sum(case when b.months_since_first = 2 then b.net_revenue_proxy_total else 0 end) / d.denom_m0_gross
        end as m2_net_proxy_retention
    from base b
    join cohort_denominator d
      on b.first_product_family = d.first_product_family
    group by 1, d.denom_m0_gross
)
select
    l.first_product_family as family_group,
    l.n_customers,
    l.m2_logo_retention,
    n.m2_net_proxy_retention,
    (n.m2_net_proxy_retention - l.m2_logo_retention) * 100.0 as gap_pp
from m2_logo l
join m2_net n
  on l.first_product_family = n.first_product_family
order by l.m2_logo_retention asc, n.m2_net_proxy_retention asc, l.n_customers desc;
