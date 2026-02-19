with source as (

    select * from {{ source('olist', 'olist_sellers') }}
),
renamed as (
    select
        -- Primary Key
        seller_id,
        
        -- Categorical Info
        seller_zip_code_prefix as zip_code_prefix,
        seller_city as city,
        seller_state as state

    from source
)
select * from renamed