with latest_macro as (
    select *
    from {{ ref('int_credit_macro_context') }}
    where observation_date = (
        select max(observation_date)
        from {{ ref('int_credit_macro_context') }}
    )
),

portfolio as (
    select
        portfolio_status,
        count(*) as customer_count,
        sum(total_outstanding_balance) as total_outstanding_balance
    from {{ ref('mart_customer_exposure') }}
    group by portfolio_status
)

select
    latest_macro.observation_date as macro_observation_date,
    latest_macro.selic_rate,
    latest_macro.credit_free_total,
    portfolio.portfolio_status,
    portfolio.customer_count,
    portfolio.total_outstanding_balance
from latest_macro
cross join portfolio
