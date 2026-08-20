with source as (

    select * from {{ source('raw', 'order_items') }}

),

renamed as (

    select
        trim(order_id) as order_id,
        order_item_id::int as order_item_id,
        trim(product_id) as product_id,
        trim(seller_id) as seller_id,
        shipping_limit_date::date as shipping_deadline,
        price::numeric(10,2) as price,
        freight_value::numeric(10,2) as freight_value

    from source
    
)

select * from renamed