-- Market basket analysis fact table for product pair co-occurrence
-- Provides atomic counts for semantic layer calculations (support, confidence, lift)
-- Self-contained model with deterministic FK generation

WITH order_items AS (
    SELECT
        order_id,
        product_id
    FROM {{ ref('int_order_items_enriched') }}
    WHERE order_status NOT IN ('canceled', 'unavailable')
),

-- Isolate raw atomic popularity per product without mixing global totals
item_popularity AS (
    SELECT
        product_id,
        COUNT(DISTINCT order_id) AS total_orders_per_product
    FROM order_items
    GROUP BY 1
),

-- Perform clean self-join to extract raw intersection pairs
product_pairs AS (
    SELECT
        a.product_id AS product_id_a,
        b.product_id AS product_id_b,
        COUNT(DISTINCT a.order_id) AS pair_count
    FROM order_items a
    INNER JOIN order_items b ON a.order_id = b.order_id
        AND a.product_id < b.product_id  -- Prevents reciprocal duplication (A-B vs B-A)
    GROUP BY 1, 2
    HAVING COUNT(DISTINCT a.order_id) >= {{ var('market_basket_min_pair_count', 5) }}
),

final AS (
    SELECT
        -- Primary Key generation for the unique combination pair
        {{ dbt_utils.generate_surrogate_key(['pp.product_id_a', 'pp.product_id_b']) }} AS basket_pair_key,

        -- Deterministic Star Schema Foreign Keys
        {{ dbt_utils.generate_surrogate_key(['pp.product_id_a']) }} AS product_key_a,
        {{ dbt_utils.generate_surrogate_key(['pp.product_id_b']) }} AS product_key_b,

        -- Atomic counts required for dynamic semantic computations
        pp.pair_count,
        ia.total_orders_per_product AS product_a_order_count,
        ib.total_orders_per_product AS product_b_order_count,

        -- Production Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM product_pairs pp
    INNER JOIN item_popularity ia ON pp.product_id_a = ia.product_id
    INNER JOIN item_popularity ib ON pp.product_id_b = ib.product_id
)

SELECT * FROM final
