-- Consolidated RFM and Churn Risk fact table with monthly snapshots
-- Combines RFM scoring with churn risk metrics for unified customer health analysis
-- Self-contained model calculating all metrics from int_orders_enriched

{{ config(
    cluster_by=['snapshot_month', 'churn_risk_segment', 'rfm_segment']
) }}

WITH orders AS (
    SELECT
        customer_unique_id,
        order_date,
        total_payment_value AS revenue,
        review_count,
        total_score
    FROM {{ ref('int_orders_enriched') }}
    WHERE order_status NOT IN ('canceled', 'unavailable')
),

-- Standard Date Spine generation engine
months AS (
    SELECT DISTINCT DATE_TRUNC('MONTH', order_date) AS snapshot_month FROM orders
),

customer_snapshots AS (
    SELECT
        m.snapshot_month,
        c.customer_unique_id,
        MAX(o.order_date) AS last_purchase_date,
        COUNT(DISTINCT CASE WHEN o.order_date <= LAST_DAY(m.snapshot_month) THEN o.order_date END) AS total_orders,
        COALESCE(SUM(CASE WHEN o.order_date <= LAST_DAY(m.snapshot_month) THEN o.revenue ELSE 0 END), 0) AS total_revenue,
        COALESCE(SUM(CASE WHEN o.order_date <= LAST_DAY(m.snapshot_month) THEN o.review_count ELSE 0 END), 0) AS total_reviews,
        COALESCE(SUM(CASE WHEN o.order_date <= LAST_DAY(m.snapshot_month) THEN o.total_score ELSE 0 END), 0) AS total_scores
    FROM months m
    CROSS JOIN (SELECT DISTINCT customer_unique_id FROM orders) c
    LEFT JOIN orders o ON o.customer_unique_id = c.customer_unique_id
        AND o.order_date <= LAST_DAY(m.snapshot_month)
    GROUP BY 1, 2
    HAVING total_orders > 0
),

base_metrics AS (
    SELECT
        snapshot_month,
        customer_unique_id,
        total_orders,
        total_revenue,
        DATEDIFF('DAY', last_purchase_date, LAST_DAY(snapshot_month)) AS recency_days,
        (total_orders = 1) AS is_single_purchaser,
        total_scores / NULLIF(total_reviews, 0) AS average_rating
    FROM customer_snapshots
),

rfm_scores AS (
    SELECT
        *,
        NTILE(5) OVER (PARTITION BY snapshot_month ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (PARTITION BY snapshot_month ORDER BY total_orders ASC) AS f_score,
        NTILE(5) OVER (PARTITION BY snapshot_month ORDER BY total_revenue ASC) AS m_score
    FROM base_metrics
),

calculated_risk AS (
    SELECT
        *,
        -- 1. Churn Status Tiers
        CASE
            WHEN recency_days >= {{ var('churn_churned_days') }} THEN 'Churned'
            WHEN recency_days >= {{ var('churn_at_risk_days') }} THEN 'At Risk'
            WHEN recency_days >= {{ var('churn_cooling_days') }} THEN 'Cooling'
            ELSE 'Active'
        END AS churn_status,

        -- 2. NPS Tiers
        CASE
            WHEN average_rating IS NULL THEN 'unknown'
            WHEN average_rating >= {{ var('customer_promoter_threshold') }} THEN 'promoter'
            WHEN average_rating >= {{ var('customer_neutral_threshold') }} THEN 'neutral'
            ELSE 'detractor'
        END AS customer_nps_segment,

        -- 3. Consolidated Composite Churn Risk Score (0-100)
        (
            CASE
                WHEN recency_days >= {{ var('churn_churned_days') }} THEN 40
                WHEN recency_days >= {{ var('churn_at_risk_days') }} THEN 30
                WHEN recency_days >= {{ var('churn_cooling_days') }} THEN 15
                ELSE 0
            END +
            CASE WHEN is_single_purchaser THEN 25 ELSE 0 END +
            CASE
                WHEN average_rating IS NULL THEN 10
                WHEN average_rating < {{ var('customer_neutral_threshold') }} THEN 20
                ELSE 0
            END +
            CASE WHEN total_revenue < {{ var('churn_low_value_threshold') }} THEN 15 ELSE 0 END
        ) AS churn_risk_score

    FROM rfm_scores
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['snapshot_month', 'customer_unique_id']) }} AS rfm_snapshot_key,
    {{ dbt_utils.generate_surrogate_key(['customer_unique_id']) }} AS customer_key,

    -- Numeric date key for easier time-series analysis
    TO_NUMERIC(TO_CHAR(snapshot_month, 'YYYYMMDD')) AS snapshot_date_key,
    snapshot_month,
    customer_unique_id,
    recency_days,
    total_orders,
    total_revenue,
    average_rating,
    r_score,
    f_score,
    m_score,
    churn_status,
    customer_nps_segment,
    churn_risk_score,

    -- Risk Segments based on your business thresholds
    CASE
        WHEN churn_risk_score >= 75 THEN 'Critical'
        WHEN churn_risk_score >= 50 THEN 'High'
        WHEN churn_risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS churn_risk_segment,

    -- RFM Behavioral Segments
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyalists'
        WHEN r_score >= 4 AND f_score = 1 THEN 'New Customers'
        WHEN r_score = 1 THEN 'At Risk / Hibernating'
        ELSE 'General Pool'
    END AS rfm_segment,

    -- Metadata
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at

FROM calculated_risk
