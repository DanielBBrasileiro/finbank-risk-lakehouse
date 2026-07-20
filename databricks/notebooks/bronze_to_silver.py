# Databricks notebook source
# DBTITLE 1,FinBank Risk Lakehouse - Bronze to Silver Ingestion
# Ingests Bronze Parquet files from S3, cleans and standardizes them, and writes to Silver Delta.

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.getActiveSession()
if spark is None:
    raise RuntimeError("An active Databricks Spark session is required")

def bronze_to_silver(table_name: str, primary_keys: list[str], cleaning_fn=None):
    bronze_path = f"s3://finbank-risk-lake/bronze/{table_name}/"
    silver_path = f"s3://finbank-risk-lake/silver/{table_name}/"

    print(f"Processing {table_name} from Bronze to Silver...")

    # Read Bronze Parquet data
    df = spark.read.format("parquet").load(bronze_path)

    # Standardize column names (lowercase, stripped)
    for col in df.columns:
        df = df.withColumnRenamed(col, col.strip().lower())

    # Deduplicate based on primary keys
    deduped = df.dropDuplicates(primary_keys)

    # Apply custom cleaning if provided
    silver = cleaning_fn(deduped) if cleaning_fn else deduped

    # Add audit columns
    silver = silver.withColumn("ingestion_processed_at", F.current_timestamp())
    
    # Write to Silver Delta Lake
    (
        silver.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(silver_path)
    )
    print(f"Successfully wrote Silver Delta table for {table_name}")

# Custom cleaning functions
def clean_transactions(df):
    return (
        df
        .withColumn("transaction_date", F.to_date("transaction_date"))
        .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
        .withColumn("is_suspicious", F.col("is_suspicious").cast("boolean"))
    )

def clean_customers(df):
    return (
        df
        .withColumn("created_at", F.to_date("created_at"))
        .withColumn("internal_score", F.col("internal_score").cast("int"))
    )

def clean_loans(df):
    return (
        df
        .withColumn("origination_date", F.to_date("origination_date"))
        .withColumn("maturity_date", F.to_date("maturity_date"))
        .withColumn("principal_amount", F.col("principal_amount").cast("decimal(18,2)"))
        .withColumn("outstanding_balance", F.col("outstanding_balance").cast("decimal(18,2)"))
        .withColumn("interest_rate", F.col("interest_rate").cast("decimal(10,4)"))
        .withColumn("days_past_due", F.col("days_past_due").cast("int"))
    )

def clean_accounts(df):
    return (
        df
        .withColumn("opened_at", F.to_date("opened_at"))
    )

def clean_macro(df):
    return (
        df
        .withColumn("observation_date", F.to_date("observation_date"))
        .withColumn("value", F.col("value").cast("decimal(18,4)"))
    )

# Run Bronze-to-Silver ingestion for all tables
bronze_to_silver("customers", ["customer_id"], clean_customers)
bronze_to_silver("accounts", ["account_id"], clean_accounts)
bronze_to_silver("loans", ["loan_id"], clean_loans)
bronze_to_silver("transactions", ["transaction_id"], clean_transactions)
bronze_to_silver("macro_indicators", ["observation_date", "indicator_name"], clean_macro)
