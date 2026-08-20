with source as (

    select * from {{ source('raw', 'orders') }}

),

renamed as (

    select
        trim(order_id) as order_id,
        trim(customer_id) as customer_id,
        trim(order_status) as order_status,
        order_purchase_timestamp::date as order_date,
        order_approved_at::timestamp as order_approved_at,
        order_delivered_carrier_date::timestamp as delivered_carrier_date,
        order_delivered_customer_date::timestamp as delivered_customer_date,
        order_estimated_delivery_date::date as estimated_delivery_date

    from source

)

select * from renamed
