with source as (

    select * from {{ source('raw', 'sellers') }}

),

renamed as (

    select
        trim(seller_id) as seller_id,
        lpad(trim(seller_zip_code_prefix)::varchar, 5, '0') as zip_code,
        initcap(trim(seller_city)) as city,
        upper(trim(seller_state)) as state
    from source

)

select * from renamed
