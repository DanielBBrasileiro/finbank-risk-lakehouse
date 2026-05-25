select
    account_id,
    customer_id,
    account_type,
    cast(opened_at as date) as opened_at,
    status
from {{ source('raw', 'accounts') }}
