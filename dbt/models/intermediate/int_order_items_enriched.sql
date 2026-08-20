--Join items with products, sellers, orders

with order_items as (
    select *
    from {{ ref('stg_ecommerce__order_items') }}
),

orders as (
    select *
    from {{ ref('stg_ecommerce__orders') }}
),

products as (
    select *
    from {{ ref('stg_ecommerce__products') }}
),

sellers as (
    select *
    from {{ ref('stg_ecommerce__sellers') }}
),

enriched as (

    select
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        o.order_status,
        o.order_date,
        o.order_approved_at,
        o.delivered_carrier_date,
        o.delivered_customer_date,
        o.estimated_delivery_date,
        oi.price,
        oi.freight_value,
        p.product_category,
        p.product_category_english,
        s.seller_id,
        s.zip_code,
        s.city,
        s.state

    from order_items oi
    join orders o using (order_id)
    join products p using (product_id)
    join sellers s using (seller_id)
    

)

select * from enriched
