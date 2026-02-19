with source as (
    select * from {{ source('olist', 'olist_order_items') }}
),
renamed as (
    select
        -- Primary Key (composite: order_id + order_item_id)
        order_id,
        order_item_id,
        
        -- Foreign Keys
        product_id,
        
        -- Numerical Info
        seller_id,
        shipping_limit_date,
        price,
        freight_value

    from source
)
select * from renamed