--Join orders with customers, aggregate items, payments, reviews

with orders as (
    select *
    from {{ ref('stg_ecommerce__orders') }}
),

order_items as (
    select *
    from {{ ref('stg_ecommerce__order_items') }}
),

-- Aggregate order items to get total price and freight value per order
aggregated_order_items as (

    select
        order_id,
        sum(price) as total_price,
        sum(freight_value) as total_freight_value
    from order_items
    group by order_id

),

payments as (
    select *
    from {{ ref('stg_ecommerce__order_payments') }}
),

-- Aggregate payments to get total payment value per order
aggregated_payments as (

    select
        order_id,
        count(*) as payment_count,
        sum(payment_value) as total_payment_value
    from payments
    group by order_id

),
reviews as (
    select *
    from {{ ref('stg_ecommerce__order_reviews') }}
),

-- Aggregate reviews to get average score and count per order
aggregated_reviews as (

    select
        order_id,
        count(*) as review_count,
        sum(score) as total_score,
        avg(score) as avg_score
    from reviews
    group by order_id

),

customers as (
    select *
    from {{ ref('stg_ecommerce__customers') }}
),

enriched as (

    select
        oi.order_id,
        o.order_status,
        o.order_date,
        o.order_approved_at,
        o.delivered_carrier_date,
        o.delivered_customer_date,
        o.estimated_delivery_date,
        c.customer_id,
        c.customer_unique_id,
        c.zip_code,
        c.city,
        c.state,
        oi.total_price,
        oi.total_freight_value,
        p.payment_count,
        p.total_payment_value,
        r.review_count,
        r.total_score,
        r.avg_score

    from orders o
    join customers c using (customer_id)
    join aggregated_order_items oi using (order_id)
    left join aggregated_payments p using (order_id)
    left join aggregated_reviews r using (order_id)
    

)
select * from enriched