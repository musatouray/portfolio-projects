-- Fact table for order items at line-item grain (one row per order item)
-- Use this for product/seller analytics: category performance, seller metrics, basket analysis
-- Uses role-playing dimensions for date contexts

{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        incremental_strategy='merge',
        cluster_by=['order_date_key', 'product_key', 'seller_key']
    )
}}

WITH
{{ incremental_max_date_cte('order_date') }}

order_items AS (
    SELECT *
    FROM {{ ref('int_order_items_enriched') }}
    {{ incremental_where_clause('order_date') }}
),

orders AS (
    -- Remove the incremental clause here to protect against lookups on cross-window line updates
    SELECT
        order_id,
        customer_unique_id
    FROM {{ ref('int_orders_enriched') }}
),

dim_dates AS (
    SELECT date_key, date FROM {{ ref('dim_dates') }}
),

final AS (
    SELECT
        -- Primary Key (Composite line grain mapping)
        {{ generate_int_surrogate_key(['oi.order_id', 'oi.order_item_id']) }} AS order_item_key,

        -- Natural Keys
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        oi.seller_id,

        -- Deterministic FK Generation (Eliminates 3 brittle dimension LEFT JOINs)
        {{ generate_int_surrogate_key(['o.customer_unique_id']) }} AS customer_key,
        {{ generate_int_surrogate_key(['oi.product_id']) }} AS product_key,
        {{ generate_int_surrogate_key(['oi.seller_id']) }} AS seller_key,

        -- Role-playing date dimension keys
        d_order.date_key AS order_date_key,
        d_delivery.date_key AS delivery_date_key,

        -- Date columns for direct queries
        oi.order_date,
        oi.order_status,

        -- Item financial metrics
        oi.price AS item_price,
        oi.freight_value AS item_freight,
        oi.price + oi.freight_value AS item_total,

        -- Pipeline Lineage Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM order_items oi
    INNER JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN dim_dates d_order ON oi.order_date = d_order.date
    LEFT JOIN dim_dates d_delivery ON DATE(oi.delivered_customer_date) = d_delivery.date
)

SELECT * FROM final
