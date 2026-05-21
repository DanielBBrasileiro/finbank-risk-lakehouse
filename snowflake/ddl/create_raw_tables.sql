create database if not exists FINBANK;
create schema if not exists FINBANK.RAW;
create schema if not exists FINBANK.STAGING;
create schema if not exists FINBANK.MARTS;

create or replace table FINBANK.RAW.CUSTOMERS (
    customer_id string,
    customer_name string,
    document_type string,
    segment string,
    state string,
    created_at date,
    internal_score number
);

create or replace table FINBANK.RAW.TRANSACTIONS (
    transaction_id string,
    customer_id string,
    account_id string,
    transaction_date date,
    channel string,
    transaction_type string,
    amount number(18,2),
    is_suspicious boolean
);

create or replace table FINBANK.RAW.LOANS (
    loan_id string,
    customer_id string,
    product_type string,
    origination_date date,
    maturity_date date,
    principal_amount number(18,2),
    outstanding_balance number(18,2),
    interest_rate number(10,4),
    days_past_due number,
    risk_rating string
);

create or replace table FINBANK.RAW.MACRO_INDICATORS (
    observation_date date,
    indicator_name string,
    series_id number,
    value number(18,4)
);

create or replace table FINBANK.MARTS.MART_CUSTOMER_EXPOSURE (
    customer_id string,
    segment string,
    state string,
    internal_score number,
    loan_count number,
    total_principal_amount number(18,2),
    total_outstanding_balance number(18,2),
    max_days_past_due number,
    avg_days_past_due number(18,2),
    portfolio_status string
);

create or replace table FINBANK.MARTS.MART_CREDIT_MACRO_CONTEXT (
    macro_observation_date date,
    selic_rate number(18,4),
    credit_free_total number(18,4),
    portfolio_status string,
    customer_count number,
    total_outstanding_balance number(18,2)
);

comment on schema FINBANK.RAW is 'Raw landing schema for source-aligned banking and macroeconomic data.';
comment on schema FINBANK.MARTS is 'Governed analytics marts consumed by dashboards and the AI risk copilot.';
comment on table FINBANK.MARTS.MART_CUSTOMER_EXPOSURE is 'Customer-level credit exposure mart with delinquency-derived portfolio status.';
comment on table FINBANK.MARTS.MART_CREDIT_MACRO_CONTEXT is 'Portfolio exposure summarized with BCB macroeconomic context for recruiter walkthroughs.';
