from __future__ import annotations

import random
import uuid
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

fake = Faker("pt_BR")
random.seed(42)
np.random.seed(42)


def make_customers(n: int = 1_000) -> pd.DataFrame:
    segments = ["PF_LOW_INCOME", "PF_MASS", "PF_AFFLUENT", "PJ_SMALL", "PJ_MID"]
    states = ["SP", "RJ", "MG", "DF", "PR", "SC", "RS", "BA", "PE", "GO"]

    rows = []
    for _ in range(n):
        segment = random.choice(segments)
        rows.append(
            {
                "customer_id": str(uuid.uuid4()),
                "customer_name": fake.name() if not segment.startswith("PJ") else fake.company(),
                "document_type": "CNPJ" if segment.startswith("PJ") else "CPF",
                "segment": segment,
                "state": random.choice(states),
                "created_at": fake.date_between(start_date="-5y", end_date="-30d"),
                "internal_score": int(np.clip(np.random.normal(650, 120), 250, 950)),
            }
        )
    return pd.DataFrame(rows)


def make_accounts(customers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, c in customers.iterrows():
        for _ in range(random.randint(1, 3)):
            rows.append(
                {
                    "account_id": str(uuid.uuid4()),
                    "customer_id": c["customer_id"],
                    "account_type": random.choice(["CHECKING", "SAVINGS", "INVESTMENT"]),
                    "opened_at": fake.date_between(start_date=c["created_at"], end_date="today"),
                    "status": random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "BLOCKED", "CLOSED"]),
                }
            )
    return pd.DataFrame(rows)


def make_transactions(accounts: pd.DataFrame, n: int = 20_000) -> pd.DataFrame:
    channels = ["PIX", "CARD", "ATM", "BRANCH", "TED", "APP"]
    transaction_types = ["DEBIT", "CREDIT", "TRANSFER", "PAYMENT", "WITHDRAWAL"]

    accounts_records = accounts[["customer_id", "account_id"]].to_dict(orient="records")
    sampled_indices = np.random.randint(0, len(accounts_records), size=n)

    today = date.today()
    start_date = today - timedelta(days=18 * 30)
    days_range = (today - start_date).days
    random_offsets = np.random.randint(0, days_range, size=n)
    precomputed_dates = [start_date + timedelta(days=int(offset)) for offset in random_offsets]

    rows = []
    for i, idx in enumerate(sampled_indices):
        acc = accounts_records[idx]
        amount = float(np.round(np.random.lognormal(mean=5.2, sigma=1.1), 2))
        suspicious = amount > 2_500 and random.random() < 0.10

        rows.append(
            {
                "transaction_id": str(uuid.uuid4()),
                "customer_id": acc["customer_id"],
                "account_id": acc["account_id"],
                "transaction_date": precomputed_dates[i],
                "channel": random.choice(channels),
                "transaction_type": random.choice(transaction_types),
                "amount": amount,
                "is_suspicious": suspicious,
            }
        )
    return pd.DataFrame(rows)


def make_loans(customers: pd.DataFrame, n: int = 3_000) -> pd.DataFrame:
    products = ["PERSONAL_LOAN", "AUTO_LOAN", "MORTGAGE", "WORKING_CAPITAL", "CREDIT_CARD"]

    rows = []
    eligible = customers.sample(n=min(n, len(customers)), replace=True)
    for _, c in eligible.iterrows():
        principal = float(np.round(np.random.lognormal(mean=10.5, sigma=0.8), 2))
        dpd = int(max(0, np.random.poisson(lam=8) - 5))
        if random.random() < 0.08:
            dpd += random.randint(30, 120)

        origination = fake.date_between(start_date="-3y", end_date="-60d")
        maturity = origination + timedelta(days=random.choice([365, 730, 1095, 1460, 1825]))
        outstanding = float(np.round(principal * random.uniform(0.15, 1.0), 2))

        rating = (
            "AA" if dpd == 0 and c["internal_score"] >= 750 else
            "A" if dpd <= 5 and c["internal_score"] >= 680 else
            "B" if dpd <= 15 else
            "C" if dpd <= 30 else
            "D" if dpd <= 90 else
            "E"
        )

        rows.append(
            {
                "loan_id": str(uuid.uuid4()),
                "customer_id": c["customer_id"],
                "product_type": random.choice(products),
                "origination_date": origination,
                "maturity_date": maturity,
                "principal_amount": principal,
                "outstanding_balance": outstanding,
                "interest_rate": round(random.uniform(0.012, 0.055), 4),
                "days_past_due": dpd,
                "risk_rating": rating,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    customers = make_customers()
    accounts = make_accounts(customers)
    transactions = make_transactions(accounts)
    loans = make_loans(customers)

    customers.to_csv(RAW_DIR / "customers.csv", index=False)
    accounts.to_csv(RAW_DIR / "accounts.csv", index=False)
    transactions.to_csv(RAW_DIR / "transactions.csv", index=False)
    loans.to_csv(RAW_DIR / "loans.csv", index=False)

    print("Synthetic banking data generated in data/raw/")
    print(f"customers: {len(customers):,}")
    print(f"accounts: {len(accounts):,}")
    print(f"transactions: {len(transactions):,}")
    print(f"loans: {len(loans):,}")


if __name__ == "__main__":
    main()
