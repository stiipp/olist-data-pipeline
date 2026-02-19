source as (
    select * from {{ source('olist', 'olist_order_payments') }}
),

renamed as (
    select
        -- Primary Key
        payment_id,
        
        -- Foreign Keys
        order_id,
        
        -- Numerical Info
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value

    from source
)