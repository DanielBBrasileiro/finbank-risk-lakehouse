# Databricks notebook source
# DBTITLE 1,FinBank Risk Lakehouse - Silver to Gold Features
# Reads Silver Delta tables, aggregates key risk metrics, and writes Gold analytical layers.

from pyspark.sql import functions as F

silver_base_path = "s3://finbank-risk-lake/silver"
gold_base_path = "s3://finbank-risk-lake/gold"

# Load Silver Delta tables
customers = spark.read.format("delta").load(f"{silver_base_path}/customers/")
accounts = spark.read.format("delta").load(f"{silver_base_path}/accounts/")
loans = spark.read.format("delta").load(f"{silver_base_path}/loans/")
transactions = spark.read.format("delta").load(f"{silver_base_path}/transactions/")

# DBTITLE 2,1. Gold Credit Snapshot (customer_credit_snapshot)
# Aggregate loans at the customer level
loan_agg = (
    loans.groupBy("customer_id")
    .agg(
        F.countDistinct("loan_id").alias("loan_count"),
        F.sum("principal_amount").alias("total_principal_amount"),
        F.sum("outstanding_balance").alias("total_outstanding_balance"),
        F.max("days_past_due").alias("max_days_past_due"),
        F.avg("days_past_due").alias("avg_days_past_due")
    )
)

# Join with customer info and derive portfolio status
credit_snapshot = (
    customers.join(loan_agg, "customer_id", "left")
    .na.fill({
        "loan_count": 0,
        "total_principal_amount": 0.0,
        "total_outstanding_balance": 0.0,
        "max_days_past_due": 0,
        "avg_days_past_due": 0.0
    })
    .withColumn(
        "portfolio_status",
        F.when(F.col("max_days_past_due") > 90, "DEFAULT_RISK")
        .when(F.col("max_days_past_due") > 30, "HIGH_RISK")
        .when(F.col("max_days_past_due") > 5, "WATCHLIST")
        .otherwise("PERFORMING")
    )
)

(
    credit_snapshot.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(f"{gold_base_path}/customer_credit_snapshot/")
)

# DBTITLE 3,2. Gold Daily Transactions (daily_transaction_monitoring)
# Aggregate transactions by date and channel
daily_transactions = (
    transactions.groupBy("transaction_date", "channel")
    .agg(
        F.countDistinct("transaction_id").alias("transaction_count"),
        F.sum("amount").alias("total_amount"),
        F.sum(F.when(F.col("is_suspicious") == True, 1).otherwise(0)).alias("suspicious_count")
    )
    .sort("transaction_date", "channel")
)

(
    daily_transactions.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(f"{gold_base_path}/daily_transaction_monitoring/")
)

# DBTITLE 4,3. Gold Account Health (mart_account_health)
# Aggregate accounts by customer
account_agg = (
    accounts.groupBy("customer_id")
    .agg(
        F.count("*").alias("total_accounts"),
        F.sum(F.when(F.col("status") == "ACTIVE", 1).otherwise(0)).alias("active_accounts"),
        F.sum(F.when(F.col("status") == "BLOCKED", 1).otherwise(0)).alias("blocked_accounts"),
        F.sum(F.when(F.col("status") == "CLOSED", 1).otherwise(0)).alias("closed_accounts"),
        F.min("opened_at").alias("earliest_account_opened"),
        F.max("opened_at").alias("latest_account_opened")
    )
)

# Join with customer info and derive account health status
account_health = (
    account_agg.join(customers.select("customer_id", "segment", "state"), "customer_id", "inner")
    .withColumn(
        "account_health_status",
        F.when((F.col("blocked_accounts") > 0) & (F.col("active_accounts") == 0), "FULLY_BLOCKED")
        .when(F.col("blocked_accounts") > 0, "PARTIALLY_BLOCKED")
        .when(F.col("closed_accounts") == F.col("total_accounts"), "ALL_CLOSED")
        .otherwise("HEALTHY")
    )
    .withColumn(
        "active_ratio_pct",
        F.round((F.col("active_accounts") / F.col("total_accounts")) * 100, 1)
    )
    .select(
        "customer_id", "segment", "state", "total_accounts", "active_accounts",
        "blocked_accounts", "closed_accounts", "earliest_account_opened",
        "latest_account_opened", "account_health_status", "active_ratio_pct"
    )
)

(
    account_health.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(f"{gold_base_path}/mart_account_health/")
)

print("Successfully built all Gold Delta tables on Databricks!")
