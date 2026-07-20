with source_totals as (
    select
        count(*) as transaction_count,
        sum(amount) as total_amount,
        sum(case when is_suspicious then 1 else 0 end) as suspicious_count
    from {{ ref('stg_transactions') }}
),

mart_totals as (
    select
        sum(transaction_count) as transaction_count,
        sum(total_amount) as total_amount,
        sum(suspicious_count) as suspicious_count
    from {{ ref('mart_daily_transactions') }}
)

select mart.*
from mart_totals mart
cross join source_totals source
where mart.transaction_count != source.transaction_count
   or abs(mart.total_amount - source.total_amount) > 0.01
   or mart.suspicious_count != source.suspicious_count
