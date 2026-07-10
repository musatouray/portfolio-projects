{% macro generate_int_surrogate_key(field_list) %}
{#
    Generates a 64-bit integer surrogate key using MD5_NUMBER_LOWER64.

    This macro is a drop-in replacement for dbt_utils.generate_surrogate_key that produces
    integers instead of 32-character hex strings, optimized for Power BI memory efficiency.

    Design Decision:
    - Uses MD5_NUMBER_LOWER64 which extracts the lower 64 bits of an MD5 hash as BIGINT
    - MD5 is a standardized algorithm (RFC 1321) guaranteed stable across Snowflake versions
    - Concatenates fields with '-' delimiter to prevent collisions (matches dbt_utils pattern)
    - Coalesces NULL values to empty strings for consistency with dbt_utils behavior

    Why MD5_NUMBER_LOWER64 over HASH():
    - Snowflake's HASH() is NOT guaranteed stable across releases
    - MD5 algorithm is standardized and will not change
    - Surrogate keys must be deterministic across time for incremental models

    Tradeoff accepted: Platform-specific implementation (Snowflake-only) in exchange for
    ~70% memory reduction on surrogate key columns in Power BI semantic models.

    Usage:
        {{ generate_int_surrogate_key(['order_id', 'product_id']) }}
        -- Produces: MD5_NUMBER_LOWER64(concat(coalesce(cast(order_id as varchar), ''), '-', ...))

    Arguments:
        field_list: List of column names to include in the hash

    Returns:
        A Snowflake MD5_NUMBER_LOWER64() expression producing a BIGINT surrogate key
#}

{%- set fields = [] -%}
{%- for field in field_list -%}
    {%- do fields.append("coalesce(cast(" ~ field ~ " as varchar), '')") -%}
    {%- if not loop.last -%}
        {%- do fields.append("'-'") -%}
    {%- endif -%}
{%- endfor -%}

MD5_NUMBER_LOWER64(concat({{ fields | join(', ') }}))

{%- endmacro %}
