-- Consolidated RFM and Churn Risk fact table with monthly snapshots
-- Combines RFM scoring with churn risk metrics for unified customer health analysis
-- Uses ABSOLUTE thresholds (not NTILE percentiles) for business-meaningful segments
--
-- Key design decisions:
-- 1. Absolute thresholds prevent skewed data from producing meaningless quintiles
-- 2. Segment priority: New Customers checked before Champions to prevent overlap
-- 3. Incremental processing for scalability (only recent months on incremental runs)

{{ config(
    materialized='incremental',
    unique_key='rfm_snapshot_key',
    incremental_strategy='merge',
    cluster_by=['snapshot_month', 'churn_risk_segment', 'rfm_segment']
) }}

WITH orders AS (
    SELECT
        order_id,
        customer_unique_id,
        order_date,
        total_payment_value AS revenue,
        review_count,
        total_score
    FROM {{ ref('int_orders_enriched') }}
    WHERE order_status NOT IN ('canceled', 'unavailable')
),

-- Date Spine: Generate all months with order activity
months AS (
    SELECT DISTINCT DATE_TRUNC('MONTH', order_date) AS snapshot_month
    FROM orders
    {% if is_incremental() %}
    -- On incremental runs, only process recent months (current + 2 prior for late arrivals)
    WHERE DATE_TRUNC('MONTH', order_date) >= DATE_TRUNC('MONTH', CURRENT_DATE()) - INTERVAL '2 MONTHS'
    {% endif %}
),

-- Pre-compute each customer's first snapshot month to eliminate anachronistic rows
customer_first_months AS (
    SELECT
        customer_unique_id,
        DATE_TRUNC('MONTH', MIN(order_date)) AS first_snapshot_month
    FROM orders
    GROUP BY 1
),

-- Aggregate customer metrics up to each snapshot month
customer_snapshots AS (
    SELECT
        m.snapshot_month,
        c.customer_unique_id,
        MAX(o.order_date) AS last_purchase_date,
        COUNT(DISTINCT o.order_id) AS total_orders,
        COALESCE(SUM(o.revenue), 0) AS total_revenue,
        COALESCE(SUM(o.review_count), 0) AS total_reviews,
        COALESCE(SUM(o.total_score), 0) AS total_scores
    FROM months m
    JOIN customer_first_months c ON m.snapshot_month >= c.first_snapshot_month
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
        -- Cap reference date at max order date to avoid measuring recency to future
        DATEDIFF('DAY', last_purchase_date,
            LEAST(LAST_DAY(snapshot_month), (SELECT MAX(order_date) FROM orders))
        ) AS recency_days,
        (total_orders = 1) AS is_single_purchaser,
        total_scores / NULLIF(total_reviews, 0) AS average_rating
    FROM customer_snapshots
),

-- RFM Scoring using ABSOLUTE thresholds (not percentile-based NTILE)
-- This ensures scores reflect actual business value, not relative ranking
rfm_scores AS (
    SELECT
        *,
        -- Recency Score: Lower recency_days = higher score (more recent = better)
        CASE
            WHEN recency_days <= {{ var('rfm_recency_score_5') }} THEN 5
            WHEN recency_days <= {{ var('rfm_recency_score_4') }} THEN 4
            WHEN recency_days <= {{ var('rfm_recency_score_3') }} THEN 3
            WHEN recency_days <= {{ var('rfm_recency_score_2') }} THEN 2
            ELSE 1
        END AS r_score,

        -- Frequency Score: Higher order count = higher score
        CASE
            WHEN total_orders >= {{ var('rfm_frequency_score_5') }} THEN 5
            WHEN total_orders >= {{ var('rfm_frequency_score_4') }} THEN 4
            WHEN total_orders >= {{ var('rfm_frequency_score_3') }} THEN 3
            WHEN total_orders >= {{ var('rfm_frequency_score_2') }} THEN 2
            ELSE 1
        END AS f_score,

        -- Monetary Score: Higher revenue = higher score
        CASE
            WHEN total_revenue >= {{ var('rfm_monetary_score_5') }} THEN 5
            WHEN total_revenue >= {{ var('rfm_monetary_score_4') }} THEN 4
            WHEN total_revenue >= {{ var('rfm_monetary_score_3') }} THEN 3
            WHEN total_revenue >= {{ var('rfm_monetary_score_2') }} THEN 2
            ELSE 1
        END AS m_score
    FROM base_metrics
),

