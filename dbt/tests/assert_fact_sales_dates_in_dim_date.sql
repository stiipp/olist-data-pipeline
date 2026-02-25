-- Test: assert_fact_sales_dates_in_dim_date
-- Purpose: Validates referential integrity between fact_sales and dim_date
-- Expected result: 0 rows (all dates in fact_sales exist in dim_date)
-- Business rule: Every date derived from order timestamps must be present in the date dimension

select distinct purchased_date as missing_date
from {{ ref('fact_sales') }}
where purchased_date is not null
  and purchased_date not in (select date_day from {{ ref('dim_date') }})

union

select distinct delivered_date
from {{ ref('fact_sales') }}
where delivered_date is not null
  and delivered_date not in (select date_day from {{ ref('dim_date') }})

union

select distinct estimated_delivery_date
from {{ ref('fact_sales') }}
where estimated_delivery_date is not null
  and estimated_delivery_date not in (select date_day from {{ ref('dim_date') }})
