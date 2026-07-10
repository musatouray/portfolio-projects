-- Fact table for orders at order grain (one row per order)
-- Use this for order-level analytics: revenue trends, AOV, customer behavior
-- Uses role-playing dimensions for multiple date contexts

{{
    config(
        materialized='incremental',
        unique_key='order_key',
        incremental_strategy='merge',
        cluster_by=['order_date_key', 'order_status']
    )
}}

WITH
{{ incremental_max_date_cte('order_date') }}

orders AS (
    SELECT *
    FROM {{ ref('int_orders_enriched') }}
    {{ incremental_where_clause('order_date') }}
),

dim_dates AS (
    SELECT date_key, date FROM {{ ref('dim_dates') }}
),

final AS (
    SELECT
        -- Primary Key
        {{ generate_int_surrogate_key(['o.order_id']) }} AS order_key,
        o.order_id,

        -- Deterministic FK Generation (Eliminates the LEFT JOIN to dim_customers)
        {{ generate_int_surrogate_key(['o.customer_unique_id']) }} AS customer_key,
        o.customer_unique_id,

        -- Role-playing date dimension keys
        d_order.date_key AS order_date_key,
        d_approval.date_key AS approval_date_key,
        d_delivery.date_key AS delivery_date_key,
        d_estimated.date_key AS estimated_delivery_date_key,

        -- Native Timestamps
        o.order_date,
        o.order_status,

        -- Delivery metrics
        DATEDIFF('DAY', o.order_date, o.delivered_customer_date) AS delivery_days,
        DATEDIFF('DAY', o.order_approved_at, o.delivered_customer_date) AS fulfillment_days,
        DATEDIFF('DAY', o.delivered_carrier_date, o.delivered_customer_date) AS shipping_transit_days,

        CASE
            WHEN o.delivered_customer_date <= o.estimated_delivery_date THEN TRUE
            ELSE FALSE
        END AS is_on_time_delivery,

        -- Core Financial Metrics
        o.total_price,
        o.total_freight_value,
        o.total_price + o.total_freight_value AS gross_order_value,
        o.payment_count,
        o.total_payment_value,

        -- Satisfaction Metrics
        o.review_count,
        o.avg_score AS review_score,

        -- Pipeline Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at

    FROM orders o
    -- Role-playing calendar dimension joins
    LEFT JOIN dim_dates d_order ON o.order_date = d_order.date
    LEFT JOIN dim_dates d_approval ON DATE(o.order_approved_at) = d_approval.date
    LEFT JOIN dim_dates d_delivery ON DATE(o.delivered_customer_date) = d_delivery.date
    LEFT JOIN dim_dates d_estimated ON DATE(o.estimated_delivery_date) = d_estimated.date
)

SELECT * FROM final
