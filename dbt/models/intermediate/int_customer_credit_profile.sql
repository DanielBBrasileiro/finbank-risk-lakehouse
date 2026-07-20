with loan_details as (
    select
        loan_id,
        customer_id,
        principal_amount,
        outstanding_balance,
        days_past_due,
        {{ risk_rating_score('risk_rating') }} as risk_rating_score
    from {{ ref('stg_loans') }}
),

loan_summary as (
    select
        customer_id,
        count(distinct loan_id) as loan_count,
        sum(principal_amount) as total_principal_amount,
        sum(outstanding_balance) as total_outstanding_balance,
        max(days_past_due) as max_days_past_due,
        avg(days_past_due) as avg_days_past_due,
        min(risk_rating_score) as best_risk_rating_score,
        max(risk_rating_score) as worst_risk_rating_score
    from loan_details
    group by customer_id
)

select
    c.customer_id,
    c.segment,
    c.state,
    c.internal_score,
    l.best_risk_rating_score,
    l.worst_risk_rating_score,
    coalesce(l.loan_count, 0) as loan_count,
    coalesce(l.total_principal_amount, 0) as total_principal_amount,
    coalesce(l.total_outstanding_balance, 0) as total_outstanding_balance,
    coalesce(l.max_days_past_due, 0) as max_days_past_due,
    coalesce(l.avg_days_past_due, 0) as avg_days_past_due,
    {{ risk_rating_from_score('l.best_risk_rating_score') }} as best_risk_rating,
    {{ risk_rating_from_score('l.worst_risk_rating_score') }} as worst_risk_rating
from {{ ref('stg_customers') }} as c
left join loan_summary as l
    on c.customer_id = l.customer_id
