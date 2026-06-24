with source as (

    select * from {{ source('raw', 'products') }}

),

translation as (

    select * from {{ ref('stg_ecommerce__product_category_translation') }}

),

renamed as (

    select
        trim(product_id) as product_id,
        trim(s.product_name) as product_name,
        trim(product_category_name) as product_category,
        COALESCE(t.product_category_english, 'Uncategorized') as product_category_english,
        product_name_lenght::int as name_length,
        product_description_lenght::int as description_length,
        product_photos_qty::int as photos_qty,
        product_weight_g::numeric(10,2) as weight_g,
        product_length_cm::numeric(10,2) as length_cm,
        product_height_cm::numeric(10,2) as height_cm,
        product_width_cm::numeric(10,2) as width_cm

    from source s
    left join translation t on trim(s.product_category_name) = t.product_category

)

select * from renamed