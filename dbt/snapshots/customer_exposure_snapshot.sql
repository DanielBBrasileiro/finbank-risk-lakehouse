{% snapshot customer_exposure_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=[
            'portfolio_status',
            'total_outstanding_balance',
            'max_days_past_due',
            'best_risk_rating',
            'worst_risk_rating'
        ],
        invalidate_hard_deletes=True
    )
}}

select
    customer_id,
    segment,
    state,
    loan_count,
    total_outstanding_balance,
    max_days_past_due,
    best_risk_rating,
    worst_risk_rating,
    portfolio_status
from {{ ref('mart_customer_exposure') }}

{% endsnapshot %}
