with source as (
    select * from {{ source('olist', 'olist_order_reviews') }}
),

deduplicated as (
    select *,
        row_number() over (
            partition by review_id 
            order by review_creation_date desc
        ) as row_num
    from source
),

renamed as (
    select
        review_id,
        order_id,
        review_score,
        review_comment_title as comment_title,
        review_comment_message as comment_message,
        cast(review_creation_date as timestamp) as created_at,
        cast(review_answer_timestamp as timestamp) as answered_at
    from deduplicated
    where row_num = 1
)

select * from renamed