-- Cohort dimension table grouping customers by their first purchase month
-- Use this to slice metrics by acquisition cohort in Power BI dashboards
-- Note: cohort_key is generated from cohort_month using dbt_utils.generate_surrogate_key
-- and must match the cohort_key FK in dim_customers for proper joins
-- Fact columns (revenue, orders) are in fct_cohort_retention for period-level analysis

with customer_cohorts as (
    -- Assign customers to cohorts based on their first order month
    select
        customer_unique_id,
        date_trunc('month', first_order_date) as cohort_month
    from {{ ref('dim_customers') }}
    where first_order_date is not null
),

cohort_sizes as (
    -- Calculate the size of each cohort
    select
        cohort_month,
        count(distinct customer_unique_id) as cohort_size
    from customer_cohorts
    group by 1
)

select
    {{ dbt_utils.generate_surrogate_key(['cohort_month']) }} as cohort_key,
    cohort_month,
    to_char(cohort_month, 'Mon YYYY') as cohort_month_name,
    year(cohort_month) as cohort_year,
    year(cohort_month) || '-Q' || quarter(cohort_month) as year_quarter,
    cohort_size,

    -- Metadata
    current_timestamp as created_at,
    current_timestamp as updated_at
from cohort_sizes