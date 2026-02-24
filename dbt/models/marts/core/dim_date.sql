with date_spine as (
    select distinct
        purchased_at::date as date_day
    from {{ ref('stg_olist__orders') }}

    union

    select distinct
        delivered_to_customer_at::date as date_day
    from {{ ref('stg_olist__orders') }}
    where delivered_to_customer_at is not null

    union

    select distinct
        estimated_delivery_at::date as date_day
    from {{ ref('stg_olist__orders') }}
    where estimated_delivery_at is not null
),

final as (
    select
        date_day,
        extract(year from date_day)::int as year,
        extract(month from date_day)::int as month,
        extract(day from date_day)::int as day_of_month,
        extract(dow from date_day)::int as day_of_week,
        extract(quarter from date_day)::int as quarter,
        to_char(date_day, 'Day') as day_name,
        to_char(date_day, 'Month') as month_name,
        case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
    from date_spine
    where date_day is not null
)

select * from final