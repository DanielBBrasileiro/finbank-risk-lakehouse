create schema if not exists raw;
create schema if not exists analytics;
create schema if not exists analytics_staging;
create schema if not exists analytics_intermediate;
create schema if not exists analytics_marts;
create schema if not exists snapshots;

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'finbank_reader') then
        create role finbank_reader login password 'finbank_reader';
    end if;
end
$$;

do $$
begin
    execute format('grant connect on database %I to finbank_reader', current_database());
end
$$;
grant usage on schema raw, analytics, analytics_staging, analytics_intermediate, analytics_marts, snapshots
to finbank_reader;

alter default privileges in schema raw grant select on tables to finbank_reader;
alter default privileges in schema analytics grant select on tables to finbank_reader;
alter default privileges in schema analytics_staging grant select on tables to finbank_reader;
alter default privileges in schema analytics_intermediate grant select on tables to finbank_reader;
alter default privileges in schema analytics_marts grant select on tables to finbank_reader;
alter default privileges in schema snapshots grant select on tables to finbank_reader;

create table if not exists raw.customers (
    customer_id text primary key,
    customer_name text not null,
    document_type text not null check (document_type in ('CPF', 'CNPJ')),
    segment text not null check (segment in ('PF_LOW_INCOME', 'PF_MASS', 'PF_AFFLUENT', 'PJ_SMALL', 'PJ_MID')),
    state text not null,
    created_at date not null,
    internal_score int not null check (internal_score between 0 and 1000)
);

create table if not exists raw.accounts (
    account_id text primary key,
    customer_id text not null references raw.customers (customer_id),
    account_type text not null check (account_type in ('CHECKING', 'SAVINGS', 'INVESTMENT')),
    opened_at date not null,
    status text not null check (status in ('ACTIVE', 'BLOCKED', 'CLOSED')),
    unique (account_id, customer_id)
);

create table if not exists raw.transactions (
    transaction_id text primary key,
    customer_id text not null,
    account_id text not null,
    transaction_date date not null,
    channel text not null check (channel in ('PIX', 'CARD', 'ATM', 'BRANCH', 'TED', 'APP')),
    transaction_type text not null check (transaction_type in ('DEBIT', 'CREDIT', 'TRANSFER', 'PAYMENT', 'WITHDRAWAL')),
    amount numeric(18,2) not null check (amount >= 0),
    is_suspicious boolean not null,
    foreign key (account_id, customer_id) references raw.accounts (account_id, customer_id)
);

create table if not exists raw.loans (
    loan_id text primary key,
    customer_id text not null references raw.customers (customer_id),
    product_type text not null check (product_type in ('PERSONAL_LOAN', 'AUTO_LOAN', 'MORTGAGE', 'WORKING_CAPITAL', 'CREDIT_CARD')),
    origination_date date not null,
    maturity_date date not null check (maturity_date > origination_date),
    principal_amount numeric(18,2) not null check (principal_amount >= 0),
    outstanding_balance numeric(18,2) not null check (outstanding_balance >= 0),
    interest_rate numeric(10,4) not null check (interest_rate >= 0),
    days_past_due int not null check (days_past_due >= 0),
    risk_rating text not null check (risk_rating in ('AA', 'A', 'B', 'C', 'D', 'E'))
);

create table if not exists raw.macro_indicators (
    observation_date date not null,
    indicator_name text not null check (indicator_name in ('selic', 'credit_free_total')),
    series_id int not null,
    value numeric(18,4) not null,
    primary key (observation_date, indicator_name),
    unique (observation_date, series_id)
);

create table if not exists raw.cvm_funds (
    cnpj text not null,
    fund_name text not null,
    fund_type text,
    status text,
    class_type text,
    net_worth numeric(18,2) check (net_worth >= 0)
);

grant select on all tables in schema raw, analytics, analytics_staging, analytics_intermediate, analytics_marts, snapshots
to finbank_reader;
