-- macros/generate_schema_name.sql
-- Ensures dbt respects the custom schema names in dbt_project.yml
-- instead of prepending the target schema to every model.

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}


-- macros/safe_divide.sql
{% macro safe_divide(numerator, denominator) %}
    case
        when ({{ denominator }}) = 0 or ({{ denominator }}) is null
        then null
        else ({{ numerator }}) / ({{ denominator }})
    end
{% endmacro %}


-- macros/date_spine_hours.sql
-- Generates a spine of hourly timestamps between start and end
{% macro date_spine_hours(start_date, end_date) %}
    with hour_spine as (
        {{ dbt_utils.date_spine(
            datepart="hour",
            start_date="cast('" ~ start_date ~ "' as timestamp)",
            end_date="cast('" ~ end_date ~ "' as timestamp)"
        ) }}
    )
    select date_hour from hour_spine
{% endmacro %}


-- macros/assert_column_not_negative.sql
-- Generic test macro: assert that column values are not negative
{% test assert_not_negative(model, column_name) %}
    select {{ column_name }}, count(*) as n_violations
    from {{ model }}
    where {{ column_name }} < 0
    group by 1
    having count(*) > 0
{% endtest %}
