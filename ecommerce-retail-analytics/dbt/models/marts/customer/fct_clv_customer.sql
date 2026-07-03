-- Customer Lifetime Value fact table with historical metrics and 12-month projection
-- Self-contained model calculating all metrics from int_orders_enriched
-- Includes absorbed behavioral segments from dim_customers

WITH orders AS (
    SELECT
        customer_unique_id,
        order_id,
        order_date,
        total_payment_value AS revenue,
        review_count,
        total_score
    FROM {{ ref('int_orders_enriched') }}
    WHERE order_status NOT IN ('canceled', 'unavailable')
),

customer_cohorts AS (
    SELECT
        customer_unique_id,
        DATE_TRUNC('MONTH', MIN(order_date)) AS cohort_month,
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date
    FROM orders
    GROUP BY 1
),

customer_aggregations AS (
    SELECT
        o.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS total_lifetime_orders,
        SUM(o.revenue) AS total_lifetime_revenue,

        -- Absorbed Review & Satisfaction Metrics
        SUM(o.review_count) AS total_reviews,
        SUM(o.total_score) / NULLIF(SUM(o.review_count), 0) AS average_rating
    FROM orders o
    GROUP BY 1
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['ca.customer_unique_id']) }} AS customer_key,
        ca.customer_unique_id,
        cc.cohort_month,
        cc.first_order_date,
        cc.last_order_date,

        -- Core Historical Value Facts
        COALESCE(ca.total_lifetime_orders, 0) AS total_lifetime_orders,
        COALESCE(ca.total_lifetime_revenue, 0) AS total_lifetime_revenue,
        ca.total_lifetime_revenue / NULLIF(ca.total_lifetime_orders, 0) AS historical_aov,
        DATEDIFF('DAY', cc.first_order_date, cc.last_order_date) AS customer_lifespan_days,

        -- Review and Satisfaction Metrics
        COALESCE(ca.total_reviews, 0) AS total_reviews,
        ca.average_rating,

        -- Absorbed Behavioral Classifications (Moved out of dim_customers)
        CASE
            WHEN ca.total_lifetime_orders = 1 THEN 'new'
            ELSE 'returning'
        END AS customer_lifecycle_segment,

        CASE
            WHEN ca.total_lifetime_revenue >= {{ var('customer_high_value_threshold') }} THEN 'high_value'
            WHEN ca.total_lifetime_revenue >= {{ var('customer_medium_value_threshold') }} THEN 'medium_value'
            ELSE 'low_value'
        END AS customer_value_segment,

        CASE
            WHEN ca.average_rating IS NULL THEN 'unknown'
            WHEN ca.average_rating >= {{ var('customer_promoter_threshold') }} THEN 'promoter'
            WHEN ca.average_rating >= {{ var('customer_neutral_threshold') }} THEN 'neutral'
            ELSE 'detractor'
        END AS customer_satisfaction_segment,

        -- Linear CLV projection over the configured horizon (clv_prediction_horizon_days var).
        -- GREATEST(1, ...) clamps customer lifespan to avoid division-by-zero and
        -- unrealistic same-day projections (brand-new customers default to one day of revenue).
        COALESCE(
            (ca.total_lifetime_revenue
                / NULLIF(GREATEST(1, DATEDIFF('DAY', cc.first_order_date, CURRENT_DATE())), 0))
            * {{ var('clv_prediction_horizon_days') }},
            0
        ) AS predicted_clv_12m,

        -- Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM customer_aggregations ca
    INNER JOIN customer_cohorts cc USING (customer_unique_id)
)

SELECT * FROM final
