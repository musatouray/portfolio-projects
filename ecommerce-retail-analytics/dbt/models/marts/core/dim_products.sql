-- Product dimension table with one row per product
-- Pure dimension containing product attributes only
-- Transactional metrics (sales, reviews, etc.) belong in fact tables

WITH products AS (
    SELECT * FROM {{ ref('stg_ecommerce__products') }}
),

final AS (
    SELECT
        -- Primary Key generation for Star Schema integration
        {{ dbt_utils.generate_surrogate_key(['p.product_id']) }} AS product_key,

        -- Natural Key
        p.product_id,

        -- Clean, descriptive text descriptors
        p.product_name,
        p.product_category_english AS product_category,

        -- Immutable physical specifications
        p.name_length,
        p.description_length,
        p.photos_qty,
        p.weight_g,
        p.length_cm,
        p.height_cm,
        p.width_cm,

        -- Production Lineage Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM products p
)

SELECT * FROM final