calculated_risk AS (
    SELECT
        *,
        -- Churn Status Tiers
        CASE
            WHEN recency_days >= {{ var('churn_churned_days') }} THEN 'Churned'
            WHEN recency_days >= {{ var('churn_at_risk_days') }} THEN 'At Risk'
            WHEN recency_days >= {{ var('churn_cooling_days') }} THEN 'Cooling'
            ELSE 'Active'
        END AS churn_status,

        -- NPS Tiers based on average review rating
        CASE
            WHEN average_rating IS NULL THEN 'unknown'
            WHEN average_rating >= {{ var('customer_promoter_threshold') }} THEN 'promoter'
            WHEN average_rating >= {{ var('customer_neutral_threshold') }} THEN 'neutral'
            ELSE 'detractor'
        END AS customer_nps_segment,

        -- Composite Churn Risk Score (0-100)
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
        ) AS churn_risk_score,

        -- Combined RFM score for segment qualification
        (r_score + f_score + m_score) AS rfm_combined_score
    FROM rfm_scores
)

SELECT
    {{ generate_int_surrogate_key(['snapshot_month', 'customer_unique_id']) }} AS rfm_snapshot_key,
    {{ generate_int_surrogate_key(['customer_unique_id']) }} AS customer_key,

    -- Date keys for joining
    TO_NUMERIC(TO_CHAR(snapshot_month, 'YYYYMMDD')) AS snapshot_date_key,
    snapshot_month,
    customer_unique_id,

    -- Core metrics
    recency_days,
    total_orders,
    total_revenue,
    average_rating,

    -- RFM Scores (1-5 scale, absolute thresholds)
    r_score,
    f_score,
    m_score,
    rfm_combined_score,

    -- Churn metrics
    churn_status,
    customer_nps_segment,
    churn_risk_score,

    -- Churn Risk Segment based on composite score
    CASE
        WHEN churn_risk_score >= 75 THEN 'Critical'
        WHEN churn_risk_score >= 50 THEN 'High'
        WHEN churn_risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS churn_risk_segment,

    -- RFM Behavioral Segments 
    CASE
        -- New Customers: Recent but few orders 
        WHEN r_score >= 4 AND total_orders <= 2 THEN 'New Customers'

        -- Champions: Elite customers - high on ALL three dimensions
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'

        -- Loyal Customers: Strong on recency and frequency, decent monetary
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'

        -- Potential Loyalists: Recent with moderate engagement
        WHEN r_score >= 4 AND f_score >= 2 THEN 'Potential Loyalists'

        -- At Risk: Were good customers but haven't purchased recently
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk'

        -- Hibernating: Low recency, were somewhat engaged
        WHEN r_score <= 2 AND f_score >= 2 THEN 'Hibernating'

        -- Lost: Very low engagement across the board
        WHEN r_score = 1 AND f_score = 1 THEN 'Lost'

        -- Need Attention: Everyone else - moderate engagement
        ELSE 'Need Attention'
    END AS rfm_segment,

    -- Segment sort index for consistent ordering in reports
    CASE
        WHEN r_score >= 4 AND total_orders <= 2 THEN 2                            -- New Customers
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 1                -- Champions
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 3                -- Loyal Customers
        WHEN r_score >= 4 AND f_score >= 2 THEN 4                                 -- Potential Loyalists
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 5                -- At Risk
        WHEN r_score <= 2 AND f_score >= 2 THEN 6                                 -- Hibernating
        WHEN r_score = 1 AND f_score = 1 THEN 8                                   -- Lost
        ELSE 7                                                                     -- Need Attention
    END AS segment_index,

    -- Metadata
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at

FROM calculated_risk
