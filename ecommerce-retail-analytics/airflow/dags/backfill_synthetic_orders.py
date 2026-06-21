"""
Backfill DAG for synthetic order data.

Generates synthetic orders from 2018-10-18 to 2026-06-19 (~7.7 years).
Manual trigger only with configurable date range.

Usage:
    airflow dags trigger backfill_synthetic_orders \
        --conf '{"start_date": "2018-10-18", "end_date": "2026-06-19"}'
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/airflow/.env")

# Import generator
import sys
sys.path.insert(0, "/opt/airflow")
from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG


# Constants
S3_BUCKET = os.getenv("S3_BUCKET", "ecommerce-retail-analytics-raw")
LOCAL_DATA_DIR = Path("/opt/airflow/data/synthetic")
SNOWFLAKE_CONN_ID = "snowflake_default"


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


def load_reference_data(**context):
    """Load reference data from Snowflake into XCom."""
    generator = SyntheticDataGenerator(seed=CONFIG["seed"], config=CONFIG)
    generator.load_reference_data()

    # Store counts for logging
    context["ti"].xcom_push(key="customer_count", value=len(generator._customer_ids))
    context["ti"].xcom_push(key="product_count", value=len(generator._product_data))

    print(f"Loaded {len(generator._customer_ids)} customers")
    print(f"Loaded {len(generator._product_data)} products")

    return "Reference data loaded"


def generate_batch(**context):
    """Generate synthetic data for date range."""
    conf = context["dag_run"].conf or {}
    start_date_str = conf.get("start_date", CONFIG["backfill_start_date"])
    end_date_str = conf.get("end_date", CONFIG["growth_end_date"])

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    print(f"Generating data from {start_date_str} to {end_date_str}")

    # Initialize generator
    generator = SyntheticDataGenerator(seed=CONFIG["seed"], config=CONFIG)
    generator.load_reference_data()

    # Create output directories
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for table in ["orders", "order_items", "order_payments", "order_reviews"]:
        (LOCAL_DATA_DIR / table).mkdir(exist_ok=True)

    # Generate data day by day
    current_date = start_date
    total_orders = 0
    files_generated = []

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        # Generate all data for this date
        data = generator.generate_all_for_date(current_date)

        # Save to local CSV files
        for table_name, df in data.items():
            filename = f"{table_name}_{date_str}.csv"
            filepath = LOCAL_DATA_DIR / table_name / filename
            df.to_csv(filepath, index=False)
            files_generated.append(str(filepath))

        total_orders += len(data["orders"])

        if current_date.day == 1:  # Log monthly progress
            print(f"Generated up to {date_str}, total orders: {total_orders}")

        current_date += timedelta(days=1)

    print(f"Generation complete: {total_orders} orders, {len(files_generated)} files")
    context["ti"].xcom_push(key="total_orders", value=total_orders)
    context["ti"].xcom_push(key="files_generated", value=len(files_generated))

    return files_generated


def upload_to_s3(**context):
    """Upload generated CSV files to S3."""
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

    uploaded_count = 0

    for table in ["orders", "order_items", "order_payments", "order_reviews"]:
        table_dir = LOCAL_DATA_DIR / table
        if not table_dir.exists():
            continue

        for filepath in table_dir.glob("*.csv"):
            s3_key = f"{table}/{filepath.name}"
            s3_client.upload_file(str(filepath), S3_BUCKET, s3_key)
            uploaded_count += 1

            if uploaded_count % 100 == 0:
                print(f"Uploaded {uploaded_count} files...")

    print(f"Upload complete: {uploaded_count} files to s3://{S3_BUCKET}/")
    context["ti"].xcom_push(key="files_uploaded", value=uploaded_count)

    return uploaded_count


def cleanup_local_files(**context):
    """Remove local CSV files after successful upload."""
    import shutil

    for table in ["orders", "order_items", "order_payments", "order_reviews"]:
        table_dir = LOCAL_DATA_DIR / table
        if table_dir.exists():
            shutil.rmtree(table_dir)
            print(f"Removed {table_dir}")

    return "Cleanup complete"


# SQL for COPY INTO (parameterized by table)
COPY_SQL_TEMPLATE = """
COPY INTO RAW.{table}
FROM @RAW.raw_ecommerce_s3_stage/{folder}/
FILE_FORMAT = RAW.csv_format
PATTERN = '.*\\.csv'
ON_ERROR = 'CONTINUE';
"""


with DAG(
    dag_id="backfill_synthetic_orders",
    default_args=default_args,
    description="Generate and load synthetic order data (backfill)",
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["synthetic", "backfill"],
    params={
        "start_date": "2018-10-18",
        "end_date": "2026-06-19",
    },
) as dag:

    load_ref_data = PythonOperator(
        task_id="load_reference_data",
        python_callable=load_reference_data,
        retries=3,
        retry_delay=timedelta(seconds=60),
    )

    generate = PythonOperator(
        task_id="generate_batch",
        python_callable=generate_batch,
        retries=1,
        retry_delay=timedelta(seconds=30),
        execution_timeout=timedelta(hours=4),  # Allow long backfill
    )

    upload = PythonOperator(
        task_id="upload_to_s3",
        python_callable=upload_to_s3,
        retries=3,
        retry_delay=timedelta(seconds=60),
    )

    copy_orders = SnowflakeOperator(
        task_id="copy_orders_to_snowflake",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql=COPY_SQL_TEMPLATE.format(table="ORDERS", folder="orders"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    copy_order_items = SnowflakeOperator(
        task_id="copy_order_items_to_snowflake",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql=COPY_SQL_TEMPLATE.format(table="ORDER_ITEMS", folder="order_items"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    copy_order_payments = SnowflakeOperator(
        task_id="copy_order_payments_to_snowflake",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql=COPY_SQL_TEMPLATE.format(table="ORDER_PAYMENTS", folder="order_payments"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    copy_order_reviews = SnowflakeOperator(
        task_id="copy_order_reviews_to_snowflake",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql=COPY_SQL_TEMPLATE.format(table="ORDER_REVIEWS", folder="order_reviews"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    cleanup = PythonOperator(
        task_id="cleanup_local_files",
        python_callable=cleanup_local_files,
        trigger_rule="all_success",
    )

    # Task dependencies
    load_ref_data >> generate >> upload
    upload >> [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews]
    [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews] >> cleanup
