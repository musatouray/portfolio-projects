{% macro generate_int_surrogate_key(field_list) %}

{%- set fields = [] -%}
{%- for field in field_list -%}
    {%- do fields.append("coalesce(cast(" ~ field ~ " as varchar), '')") -%}
    {%- if not loop.last -%}
        {%- do fields.append("'-'") -%}
    {%- endif -%}
{%- endfor -%}

-- Shifting the unsigned 64-bit value into a signed 64-bit BIGINT range for Power BI
CAST(MD5_NUMBER_LOWER64(concat({{ fields | join(', ') }})) - 9223372036854775808 AS BIGINT)

{%- endmacro %}
