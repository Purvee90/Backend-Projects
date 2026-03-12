{{
  config(
    materialized = 'view',
    description  = 'Cleaned OPSD 60-min electricity load time series'
  )
}}

with source as (

    select * from {{ source('energy_staging', 'raw_opsd_load') }}

),

renamed as (

    select
        -- ── Timestamps ────────────────────────────────────────────────────
        cast(utc_timestamp as timestamp)   as utc_timestamp,
        cet_cest_timestamp,

        -- ── Germany ───────────────────────────────────────────────────────
        cast(de_load_actual_entsoe_transparency    as float64)  as de_load_actual_mw,
        cast(de_load_forecast_entsoe_transparency  as float64)  as de_load_forecast_mw,

        -- ── Austria ───────────────────────────────────────────────────────
        cast(at_load_actual_entsoe_transparency    as float64)  as at_load_actual_mw,
        cast(at_load_forecast_entsoe_transparency  as float64)  as at_load_forecast_mw,

        -- ── Great Britain ─────────────────────────────────────────────────
        cast(gb_gbn_load_actual_entsoe_transparency   as float64)  as gb_load_actual_mw,
        cast(gb_gbn_load_forecast_entsoe_transparency as float64)  as gb_load_forecast_mw,

        -- ── Metadata ──────────────────────────────────────────────────────
        _ingested_at,
        _source_file

    from source
    where utc_timestamp is not null

),

with_derived as (

    select
        *,

        -- Date parts for easy partitioning / filtering
        date(utc_timestamp)                            as date_day,
        extract(year  from utc_timestamp)              as year,
        extract(month from utc_timestamp)              as month,
        extract(hour  from utc_timestamp)              as hour_of_day,
        format_date('%A', date(utc_timestamp))         as day_of_week,

        -- Forecast error (Germany)
        safe_divide(
            de_load_actual_mw - de_load_forecast_mw,
            de_load_forecast_mw
        ) * 100                                        as de_forecast_error_pct

    from renamed

)

select * from with_derived
