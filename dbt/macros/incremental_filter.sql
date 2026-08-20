{#
    Incremental filter macro for Snowflake-compatible incremental loads.

    Usage: Call incremental_max_date_cte() at the top of your CTEs, then use
           incremental_where_clause() in the WHERE clause of your source CTE.

    Example:
        with
        {{ incremental_max_date_cte('order_date') }}

        source as (
            select * from {{ ref('upstream') }}
            {{ incremental_where_clause('order_date') }}
        )
#}

{% macro incremental_max_date_cte(column_name, lookback_days=3) -%}
    {%- if is_incremental() -%}
_incremental_cutoff as (
    select dateadd(day, -{{ lookback_days }}, max({{ column_name }})) as cutoff_date
    from {{ this }}
),
    {%- endif -%}
{%- endmacro %}

{% macro incremental_where_clause(column_name) -%}
    {%- if is_incremental() -%}
    where {{ column_name }} > (select cutoff_date from _incremental_cutoff)
    {%- endif -%}
{%- endmacro %}