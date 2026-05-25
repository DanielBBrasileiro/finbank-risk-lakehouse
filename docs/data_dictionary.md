# Data dictionary

## customers

| Column | Description |
|---|---|
| customer_id | Synthetic customer unique identifier |
| customer_name | Synthetic name or company name |
| document_type | CPF or CNPJ synthetic flag |
| segment | Customer segment |
| state | Brazilian state |
| created_at | Synthetic customer onboarding date |
| internal_score | Synthetic internal risk score |

## accounts

| Column | Description |
|---|---|
| account_id | Synthetic account unique identifier |
| customer_id | Related customer |
| account_type | Checking, savings or investment account |
| opened_at | Synthetic account opening date |
| status | Active, blocked or closed account status |

## transactions

| Column | Description |
|---|---|
| transaction_id | Unique transaction identifier |
| customer_id | Related customer |
| account_id | Related account |
| transaction_date | Transaction date |
| channel | PIX, CARD, ATM, BRANCH, TED or APP |
| transaction_type | Debit, credit, transfer, payment or withdrawal |
| amount | Transaction amount |
| is_suspicious | Synthetic suspicious transaction flag |

## loans

| Column | Description |
|---|---|
| loan_id | Unique loan identifier |
| customer_id | Related customer |
| product_type | Loan product |
| origination_date | Loan origination date |
| maturity_date | Loan contractual maturity date |
| principal_amount | Original loan principal |
| outstanding_balance | Current exposure |
| interest_rate | Synthetic monthly interest rate |
| days_past_due | Days past due |
| risk_rating | Synthetic risk rating |

## mart_customer_exposure

| Column | Description |
|---|---|
| customer_id | Customer identifier |
| segment | Customer segment |
| state | Customer state |
| internal_score | Internal credit score |
| loan_count | Number of loans linked to the customer |
| total_principal_amount | Total original principal amount |
| total_outstanding_balance | Total current credit exposure |
| max_days_past_due | Maximum delinquency observed for the customer |
| avg_days_past_due | Average delinquency across the customer portfolio |
| portfolio_status | Derived status: PERFORMING, WATCHLIST, HIGH_RISK or DEFAULT_RISK |

## mart_daily_transactions

| Column | Description |
|---|---|
| transaction_date | Daily transaction date |
| channel | Transaction channel |
| transaction_type | Transaction type |
| transaction_count | Number of transactions in the slice |
| total_amount | Total transaction amount |
| avg_amount | Average transaction amount |
| suspicious_count | Count of transactions flagged as suspicious |

## macro_indicators

| Column | Description |
|---|---|
| observation_date | BCB observation date normalized to ISO format |
| indicator_name | Macro indicator name, such as selic or credit_free_total |
| series_id | BCB SGS series identifier |
| value | Numeric indicator value |

## mart_credit_macro_context

| Column | Description |
|---|---|
| macro_observation_date | Latest macro observation date available locally |
| selic_rate | Latest SELIC value in the macro source |
| credit_free_total | Latest free-credit total value in the macro source |
| portfolio_status | Derived credit portfolio status |
| customer_count | Number of customers by portfolio status |
| total_outstanding_balance | Outstanding credit exposure by portfolio status |

## accounts

| Column | Description |
|---|---|
| account_id | Synthetic account unique identifier |
| customer_id | Related customer |
| account_type | Checking, savings or investment account |
| opened_at | Synthetic account opening date |
| status | Active, blocked or closed account status |

## mart_account_health

| Column | Description |
|---|---|
| customer_id | Customer identifier |
| segment | Customer segment |
| state | Customer state |
| total_accounts | Total number of accounts for the customer |
| active_accounts | Number of active accounts |
| blocked_accounts | Number of blocked accounts |
| closed_accounts | Number of closed accounts |
| earliest_account_opened | Date of the customer's first account |
| latest_account_opened | Date of the customer's most recent account |
| account_health_status | Derived status: HEALTHY, PARTIALLY_BLOCKED, FULLY_BLOCKED or ALL_CLOSED |
| active_ratio_pct | Percentage of active accounts relative to total |
