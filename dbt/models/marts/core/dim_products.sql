with products as (
    select * from {{ ref('stg_olist__products') }}
),

categories as (
    select * from {{ ref('stg_olist__category_translation') }}
),

final as (
    select
        -- Primary Key
        p.product_id,
        
        -- Product Category
        p.category_name,
        c.category_name_english,
        
        -- Product Attributes
        p.name_length,
        p.description_length,
        p.photos_quantity,
        
        -- Dimensions
        p.weight_g,
        p.length_cm,
        p.height_cm,
        p.width_cm
        
    from products p
    left join categories c on p.category_name = c.category_name
)

select * from final
