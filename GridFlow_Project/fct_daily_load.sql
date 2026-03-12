{{
  config(
    materialized        = 'incremental',
    incremental_strategy= 'merge',
    unique_key          = ['date_day', 'country_code'],
    partition_by        = {
      'field': 'date_day',
      'data_type': 'date',
      'granularity': 'month'
    },
    cluster_by          = ['country_code'],
    description         = 'Daily electricity load KPIs by country'
  )
}}

/*
  Aggregates hourly OPSD load observations to daily metrics per country.
  Supports incremental runs — only processes new/changed dates.
*/

with hourly_load as (

    select * from {{ ref('stg_opsd__load') }}

    {% if is_incremental() %}
      -- Only process dates not yet in the mart or updated since last run
      where date_day > (
        select coalesce(max(date_day), date('{{ var("start_date") }}'))
        from {{ this }}
      )
    {% endif %}

),

-- Unpivot countries into rows for extensibility
unpivoted as (

    select date_day, utc_timestamp, 'DE' as country_code,
           de_load_actual_mw   as load_actual_mw,
           de_load_forecast_mw as load_forecast_mw
    from hourly_load where de_load_actual_mw is not null

    union all

    select date_day, utc_timestamp, 'AT',
           at_load_actual_mw, at_load_forecast_mw
    from hourly_load where at_load_actual_mw is not null

    union all

    select date_day, utc_timestamp, 'GB',
           gb_load_actual_mw, gb_load_forecast_mw
    from hourly_load where gb_load_actual_mw is not null

),

daily_agg as (

    select
        date_day,
        country_code,

        -- ── Volume ────────────────────────────────────────────────────────
        round(sum(load_actual_mw)  / 1000, 2)   as total_load_gwh,
        round(avg(load_actual_mw),         1)   as avg_load_mw,
        round(min(load_actual_mw),         1)   as min_load_mw,
        round(max(load_actual_mw),         1)   as max_load_mw,
        round(max(load_actual_mw)
            - min(load_actual_mw),             1) as load_range_mw,

        -- ── Forecast accuracy ─────────────────────────────────────────────
        round(avg(
            safe_divide(
                abs(load_actual_mw - load_forecast_mw),
                load_actual_mw
            ) * 100
        ), 2)                                   as mape_pct,

        round(sqrt(avg(
            power(load_actual_mw - load_forecast_mw, 2)
        )), 1)                                  as rmse_mw,

        -- ── Peaks ─────────────────────────────────────────────────────────
        max(case when
            load_actual_mw = max(load_actual_mw) over (partition by date_day, country_code)
            then utc_timestamp end)             as peak_hour_utc,

        -- ── Completeness ──────────────────────────────────────────────────
        count(*)                                as obs_count,
        count(*) / 24.0                         as data_completeness_ratio

    from unpivoted
    group by 1, 2

)

select
    *,
    current_timestamp()                         as _dbt_updated_at
from daily_agg
