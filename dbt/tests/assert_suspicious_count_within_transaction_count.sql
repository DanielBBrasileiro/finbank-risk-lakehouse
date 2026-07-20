select *
from {{ ref('mart_daily_transactions') }}
where
    suspicious_count > transaction_count
    or suspicious_count < 0
    or transaction_count < 0
