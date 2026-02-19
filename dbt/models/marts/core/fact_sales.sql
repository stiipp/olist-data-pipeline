with order_items as (
    select * from {{ ref('stg_olist__order_items') }}
),

orders as (
    select * from {{ ref('stg_olist__orders') }}
),

final as (
    select
        -- Surrogate Key
        oi.order_id || '-' || oi.order_item_id as sales_key,
        
        -- Foreign Keys
        oi.order_id,
        o.customer_id,
        oi.product_id,
        oi.seller_id,
        
        -- Order Context
        oi.order_item_id,
        o.order_status,
        o.purchased_at,
        o.approved_at,
        o.delivered_to_carrier_at,
        o.delivered_to_customer_at,
        o.estimated_delivery_at,
        
        -- Measures
        oi.price,
        oi.freight_value,
        oi.price + oi.freight_value as total_amount
        
    from order_items oi
    inner join orders o on oi.order_id = o.order_id
)

select * from final
