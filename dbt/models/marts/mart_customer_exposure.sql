select
    customer_id,
    segment,
    state,
    internal_score,
    loan_count,
    total_principal_amount,
    total_outstanding_balance,
    max_days_past_due,
    avg_days_past_due,
    best_risk_rating,
    worst_risk_rating,
    {{ portfolio_status('loan_count', 'max_days_past_due') }} as portfolio_status
from {{ ref('int_customer_credit_profile') }}
