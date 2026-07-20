select *
from {{ ref('mart_customer_exposure') }}
where (loan_count = 0 and portfolio_status != 'NO_CREDIT_EXPOSURE')
   or (loan_count > 0 and max_days_past_due >= 90 and portfolio_status != 'DEFAULT_RISK')
   or (loan_count > 0 and max_days_past_due >= 30 and max_days_past_due < 90 and portfolio_status != 'HIGH_RISK')
   or (loan_count > 0 and max_days_past_due > 0 and max_days_past_due < 30 and portfolio_status != 'WATCHLIST')
   or (loan_count > 0 and max_days_past_due = 0 and portfolio_status != 'PERFORMING')
