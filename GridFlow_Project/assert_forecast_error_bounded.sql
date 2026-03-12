-- tests/assert_forecast_error_bounded.sql
-- Singular test: MAPE should stay below 30% on average.
-- A persistent violation signals a data quality or modelling problem.

select
    country_code,
    avg(mape_pct)          as avg_mape,
    max(mape_pct)          as max_mape,
    count(*)               as n_days
from {{ ref('fct_daily_load') }}
where mape_pct is not null
group by 1
having avg(mape_pct) > 30   -- fail if any country exceeds 30% avg MAPE
