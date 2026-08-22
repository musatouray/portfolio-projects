-- Customer retention fact table at customer × period grain
-- Enables cohort retention analysis with filtering by customer dimensions
-- Sparse model: only periods with customer activity (Power BI calculates retention %)
--
-- Relationships:
--   customer_key → dim_customers (state, city, cohort_month)
--   cohort_date_key → dim_dates (role-playing for cohort filtering)
--   period_date_key → dim_dates (role-playing for period filtering)

{{ config(
    materialized='table',
    cluster_by=['cohort_month', 'cohort_period']
) }}

WITH orders AS (
    SELECT
        customer_unique_id,
        order_id,
        order_date,
        total_payment_value AS revenue,
        DATE_TRUNC('MONTH', order_date) AS order_month
    FROM {{ ref('int_orders_enriched') }}
    WHERE order_status NOT IN ('canceled', 'unavailable')
),

-- Customer cohort assignment (first purchase month)
customer_cohorts AS (
    SELECT
        customer_unique_id,
        MIN(order_month) AS cohort_month
    FROM orders
    GROUP BY 1
),

-- Aggregate customer activity by period (months since cohort)
customer_periods AS (
    SELECT
        o.customer_unique_id,
        cc.cohort_month,
        o.order_month AS period_month,
        DATEDIFF('MONTH', cc.cohort_month, o.order_month) AS cohort_period,
        COUNT(DISTINCT o.order_id) AS period_orders,
        COALESCE(SUM(o.revenue), 0) AS period_revenue
    FROM orders o
    INNER JOIN customer_cohorts cc USING (customer_unique_id)
    GROUP BY 1, 2, 3, 4
),

final AS (
    SELECT
        -- Surrogate key
        {{ generate_int_surrogate_key(['cp.customer_unique_id', 'cp.cohort_period']) }} AS customer_retention_key,

        -- Foreign keys for dimension relationships
        {{ generate_int_surrogate_key(['cp.customer_unique_id']) }} AS customer_key,
        TO_NUMERIC(TO_CHAR(cp.cohort_month, 'YYYYMMDD')) AS cohort_date_key,
        TO_NUMERIC(TO_CHAR(cp.period_month, 'YYYYMMDD')) AS period_date_key,

        -- Cohort dimensions
        cp.cohort_month,
        cp.period_month,
        cp.cohort_period,

        -- Activity metrics
        1 AS is_active,  -- Sparse model: row exists = customer was active
        cp.period_orders,
        ROUND(cp.period_revenue, 2) AS period_revenue,

        -- Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM customer_periods cp
)

SELECT * FROM final
