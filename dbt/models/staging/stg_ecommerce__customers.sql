with source as (

    select * from {{ source('raw', 'customers') }}

),

renamed as (

    select
        customer_id,
        customer_unique_id,
        lpad(customer_zip_code_prefix::varchar, 5, '0') as zip_code,
        initcap(trim(customer_city)) as city,
        upper(trim(customer_state)) as state

    from source

)

select * from renamed