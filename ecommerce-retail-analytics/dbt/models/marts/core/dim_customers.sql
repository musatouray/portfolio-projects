-- Customer dimension table with one row per unique customer
-- Pure dimension containing customer attributes and cohort assignment
-- Transactional metrics (orders, revenue, etc.) belong in fact tables

WITH customers AS (
    SELECT * FROM {{ ref('stg_ecommerce__customers') }}
),

orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
    WHERE order_status NOT IN ('canceled', 'unavailable')
),

-- Isolate acquisition milestones cleanly without mixing transactional metrics
customer_first_orders AS (
    SELECT
        customer_unique_id,
        MIN(order_date) AS first_order_date
    FROM orders
    GROUP BY 1
),

-- Dedupe customers safely to unique customer level (take most recent address)
deduped_customers AS (
    SELECT
        customer_unique_id,
        FIRST_VALUE(zip_code) OVER (PARTITION BY customer_unique_id ORDER BY customer_id DESC) AS zip_code,
        FIRST_VALUE(city) OVER (PARTITION BY customer_unique_id ORDER BY customer_id DESC) AS city,
        FIRST_VALUE(state) OVER (PARTITION BY customer_unique_id ORDER BY customer_id DESC) AS state
    FROM customers
    -- Enforce deterministic deduplication via qualify window step
    QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY customer_id DESC) = 1
),

final AS (
    SELECT
        -- Primary Key generation for downstream Star Schema mapping
        {{ dbt_utils.generate_surrogate_key(['dc.customer_unique_id']) }} AS customer_key,
        dc.customer_unique_id,
        dc.zip_code,
        dc.city,
        dc.state,

        -- Flat, immutable temporal descriptors instead of surrogate bridge keys
        cfo.first_order_date,
        DATE_TRUNC('MONTH', cfo.first_order_date) AS cohort_month,

        -- Metadata logging for pipeline lineage tracking
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM deduped_customers dc
    -- LEFT JOIN guarantees prospects remain in system if your pipeline loads them
    LEFT JOIN customer_first_orders cfo USING (customer_unique_id)
)

SELECT * FROM final
