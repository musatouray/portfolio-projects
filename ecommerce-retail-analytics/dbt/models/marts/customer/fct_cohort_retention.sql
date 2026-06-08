-- Cohort retention fact table tracking customer retention by acquisition month
-- Use this for retention curves, cohort comparisons, and identifying improving/declining acquisition quality
-- Includes period-level revenue and orders for cohort revenue analysis

with customer_cohorts as (
    -- Assign customers to cohorts based on their first order month
    select
        customer_unique_id,
        date_trunc('month', first_order_date) as cohort_month
    from {{ ref('dim_customers') }}
    where first_order_date is not null
),

orders as (
    -- Get order details for revenue and order count calculations
    select
        customer_unique_id,
        order_id,
        date_trunc('month', order_date) as activity_month,
        total_payment_value
    from {{ ref('int_orders_enriched') }}
    where date_trunc('month', order_date) < date_trunc('month', current_date) -- Exclude current month to avoid partial data
),

customer_activity as (
    -- Get the months in which each customer was active (placed an order)
    select
        customer_unique_id,
        activity_month
    from orders
    group by 1, 2
),

cohort_activity as (
    -- Join cohorts with activity to calculate active customers, orders, and revenue per cohort and period
    select
        cc.cohort_month,
        o.activity_month,
        datediff('month', cc.cohort_month, o.activity_month) as period_number,
        count(distinct o.customer_unique_id) as active_customers,
        count(distinct o.order_id) as period_orders,
        sum(o.total_payment_value) as period_revenue
    from customer_cohorts cc
    inner join orders o using (customer_unique_id)
    where o.activity_month is not null
      and datediff('month', cc.cohort_month, o.activity_month) >= 0 -- Only consider activity after cohort month
    group by 1, 2, 3
),

cohort_sizes as (
    -- Calculate the size of each cohort
    select
        cohort_month,
        count(distinct customer_unique_id) as cohort_size
    from customer_cohorts
    group by 1
),

retention_metrics as (
    -- Calculate retention and churn rates for each cohort and period
    select
        ca.cohort_month,
        ca.period_number,
        ca.active_customers,
        ca.period_orders,
        ca.period_revenue,
        cs.cohort_size,
        case when cs.cohort_size > 0 then (ca.active_customers::float / cs.cohort_size) * 100 else 0 end as retention_rate
    from cohort_activity ca
    left join cohort_sizes cs using (cohort_month)
)

select
    {{ dbt_utils.generate_surrogate_key(['cohort_month', 'period_number']) }} as cohort_retention_key,
    -- FK to dim_cohorts
    {{ dbt_utils.generate_surrogate_key(['cohort_month']) }} as cohort_key,
    cohort_month,
    period_number,
    active_customers,
    cohort_size,
    round(retention_rate, 2) as retention_rate,
    round(100 - retention_rate, 2) as churn_rate,
    period_orders,
    round(period_revenue, 2) as period_revenue,

    -- Metadata
    current_timestamp() as created_at,
    current_timestamp() as updated_at
from retention_metrics