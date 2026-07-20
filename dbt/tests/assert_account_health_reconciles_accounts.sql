with source_accounts as (
    select
        customer_id,
        count(*) as total_accounts,
        sum(case when status = 'ACTIVE' then 1 else 0 end) as active_accounts,
        sum(case when status = 'BLOCKED' then 1 else 0 end) as blocked_accounts,
        sum(case when status = 'CLOSED' then 1 else 0 end) as closed_accounts
    from {{ ref('stg_accounts') }}
    group by customer_id
)

select mart.customer_id
from {{ ref('mart_account_health') }} mart
inner join source_accounts source
    on mart.customer_id = source.customer_id
where mart.total_accounts != source.total_accounts
   or mart.active_accounts != source.active_accounts
   or mart.blocked_accounts != source.blocked_accounts
   or mart.closed_accounts != source.closed_accounts
