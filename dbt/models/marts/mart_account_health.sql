with account_summary as (
    select
        a.customer_id,
        c.segment,
        c.state,
        count(*) as total_accounts,
        sum(case when a.status = 'ACTIVE' then 1 else 0 end) as active_accounts,
        sum(case when a.status = 'BLOCKED' then 1 else 0 end) as blocked_accounts,
        sum(case when a.status = 'CLOSED' then 1 else 0 end) as closed_accounts,
        min(a.opened_at) as earliest_account_opened,
        max(a.opened_at) as latest_account_opened
    from {{ ref('stg_accounts') }} as a
    inner join {{ ref('stg_customers') }} as c
        on a.customer_id = c.customer_id
    group by a.customer_id, c.segment, c.state
)

select
    customer_id,
    segment,
    state,
    total_accounts,
    active_accounts,
    blocked_accounts,
    closed_accounts,
    earliest_account_opened,
    latest_account_opened,
    case
        when blocked_accounts > 0 and active_accounts = 0 then 'FULLY_BLOCKED'
        when blocked_accounts > 0 then 'PARTIALLY_BLOCKED'
        when closed_accounts = total_accounts then 'ALL_CLOSED'
        else 'HEALTHY'
    end as account_health_status,
    round(
        cast(active_accounts as numeric) / nullif(total_accounts, 0) * 100, 1
    ) as active_ratio_pct
from account_summary
