with customers as (
    select * from {{ ref('stg_olist__customers') }}
),

final as (
    select
        -- Primary Key
        customer_id,
        
        -- Natural Key
        customer_unique_id,
        
        -- Location Attributes
        zip_code_prefix,
        city,
        state
        
    from customers
)

select * from final