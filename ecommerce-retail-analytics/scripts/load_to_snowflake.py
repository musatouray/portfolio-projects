"""
Load CSV data from data/raw/ into Snowflake RAW schema.

This script connects to Snowflake using key-pair authentication,
creates tables based on CSV structure, and loads data using PUT/COPY INTO.
"""

import os
from pathlib import Path

import pandas as pd
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
from snowflake.connector import connect
from snowflake.connector.pandas_tools import write_pandas


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
ENV_FILE = PROJECT_ROOT / ".env"

# CSV file to table name mapping
TABLE_MAPPING = {
    "olist_orders_dataset.csv": "orders",
    "us_customers_dataset.csv": "customers",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "us_sellers_dataset.csv": "sellers",
    "us_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "product_category_translation",
}


def load_private_key():
    """Load the private key for Snowflake authentication."""
    private_key_path = Path.home() / ".snowflake" / "rsa_key.p8"

    if not private_key_path.exists():
        raise FileNotFoundError(
            f"Private key not found at {private_key_path}. "
            "Please set up key-pair authentication."
        )

    passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
    passphrase_bytes = passphrase.encode() if passphrase else None

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase_bytes,
            backend=default_backend()
        )

    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )


def get_snowflake_connection():
    """Create a Snowflake connection using environment variables."""
    private_key_bytes = load_private_key()

    conn = connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=private_key_bytes,
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )

    return conn


def infer_snowflake_type(dtype) -> str:
    """Map pandas dtype to Snowflake data type."""
    dtype_str = str(dtype)

    if "int" in dtype_str:
        return "INTEGER"
    elif "float" in dtype_str:
        return "FLOAT"
    elif "bool" in dtype_str:
        return "BOOLEAN"
    elif "datetime" in dtype_str:
        return "TIMESTAMP"
    else:
        return "VARCHAR"


def create_table_from_df(cursor, table_name: str, df: pd.DataFrame) -> None:
    """Create a Snowflake table based on DataFrame structure."""
    columns = []
    for col_name, dtype in df.dtypes.items():
        sf_type = infer_snowflake_type(dtype)
        # Escape column names with special characters
        safe_col_name = f'"{col_name}"'
        columns.append(f"{safe_col_name} {sf_type}")

    columns_sql = ",\n    ".join(columns)
    create_sql = f"""
    CREATE OR REPLACE TABLE {table_name} (
        {columns_sql}
    )
    """

    cursor.execute(create_sql)
    print(f"  Created table: {table_name}")


def load_csv_to_snowflake(conn, csv_path: Path, table_name: str) -> int:
    """Load a CSV file into a Snowflake table."""
    print(f"\nProcessing: {csv_path.name} -> {table_name}")

    # Read CSV into DataFrame
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  Read {len(df):,} rows from CSV")

    # Normalize column names (uppercase for Snowflake)
    df.columns = [col.upper() for col in df.columns]

    cursor = conn.cursor()

    try:
        # Create table based on DataFrame structure
        create_table_from_df(cursor, table_name, df)

        # Use write_pandas to efficiently load data
        success, num_chunks, num_rows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=table_name.upper(),
            quote_identifiers=False
        )

        if success:
            print(f"  Loaded {num_rows:,} rows in {num_chunks} chunk(s)")
        else:
            print(f"  Warning: Load may have had issues")

        # Verify row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        actual_count = cursor.fetchone()[0]
        print(f"  Verified: {actual_count:,} rows in table")

        return actual_count

    finally:
        cursor.close()


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv(ENV_FILE)

    print("=" * 60)
    print("Snowflake Data Loader")
    print("=" * 60)
    print(f"\nSource: {DATA_RAW_DIR}")
    print(f"Target: {os.getenv('SNOWFLAKE_DATABASE')}.{os.getenv('SNOWFLAKE_SCHEMA')}")
    print(f"Warehouse: {os.getenv('SNOWFLAKE_WAREHOUSE')}")

    # Verify CSV files exist
    missing_files = []
    for csv_file in TABLE_MAPPING.keys():
        if not (DATA_RAW_DIR / csv_file).exists():
            missing_files.append(csv_file)

    if missing_files:
        print(f"\nError: Missing CSV files: {missing_files}")
        print("Run download_kaggle_data.py first.")
        return

    # Connect to Snowflake
    print("\nConnecting to Snowflake...")
    conn = get_snowflake_connection()
    print("Connected successfully")

    # Load each CSV file
    results = {}

    try:
        for csv_file, table_name in TABLE_MAPPING.items():
            csv_path = DATA_RAW_DIR / csv_file
            row_count = load_csv_to_snowflake(conn, csv_path, table_name)
            results[table_name] = row_count
    finally:
        conn.close()
        print("\nConnection closed")

    # Print summary
    print("\n" + "=" * 60)
    print("Load Complete - Summary")
    print("=" * 60)
    print(f"\n{'Table':<35} {'Rows':>15}")
    print("-" * 50)

    total_rows = 0
    for table_name, row_count in results.items():
        print(f"{table_name:<35} {row_count:>15,}")
        total_rows += row_count

    print("-" * 50)
    print(f"{'TOTAL':<35} {total_rows:>15,}")


if __name__ == "__main__":
    main()
