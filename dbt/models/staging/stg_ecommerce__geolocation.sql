with source as (

    select * from {{ source('raw', 'geolocation') }}

),

renamed as (

    select
        lpad(geolocation_zip_code_prefix::varchar, 5, '0') as zip_code,
        avg(geolocation_lat) as latitude,
        avg(geolocation_lng) as longitude,
        max(initcap(trim(geolocation_city))) as city,
        max(upper(trim(geolocation_state))) as state

    from source
    group by geolocation_zip_code_prefix
)

select * from renamed
