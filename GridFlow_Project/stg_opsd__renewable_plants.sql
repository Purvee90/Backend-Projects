{{
  config(
    materialized = 'view',
    description  = 'Cleaned OPSD EU renewable power plant registry'
  )
}}

with source as (

    select * from {{ source('energy_staging', 'raw_opsd_renewable_plants') }}

),

cleaned as (

    select
        -- ── Identity ──────────────────────────────────────────────────────
        coalesce(id, cast(row_number() over () as string))  as plant_id,

        -- ── Classification ────────────────────────────────────────────────
        upper(trim(country))                        as country_code,
        initcap(trim(energy_source_level_1))        as energy_source_l1,
        initcap(trim(energy_source_level_2))        as energy_source_l2,
        initcap(trim(energy_source_level_3))        as energy_source_l3,
        initcap(trim(technology))                   as technology,
        trim(data_source)                           as data_source,

        -- ── Capacity ──────────────────────────────────────────────────────
        cast(capacity as float64)                   as capacity_mw,
        case
            when cast(capacity as float64) < 0.1   then 'micro'
            when cast(capacity as float64) < 1      then 'small'
            when cast(capacity as float64) < 10     then 'medium'
            when cast(capacity as float64) < 100    then 'large'
            else                                         'utility'
        end                                         as capacity_class,

        -- ── Geography ─────────────────────────────────────────────────────
        cast(lat as float64)                        as latitude,
        cast(lon as float64)                        as longitude,
        trim(municipality)                          as municipality,
        trim(nuts_1_region)                         as nuts_1_region,

        -- ── Lifecycle ─────────────────────────────────────────────────────
        safe_cast(commissioning_date   as date)     as commissioning_date,
        safe_cast(decommissioning_date as date)     as decommissioning_date,
        case
            when decommissioning_date is null
              or safe_cast(decommissioning_date as date) > current_date()
            then true
            else false
        end                                         as is_active,

        -- ── Metadata ──────────────────────────────────────────────────────
        trim(comment)    as comment,
        _ingested_at,
        _source_file

    from source
    where capacity is not null
      and cast(capacity as float64) >= {{ var('capacity_min_mw') }}

)

select * from cleaned
