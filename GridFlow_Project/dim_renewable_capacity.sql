{{
  config(
    materialized = 'table',
    description  = 'Renewable generation capacity aggregated by country and technology'
  )
}}

/*
  Joins cleaned plant registry with country reference seed data.
  Produces a wide analytical table for capacity planning / dashboards.
*/

with plants as (

    select * from {{ ref('stg_opsd__renewable_plants') }}
    where is_active = true

),

country_ref as (

    select * from {{ ref('country_codes') }}

),

capacity_by_tech as (

    select
        p.country_code,
        p.energy_source_l2                          as technology,
        p.capacity_class,
        count(*)                                    as plant_count,
        round(sum(p.capacity_mw), 2)                as total_capacity_mw,
        round(avg(p.capacity_mw), 3)                as avg_capacity_mw,
        round(min(p.capacity_mw), 3)                as min_plant_mw,
        round(max(p.capacity_mw), 2)                as max_plant_mw,
        min(p.commissioning_date)                   as earliest_commission_date,
        max(p.commissioning_date)                   as latest_commission_date

    from plants p
    group by 1, 2, 3

),

with_share as (

    select
        c.*,
        r.country_name,
        r.region,

        -- Share of total capacity within each country
        round(
            safe_divide(c.total_capacity_mw,
                sum(c.total_capacity_mw) over (partition by c.country_code)
            ) * 100, 2
        )                                           as pct_of_country_capacity,

        -- Share within region
        round(
            safe_divide(c.total_capacity_mw,
                sum(c.total_capacity_mw) over (partition by r.region)
            ) * 100, 2
        )                                           as pct_of_region_capacity

    from capacity_by_tech c
    left join country_ref r on c.country_code = r.country_code

)

select
    *,
    current_timestamp()    as _dbt_updated_at
from with_share
order by country_code, total_capacity_mw desc
