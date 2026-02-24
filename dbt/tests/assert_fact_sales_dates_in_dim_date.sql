-- Test: assert_fact_sales_dates_in_dim_date
-- Purpose: Validates referential integrity between fact_sales and dim_date
-- Expected result: 0 rows (all dates in fact_sales exist in dim_date)
-- Business rule: Every date derived from order timestamps must be present in the date dimension

select distinct purchased_at::date as missing_date
from {{ ref('fact_sales') }}
where purchased_at is not null
  and purchased_at::date not in (select date_day from {{ ref('dim_date') }})

union

select distinct delivered_to_customer_at::date
from {{ ref('fact_sales') }}
where delivered_to_customer_at is not null
  and delivered_to_customer_at::date not in (select date_day from {{ ref('dim_date') }})

union

select distinct estimated_delivery_at::date
from {{ ref('fact_sales') }}
where estimated_delivery_at is not null
  and estimated_delivery_at::date not in (select date_day from {{ ref('dim_date') }})
