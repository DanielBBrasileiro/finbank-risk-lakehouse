create schema if not exists raw;
create schema if not exists analytics;

create table if not exists raw.customers (
    customer_id text primary key,
    customer_name text,
    document_type text,
    segment text,
    state text,
    created_at date,
    internal_score int
);

create table if not exists raw.transactions (
    transaction_id text primary key,
    customer_id text,
    account_id text,
    transaction_date date,
    channel text,
    transaction_type text,
    amount numeric(18,2),
    is_suspicious boolean
);

create table if not exists raw.loans (
    loan_id text primary key,
    customer_id text,
    product_type text,
    origination_date date,
    maturity_date date,
    principal_amount numeric(18,2),
    outstanding_balance numeric(18,2),
    interest_rate numeric(10,4),
    days_past_due int,
    risk_rating text
);

create table if not exists raw.macro_indicators (
    observation_date date,
    indicator_name text,
    series_id int,
    value numeric(18,4)
);
