with source_loans as (
    select
        customer_id,
        count(distinct loan_id) as loan_count,
        sum(principal_amount) as total_principal_amount,
        sum(outstanding_balance) as total_outstanding_balance
    from {{ ref('stg_loans') }}
    group by customer_id
)

select mart.customer_id
from {{ ref('mart_customer_exposure') }} as mart
left join source_loans as source
    on mart.customer_id = source.customer_id
where
    mart.loan_count != coalesce(source.loan_count, 0)
    or abs(mart.total_principal_amount - coalesce(source.total_principal_amount, 0)) > 0.01
    or abs(mart.total_outstanding_balance - coalesce(source.total_outstanding_balance, 0)) > 0.01
