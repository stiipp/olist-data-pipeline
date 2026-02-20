-- Test: assert_total_amount_equals_price_plus_freight
-- Purpose: Validates that total_amount equals price + freight_value
-- Expected result: 0 rows (no calculation errors)
-- Business rule: total_amount must always equal the sum of item price and freight cost

select
    sales_key,
    order_id,
    order_item_id,
    price,
    freight_value,
    total_amount,
    round((price + freight_value)::numeric, 2) as expected_total
from {{ ref('fact_sales') }}
where round(total_amount::numeric, 2) != round((price + freight_value)::numeric, 2)
