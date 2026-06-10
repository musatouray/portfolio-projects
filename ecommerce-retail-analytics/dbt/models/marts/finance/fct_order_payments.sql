-- Order payments fact table at payment line item grain
-- Use this for payment analysis, installment patterns, and payment method performance
-- Self-contained model with deterministic FK generation

{{ config(
    cluster_by=['order_date_key', 'payment_type']
) }}

WITH payments AS (
    SELECT *
    FROM {{ ref('stg_ecommerce__order_payments') }}
),

orders AS (
    SELECT
        order_id,
        customer_unique_id,
        order_date
    FROM {{ ref('int_orders_enriched') }}
    WHERE order_status NOT IN ('canceled', 'unavailable')
),

dim_dates AS (
    SELECT date_key, date FROM {{ ref('dim_dates') }}
),

final AS (
    SELECT
        -- Primary Key (Grain: Individual payment line item per order)
        {{ dbt_utils.generate_surrogate_key(['p.order_id', 'p.payment_sequential', 'p.payment_type']) }} AS order_payment_key,

        -- Parent Fact Foreign Key Linkages
        {{ dbt_utils.generate_surrogate_key(['p.order_id']) }}           AS order_key,
        {{ dbt_utils.generate_surrogate_key(['o.customer_unique_id']) }} AS customer_key,

        -- Role-Playing Date Dimension Keys
        d_order.date_key AS order_date_key,

        -- Natural Business Keys & Descriptive Dimensions
        p.order_id,
        p.payment_type,
        p.payment_sequential,

        -- Atomic Fact Measures
        p.payment_installments,
        p.payment_value,

        -- Production Lineage Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM payments p
    INNER JOIN orders o ON p.order_id = o.order_id
    LEFT JOIN dim_dates d_order ON o.order_date = d_order.date
)

SELECT * FROM final
