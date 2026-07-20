select *
from {{ ref('mart_customer_exposure') }}
where
    total_outstanding_balance < 0
    or total_principal_amount < 0
    or loan_count < 0
