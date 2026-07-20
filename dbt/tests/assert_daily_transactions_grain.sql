select
    transaction_date,
    channel,
    transaction_type,
    count(*) as row_count
from {{ ref('mart_daily_transactions') }}
group by transaction_date, channel, transaction_type
having count(*) > 1
