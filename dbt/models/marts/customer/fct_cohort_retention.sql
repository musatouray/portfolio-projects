{{ config(
    cluster_by=['cohort_month', 'period']
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

customer_cohorts AS (
    SELECT
        customer_unique_id,
        MIN(order_month) AS cohort_month
    FROM orders
    GROUP BY 1
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM customer_cohorts
    GROUP BY 1
),

cohort_base_revenue AS (
    SELECT
        cc.cohort_month,
        SUM(o.revenue) AS cohort_initial_revenue
    FROM orders o
    INNER JOIN customer_cohorts cc USING (customer_unique_id)
    WHERE o.order_month = cc.cohort_month
    GROUP BY 1
),

aging_periods AS (
    SELECT
        o.customer_unique_id,
        cc.cohort_month,
        o.order_month,
        DATEDIFF('MONTH', cc.cohort_month, o.order_month) AS period,
        o.order_id,
        o.revenue
    FROM orders o
    INNER JOIN customer_cohorts cc USING (customer_unique_id)
    -- Exclude current month to avoid partial period data
    WHERE o.order_month < DATE_TRUNC('MONTH', CURRENT_DATE)
),

aggregated_periods AS (
    SELECT
        ap.cohort_month,
        ap.period,
        COUNT(DISTINCT ap.customer_unique_id) AS active_customers,
        COUNT(DISTINCT ap.order_id)           AS period_orders,
        SUM(ap.revenue)                       AS period_revenue
    FROM aging_periods ap
    GROUP BY 1, 2
),

final AS (
    SELECT
        {{ generate_int_surrogate_key(['a.cohort_month', 'a.period']) }} AS cohort_retention_key,

        -- Numeric date key for easier time-series analysis
        TO_NUMERIC(TO_CHAR(a.cohort_month, 'YYYYMMDD')) AS cohort_date_key,

        a.cohort_month,
        cs.cohort_size,
        a.period,
        a.active_customers,
        a.period_orders,
        ROUND(a.period_revenue, 2) AS period_revenue,

        -- Retention Metrics
        ROUND(LEAST(a.period_revenue, cbr.cohort_initial_revenue), 2) AS gross_retained_revenue,
        ROUND(a.period_revenue, 2) AS net_retained_revenue,
        ROUND(cbr.cohort_initial_revenue, 2) AS cohort_initial_revenue,

        -- Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM aggregated_periods a
    INNER JOIN cohort_sizes cs USING (cohort_month)
    INNER JOIN cohort_base_revenue cbr USING (cohort_month)
)

SELECT * FROM final
