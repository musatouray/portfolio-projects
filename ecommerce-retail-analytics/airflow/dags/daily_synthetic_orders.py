"""
Daily DAG for synthetic order data.

Generates synthetic orders for the previous day and loads to Snowflake.
Scheduled to run daily at 2:00 AM UTC.
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

from utils.slack_alerts import slack_failure_callback

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
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "on_failure_callback": slack_failure_callback,
}


def generate_daily(**context):
    """Generate synthetic data for the previous day."""
    # Use execution_date (logical date) for the data being generated
    execution_date = context["execution_date"]
    target_date = execution_date.date()

    print(f"Generating synthetic data for {target_date}")

    # Initialize generator
    generator = SyntheticDataGenerator(seed=CONFIG["seed"], config=CONFIG)
    generator.load_reference_data()

    # Create output directories
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for table in ["orders", "order_items", "order_payments", "order_reviews"]:
        (LOCAL_DATA_DIR / table).mkdir(exist_ok=True)

    # Generate data for target date
    target_datetime = datetime.combine(target_date, datetime.min.time())
    data = generator.generate_all_for_date(target_datetime)

    # Save to local CSV files
    date_str = target_date.strftime("%Y-%m-%d")
    files_generated = []

    for table_name, df in data.items():
        filename = f"{table_name}_{date_str}.csv"
        filepath = LOCAL_DATA_DIR / table_name / filename
        df.to_csv(filepath, index=False)
        files_generated.append(str(filepath))
        print(f"Generated {filepath}: {len(df)} rows")

    context["ti"].xcom_push(key="target_date", value=date_str)
    context["ti"].xcom_push(key="order_count", value=len(data["orders"]))

    return files_generated


def upload_daily_to_s3(**context):
    """Upload daily CSV files to S3."""
    target_date = context["ti"].xcom_pull(key="target_date")

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

    uploaded_count = 0

    for table in ["orders", "order_items", "order_payments", "order_reviews"]:
        filename = f"{table}_{target_date}.csv"
        filepath = LOCAL_DATA_DIR / table / filename

        if filepath.exists():
            s3_key = f"{table}/{filename}"
            s3_client.upload_file(str(filepath), S3_BUCKET, s3_key)
            uploaded_count += 1
            print(f"Uploaded {s3_key}")

    print(f"Upload complete: {uploaded_count} files")
    return uploaded_count


def cleanup_daily_files(**context):
    """Remove daily CSV files after successful upload."""
    target_date = context["ti"].xcom_pull(key="target_date")

    for table in ["orders", "order_items", "order_payments", "order_reviews"]:
        filename = f"{table}_{target_date}.csv"
        filepath = LOCAL_DATA_DIR / table / filename

        if filepath.exists():
            filepath.unlink()
            print(f"Removed {filepath}")

    return "Cleanup complete"


# SQL for COPY INTO specific date file
COPY_DAILY_SQL = """
COPY INTO RAW.{table}
FROM @RAW.raw_ecommerce_s3_stage/{folder}/{table}_{date}.csv
FILE_FORMAT = RAW.csv_format
ON_ERROR = 'ABORT_STATEMENT';
"""


def get_copy_sql(table: str, folder: str, **context) -> str:
    """Generate COPY SQL for specific date."""
    target_date = context["ti"].xcom_pull(key="target_date")
    return COPY_DAILY_SQL.format(table=table, folder=folder, date=target_date)


with DAG(
    dag_id="daily_synthetic_orders",
    default_args=default_args,
    description="Generate and load daily synthetic order data",
    schedule_interval="0 2 * * *",  # 2:00 AM UTC daily
    start_date=datetime(2026, 6, 20),  # Start after backfill
    catchup=False,
    tags=["synthetic", "daily"],
) as dag:

    generate = PythonOperator(
        task_id="generate_daily",
        python_callable=generate_daily,
        retries=1,
        retry_delay=timedelta(seconds=30),
    )

    upload = PythonOperator(
        task_id="upload_to_s3",
        python_callable=upload_daily_to_s3,
        retries=3,
        retry_delay=timedelta(seconds=60),
    )

    # Use PythonOperator to generate dynamic SQL
    def copy_table(table: str, folder: str):
        def _copy(**context):
            from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

            target_date = context["ti"].xcom_pull(key="target_date")
            sql = COPY_DAILY_SQL.format(table=table.upper(), folder=folder, date=target_date)

            hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)
            hook.run(sql)
            print(f"COPY INTO {table} complete for {target_date}")

        return _copy

    copy_orders = PythonOperator(
        task_id="copy_orders_to_snowflake",
        python_callable=copy_table("orders", "orders"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    copy_order_items = PythonOperator(
        task_id="copy_order_items_to_snowflake",
        python_callable=copy_table("order_items", "order_items"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    copy_order_payments = PythonOperator(
        task_id="copy_order_payments_to_snowflake",
        python_callable=copy_table("order_payments", "order_payments"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    copy_order_reviews = PythonOperator(
        task_id="copy_order_reviews_to_snowflake",
        python_callable=copy_table("order_reviews", "order_reviews"),
        retries=3,
        retry_delay=timedelta(seconds=120),
    )

    cleanup = PythonOperator(
        task_id="cleanup_local_files",
        python_callable=cleanup_daily_files,
        trigger_rule="all_success",
    )

    # Task dependencies
    generate >> upload
    upload >> [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews]
    [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews] >> cleanup
