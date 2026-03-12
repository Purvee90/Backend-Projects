-- tests/assert_capacity_shares_sum_to_100.sql
-- The sum of pct_of_country_capacity for each country should be ~100 %.
-- Tolerance of ±0.1 % allows for floating-point rounding.

select
    country_code,
    round(sum(pct_of_country_capacity), 2)  as share_sum
from {{ ref('dim_renewable_capacity') }}
group by 1
having abs(sum(pct_of_country_capacity) - 100) > 0.1
