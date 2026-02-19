with sellers as (
    select * from {{ ref('stg_olist__sellers') }}
),

final as (
    select
        -- Primary Key
        seller_id,
        
        -- Location Attributes
        seller_zip_code_prefix,
        seller_city,
        seller_state
        
    from sellers
)

select * from final
