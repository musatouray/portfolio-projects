{% macro generate_schema_name(custom_schema_name, node) -%}
    {#
        Override dbt's default schema naming to support:
        1. Dev/Prod: Use custom schema names directly (STAGING, INTERMEDIATE, MARTS)
        2. CI: Prefix with CI schema for isolation (CI_PR_1_INTERMEDIATE, CI_PR_1_MARTS)

        Note: Staging models always go to STAGING schema (shared silver layer)
    #}
    {%- set default_schema = target.schema -%}

    {%- if custom_schema_name is none -%}
        {{ default_schema | upper }}

    {%- elif target.name == 'ci' and custom_schema_name | upper not in ['STAGING'] -%}
        {# CI environment: prefix intermediate/marts with CI schema for isolation #}
        {{ default_schema | upper }}_{{ custom_schema_name | upper }}

    {%- else -%}
        {# Dev/Prod or Staging: use custom schema directly #}
        {{ custom_schema_name | upper }}

    {%- endif -%}
{%- endmacro %}
