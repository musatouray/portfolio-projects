"""
Validate synthetic data in Snowflake.

Runs validation queries to verify:
- Repeat purchase rate (target: 30-40%)
- Order volume growth curve
- Referential integrity
- No null required fields
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from snowflake.connector import connect
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


# Load environment
ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_FILE)


def get_connection():
    """Create Snowflake connection."""
    private_key_path = Path.home() / ".snowflake" / "rsa_key.p8"
    passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
    passphrase_bytes = passphrase.encode() if passphrase else None

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase_bytes,
            backend=default_backend()
        )

    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=private_key_bytes,
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )


def run_validation():
    """Run all validation queries."""
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 60)
    print("SYNTHETIC DATA VALIDATION REPORT")
    print("=" * 60)

    # 1. Count synthetic orders
    print("\n1. SYNTHETIC ORDER COUNTS")
    cursor.execute("""
        SELECT
            COUNT(*) as total_orders,
            COUNT(DISTINCT customer_id) as unique_customers,
            MIN(order_purchase_timestamp) as min_date,
            MAX(order_purchase_timestamp) as max_date
        FROM orders
        WHERE order_id LIKE 'syn_%'
    """)
    row = cursor.fetchone()
    print(f"   Total synthetic orders: {row[0]:,}")
    print(f"   Unique customers: {row[1]:,}")
    print(f"   Date range: {row[2]} to {row[3]}")

    # 2. Repeat purchase rate
    print("\n2. REPEAT PURCHASE RATE")
    cursor.execute("""
        SELECT
            COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END) * 100.0
            / COUNT(DISTINCT customer_id) AS repeat_rate
        FROM (
            SELECT customer_id, COUNT(*) as order_count
            FROM orders
            WHERE order_id LIKE 'syn_%'
            GROUP BY customer_id
        )
    """)
    repeat_rate = cursor.fetchone()[0]
    status = "PASS" if 30 <= repeat_rate <= 40 else "FAIL"
    print(f"   Repeat rate: {repeat_rate:.1f}% (target: 30-40%) {status}")

    # 3. Order volume growth
    print("\n3. ORDER VOLUME GROWTH")
    cursor.execute("""
        SELECT
            DATE_TRUNC('year', order_purchase_timestamp) AS year,
            COUNT(*) as orders,
            COUNT(*) / 365 AS avg_daily
        FROM orders
        WHERE order_id LIKE 'syn_%'
        GROUP BY 1
        ORDER BY 1
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} orders ({row[2]:.0f}/day)")

    # 4. Referential integrity
    print("\n4. REFERENTIAL INTEGRITY")

    # Orders -> Customers
    cursor.execute("""
        SELECT COUNT(*) FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_id LIKE 'syn_%' AND c.customer_id IS NULL
    """)
    orphan_orders = cursor.fetchone()[0]
    status = "PASS" if orphan_orders == 0 else "FAIL"
    print(f"   Orders with invalid customer_id: {orphan_orders} {status}")

    # Order items -> Orders
    cursor.execute("""
        SELECT COUNT(*) FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.order_id
        WHERE oi.order_id LIKE 'syn_%' AND o.order_id IS NULL
    """)
    orphan_items = cursor.fetchone()[0]
    status = "PASS" if orphan_items == 0 else "FAIL"
    print(f"   Order items with invalid order_id: {orphan_items} {status}")

    # Order items -> Products
    cursor.execute("""
        SELECT COUNT(*) FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id LIKE 'syn_%' AND p.product_id IS NULL
    """)
    orphan_products = cursor.fetchone()[0]
    status = "PASS" if orphan_products == 0 else "FAIL"
    print(f"   Order items with invalid product_id: {orphan_products} {status}")

    # 5. Null checks
    print("\n5. NULL CHECKS")
    cursor.execute("""
        SELECT COUNT(*) FROM orders
        WHERE order_id LIKE 'syn_%'
        AND (order_id IS NULL OR customer_id IS NULL OR order_status IS NULL)
    """)
    null_orders = cursor.fetchone()[0]
    status = "PASS" if null_orders == 0 else "FAIL"
    print(f"   Orders with null required fields: {null_orders} {status}")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run_validation()
