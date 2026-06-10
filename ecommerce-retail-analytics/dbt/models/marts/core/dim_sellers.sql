-- Seller dimension table with one row per seller
-- Pure dimension containing seller attributes only
-- Transactional metrics (orders, revenue, delivery performance) belong in fact tables

WITH sellers AS (
    SELECT * FROM {{ ref('stg_ecommerce__sellers') }}
),

-- Enforce deterministic deduplication on geo mapping
deduped_geolocation AS (
    SELECT
        zip_code,
        latitude,
        longitude
    FROM {{ ref('stg_ecommerce__geolocation') }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY zip_code ORDER BY latitude DESC, longitude DESC) = 1
),

seller_primary_category AS (
    SELECT
        seller_id,
        product_category_english,
        COUNT(*) AS items_sold
    FROM {{ ref('int_order_items_enriched') }}
    WHERE product_category_english IS NOT NULL
    GROUP BY 1, 2
    QUALIFY ROW_NUMBER() OVER (PARTITION BY seller_id ORDER BY COUNT(*) DESC, MAX(order_date) DESC, product_category_english) = 1
),

final AS (
    SELECT
        -- Primary Key generation for Star Schema mapping
        {{ dbt_utils.generate_surrogate_key(['s.seller_id']) }} AS seller_key,

        -- Natural Key
        s.seller_id,

        -- Location Attributes
        s.zip_code,
        s.city,
        s.state,
        g.latitude,
        g.longitude,

        -- Primary business classification attribute
        COALESCE(spc.product_category_english, 'Unknown') AS primary_product_category,

        -- Production Lineage Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM sellers s
    LEFT JOIN deduped_geolocation g USING (zip_code)
    LEFT JOIN seller_primary_category spc USING (seller_id)
)

SELECT * FROM final
