with source as (

    select * from {{ source('raw', 'order_reviews') }}

),

renamed as (

    select
        trim(review_id) as review_id,
        trim(order_id) as order_id,
        review_score::int as score,
        trim(review_comment_title) as comment_title,
        trim(review_comment_message) as comment_message,
        review_creation_date::date as creation_date,
        review_answer_timestamp::timestamp as answer_date,
        row_number() over (partition by review_id order by review_answer_timestamp desc) as row_num

    from source

),

deduplicated as (

    select
        review_id,
        order_id,
        score,
        comment_title,
        comment_message,
        creation_date,
        answer_date

    from renamed
    where row_num = 1

)

select * from deduplicated
