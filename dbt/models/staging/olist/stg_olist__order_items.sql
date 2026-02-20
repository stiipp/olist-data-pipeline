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
        seller_id,
        
        -- Timestamps
        cast(shipping_limit_date as timestamp) as shipping_limit_date,
        
        -- Measures (cast to numeric for precision)
        round(price::numeric, 2) as price,
        round(freight_value::numeric, 2) as freight_value

    from source
)

select * from renamed