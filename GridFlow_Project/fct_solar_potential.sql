{{
  config(
    materialized        = 'incremental',
    incremental_strategy= 'merge',
    unique_key          = ['date_day', 'lat_bin', 'lon_bin'],
    partition_by        = {
      'field': 'date_day',
      'data_type': 'date',
      'granularity': 'month'
    },
    description         = 'Daily solar generation potential aggregated to 1° grid cells'
  )
}}

with solar as (

    select * from {{ ref('stg_nrel__solar_resource') }}

    {% if is_incremental() %}
      where date_day > (
        select coalesce(max(date_day), date('{{ var("start_date") }}'))
        from {{ this }}
      )
    {% endif %}

),

gridded as (

    select
        date_day,

        -- Bin to 1° × 1° grid cells
        floor(latitude)  as lat_bin,
        floor(longitude) as lon_bin,

        -- Daily irradiance sums (Wh/m² → kWh/m²)
        round(sum(ghi_wm2) / 1000, 3)           as daily_ghi_kwh_m2,
        round(sum(dni_wm2) / 1000, 3)           as daily_dni_kwh_m2,
        round(sum(dhi_wm2) / 1000, 3)           as daily_dhi_kwh_m2,

        -- Average meteorological conditions
        round(avg(air_temp_c),       1)         as avg_temp_c,
        round(avg(wind_speed_ms),    2)         as avg_wind_ms,
        round(avg(clearness_index),  3)         as avg_clearness_index,

        -- Peak irradiance hour
        max(ghi_wm2)                            as peak_ghi_wm2,

        -- Approximate PV yield (15% system efficiency, standard test conditions)
        -- kWh/kWp/day  =  GHI (kWh/m²) × panel_efficiency
        round(sum(ghi_wm2) / 1000 * 0.15, 3)   as est_pv_yield_kwh_kwp,

        count(*)                                as hours_with_data

    from solar
    group by 1, 2, 3

)

select
    *,
    current_timestamp()    as _dbt_updated_at
from gridded
