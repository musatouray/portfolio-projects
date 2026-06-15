-- Consolidated RFM and Churn Risk fact table with monthly snapshots
-- Combines RFM scoring with churn risk metrics for unified customer health analysis
-- Self-contained model calculating all metrics from int_orders_enriched

{{ config(
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

-- Standard Date Spine generation engine
months AS (
    SELECT DISTINCT DATE_TRUNC('MONTH', order_date) AS snapshot_month FROM orders
),

-- Pre-compute each customer's first snapshot month to eliminate anachronistic cross-join rows
-- (a full CROSS JOIN produces 2.28M rows; ~60% predate each customer's first order)
customer_first_months AS (
    SELECT
        customer_unique_id,
        DATE_TRUNC('MONTH', MIN(order_date)) AS first_snapshot_month
    FROM orders
    GROUP BY 1
),

customer_snapshots AS (
    SELECT
        m.snapshot_month,
        c.customer_unique_id,
        MAX(o.order_date) AS last_purchase_date,
        -- Fix: COUNT(DISTINCT order_id) — previously COUNT(DISTINCT order_date) undercounted
        -- customers who placed multiple orders on the same calendar date
        COUNT(DISTINCT o.order_id) AS total_orders,
        COALESCE(SUM(o.revenue), 0) AS total_revenue,
        COALESCE(SUM(o.review_count), 0) AS total_reviews,
        COALESCE(SUM(o.total_score), 0) AS total_scores
    FROM months m
    -- Fix: inner join on first_snapshot_month replaces the CROSS JOIN,
    -- only pairing each customer with months on or after their first order month
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
        -- Fix: cap reference date at CURRENT_DATE() so the final partial month
        -- measures recency to today rather than the future end-of-month
        DATEDIFF('DAY', last_purchase_date, LEAST(LAST_DAY(snapshot_month), (SELECT MAX(order_date) FROM orders))) AS recency_days,
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

    -- Risk Segments based on composite churn_risk_score thresholds
    CASE
        WHEN churn_risk_score >= 75 THEN 'Critical'
        WHEN churn_risk_score >= 50 THEN 'High'
        WHEN churn_risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS churn_risk_segment,

    -- RFM Behavioral Segments
    -- "New Customers" broadened from (r>=4 AND f_score=1) to (r>=4 AND total_orders<=2).
    -- The old f_score=1 condition was too narrow due to NTILE ties in a dataset of mostly
    -- single-purchase customers; using total_orders directly is more semantically accurate.
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyalists'
        WHEN r_score >= 4 AND total_orders <= 2 THEN 'New Customers'
        WHEN r_score = 1 THEN 'At Risk / Hibernating'
        ELSE 'General Pool'
    END AS rfm_segment,

    -- Sort index for RFM segments (Champions first, General Pool last)
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 1  -- Champions
        WHEN r_score >= 3 AND f_score >= 3 THEN 2                   -- Loyalists
        WHEN r_score >= 4 AND total_orders <= 2 THEN 3              -- New Customers
        WHEN r_score = 1 THEN 4                                     -- At Risk / Hibernating
        ELSE 5                                                      -- General Pool
    END AS segment_index,

    -- Metadata
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at

FROM calculated_risk
