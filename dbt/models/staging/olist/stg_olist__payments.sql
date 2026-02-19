with source as (
    select * from {{ source('olist', 'olist_order_payments') }}
),

renamed as (
    select
        -- Primary Key (composite: order_id + payment_sequential)
        order_id,
        payment_sequential,
        
        -- Payment details
        payment_type,
        payment_installments,
        payment_value

    from source
)

select * from renamed