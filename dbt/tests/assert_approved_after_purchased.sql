-- Test: assert_approved_after_purchased
-- Purpose: Validates temporal order of purchase and approval timestamps
-- Expected result: 0 rows (all orders have valid timestamp sequences)
-- Business rule: An order cannot be approved before it is purchased

select
    order_id,
    purchased_at,
    approved_at
from {{ ref('stg_olist__orders') }}
where approved_at is not null
  and purchased_at is not null
  and approved_at < purchased_at
