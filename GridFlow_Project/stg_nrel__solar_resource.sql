{{
  config(
    materialized = 'view',
    description  = 'Cleaned NREL solar resource data'
  )
}}

with source as (

    select * from {{ source('energy_staging', 'raw_nrel_solar_resource') }}

),

cleaned as (

    select
        -- ── Time ──────────────────────────────────────────────────────────
        cast(period_start as timestamp)              as period_start,
        cast(period_end   as timestamp)              as period_end,
        date(cast(period_start as timestamp))        as date_day,
        extract(hour from cast(period_start as timestamp))  as hour_of_day,

        -- ── Location ──────────────────────────────────────────────────────
        cast(latitude  as float64)                   as latitude,
        cast(longitude as float64)                   as longitude,
        cast(elevation_m as float64)                 as elevation_m,

        -- ── Irradiance ────────────────────────────────────────────────────
        cast(ghi_wm2 as float64)                     as ghi_wm2,
        cast(dni_wm2 as float64)                     as dni_wm2,
        cast(dhi_wm2 as float64)                     as dhi_wm2,

        -- Clearness index: ratio of GHI to extraterrestrial irradiance
        -- (approximated as GHI / 1361; true ETR requires sun position)
        safe_divide(cast(ghi_wm2 as float64), 1361)  as clearness_index,

        -- ── Meteorology ───────────────────────────────────────────────────
        cast(air_temperature_c      as float64)      as air_temp_c,
        cast(wind_speed_ms          as float64)      as wind_speed_ms,
        cast(surface_pressure_mbar  as float64)      as pressure_mbar,

        -- ── Metadata ──────────────────────────────────────────────────────
        _ingested_at,
        _source_file

    from source
    where period_start is not null
      and cast(ghi_wm2 as float64) >= 0   -- irradiance cannot be negative

)

select * from cleaned
