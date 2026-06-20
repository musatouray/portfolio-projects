"""
Synthetic Data Generator for E-Commerce Analytics.

This module generates synthetic order data using customer segmentation logic
to achieve a target repeat purchase rate. It uses real customer, product, and
seller data from Snowflake as reference data for realistic generation.

Key Features:
- RFM-based customer segmentation (one_time, occasional, loyal, champion)
- Weighted random selection favoring high-value segments
- Deterministic generation using random.Random(seed) and Faker.seed()
- Respects segment-based order limits

Usage:
    from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

    generator = SyntheticDataGenerator(seed=42, config=CONFIG)
    generator.load_reference_data()
    customer_segments = generator.assign_customer_segments()
"""

import hashlib
import os
import random
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from faker import Faker

# Load environment variables
load_dotenv()

# Configuration for synthetic data generation
CONFIG = {
    "seed": 42,
    "repeat_rate_target": 0.35,  # 35% repeat purchase rate target
    "base_daily_orders": 135,
    "max_daily_orders": 500,
    "growth_end_date": "2026-06-19",
    "backfill_start_date": "2018-10-18",
    "customer_segments": {
        "one_time": 0.60,      # 60% one-time purchasers
        "occasional": 0.25,    # 25% occasional buyers (2-4 orders)
        "loyal": 0.12,         # 12% loyal customers (5-10 orders)
        "champion": 0.03,      # 3% champion customers (11+ orders)
    },
    "segment_max_orders": {
        "one_time": 1,
        "occasional": 4,
        "loyal": 10,
        "champion": 50,
    },
    "segment_weights": {
        "one_time": 0,         # Not selected after first order
        "occasional": 1.0,     # Base weight
        "loyal": 3.0,          # 3x more likely than occasional
        "champion": 10.0,      # 10x more likely than occasional
    },
}


class SyntheticDataGenerator:
    """
    Generate synthetic e-commerce order data with customer segmentation.

    This class implements a weighted random selection algorithm that assigns
    customers to segments (one_time, occasional, loyal, champion) and generates
    orders respecting each segment's behavioral patterns.

    Attributes:
        seed (int): Random seed for reproducibility
        config (dict): Configuration parameters
        rng (random.Random): Random number generator instance
        faker (Faker): Faker instance for generating realistic data
        customer_ids (list): Customer IDs loaded from Snowflake
        product_data (list): Product data loaded from Snowflake
        seller_ids (list): Seller IDs loaded from Snowflake
        customer_segments (dict): Mapping of customer_id -> segment
        customer_order_counts (dict): Tracking of orders per customer
    """

    def __init__(self, seed: int, config: dict):
        """
        Initialize the synthetic data generator.

        Args:
            seed (int): Random seed for reproducibility
            config (dict): Configuration dictionary with generation parameters
        """
        self.seed = seed
        self.config = config
        self.rng = random.Random(seed)
        self.faker = Faker()
        Faker.seed(seed)

        # Reference data (loaded from Snowflake)
        self.customer_ids = []
        self.product_data = []
        self.seller_ids = []

        # Customer segmentation
        self.customer_segments = {}
        self.customer_order_counts = {}

    def load_reference_data(self) -> None:
        """
        Load reference data from Snowflake.

        Queries the production database to get:
        - Customer IDs from dim_customers
        - Product data (id, category, price) from dim_products
        - Seller IDs from dim_sellers

        This ensures generated orders reference real entities in the warehouse.
        """
        # Get Snowflake credentials from environment
        conn = snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            private_key_path=os.path.expanduser("~/.snowflake/rsa_key.p8"),
            private_key_passphrase=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )

        try:
            cursor = conn.cursor()

            # Load customer IDs
            cursor.execute("""
                SELECT customer_unique_id
                FROM dim_customers
                ORDER BY customer_unique_id
            """)
            self.customer_ids = [row[0] for row in cursor.fetchall()]

            # Load product data
            cursor.execute("""
                SELECT product_id, product_category_name_english, price
                FROM dim_products
                WHERE price IS NOT NULL
                ORDER BY product_id
            """)
            self.product_data = cursor.fetchall()

            # Load seller IDs
            cursor.execute("""
                SELECT seller_id
                FROM dim_sellers
                ORDER BY seller_id
            """)
            self.seller_ids = [row[0] for row in cursor.fetchall()]

        finally:
            cursor.close()
            conn.close()

    def assign_customer_segments(self) -> dict[str, str]:
        """
        Assign each customer to a segment using weighted random distribution.

        Uses the segment percentages defined in config to assign customers
        to one_time, occasional, loyal, or champion segments. The assignment
        is deterministic based on the seed.

        Returns:
            dict: Mapping of customer_id -> segment_name

        Example:
            {
                "CUST_001": "champion",
                "CUST_002": "one_time",
                "CUST_003": "occasional",
                ...
            }
        """
        segments = list(self.config["customer_segments"].keys())
        weights = [self.config["customer_segments"][s] for s in segments]

        for customer_id in self.customer_ids:
            segment = self.rng.choices(segments, weights=weights, k=1)[0]
            self.customer_segments[customer_id] = segment
            self.customer_order_counts[customer_id] = 0

        return self.customer_segments

    def _select_customer(self, date: datetime) -> Optional[str]:
        """
        Select a customer for an order on the given date.

        Implements weighted random selection that:
        1. Filters out customers who have reached their segment's max orders
        2. Weights remaining customers by their segment's selection weight
        3. Returns None if no eligible customers remain

        Args:
            date (datetime): The date for which to select a customer

        Returns:
            Optional[str]: Selected customer_id or None if no eligible customers
        """
        # Get eligible customers (haven't reached max orders for their segment)
        eligible_customers = []
        eligible_weights = []

        for customer_id in self.customer_ids:
            segment = self.customer_segments[customer_id]
            current_orders = self.customer_order_counts[customer_id]
            max_orders = self.config["segment_max_orders"][segment]

            if current_orders < max_orders:
                eligible_customers.append(customer_id)
                weight = self.config["segment_weights"][segment]
                # For one_time customers, weight is 0 after they've made their first purchase
                # But we still include them in the first round
                if segment == "one_time" and current_orders > 0:
                    weight = 0
                eligible_weights.append(weight)

        if not eligible_customers:
            return None

        # Handle case where all weights are 0
        if sum(eligible_weights) == 0:
            return None

        # Select customer using weighted random choice
        selected_customer = self.rng.choices(
            eligible_customers, weights=eligible_weights, k=1
        )[0]

        return selected_customer

    def calculate_daily_orders(self, date: datetime) -> int:
        """
        Calculate the number of orders to generate for a given date.

        Uses a linear growth curve from base_daily_orders to max_daily_orders
        over the period from backfill_start_date to growth_end_date.

        Formula: base + (max - base) * days_elapsed / max_days

        Args:
            date (datetime): The date for which to calculate daily orders

        Returns:
            int: Number of orders to generate for this date

        Example:
            Oct 2018: ~135 orders/day
            Jun 2023: ~380 orders/day
            Jun 2026: ~500 orders/day
        """
        base_orders = self.config["base_daily_orders"]
        max_orders = self.config["max_daily_orders"]
        start_date = datetime.strptime(self.config["backfill_start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(self.config["growth_end_date"], "%Y-%m-%d")

        # Calculate days elapsed and total days in growth period
        days_elapsed = (date - start_date).days
        max_days = (end_date - start_date).days

        # Linear growth formula
        daily_orders = base_orders + (max_orders - base_orders) * days_elapsed / max_days

        return int(daily_orders)

    def generate_order_id(self, date: datetime, sequence: int) -> str:
        """
        Generate a deterministic synthetic order ID.

        Format: syn_{YYYYMMDD}_{sequence:06d}_{hash:8}
        Example: syn_20240115_000042_a3f8c921

        The hash is the first 8 characters of MD5({seed}_{date_str}_{sequence})
        to ensure deterministic generation.

        Args:
            date (datetime): The order date
            sequence (int): The sequence number for this date (0-indexed)

        Returns:
            str: Generated order ID (28 characters)
        """
        date_str = date.strftime("%Y%m%d")
        sequence_str = f"{sequence:06d}"

        # Generate deterministic hash
        hash_input = f"{self.seed}_{date_str}_{sequence}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()[:8]

        order_id = f"syn_{date_str}_{sequence_str}_{hash_digest}"

        return order_id

    def generate_orders_for_date(self, date: datetime) -> pd.DataFrame:
        """
        Generate all orders for a given date.

        Creates a DataFrame with order IDs, customer assignments, status,
        and timestamp flow (purchase → approved → carrier → delivered).

        Status distribution:
        - delivered: 97%
        - shipped: 1%
        - canceled: 1%
        - unavailable: 0.5%
        - processing: 0.5%

        Timestamp flow:
        - purchase: random hour of the day
        - approved: 0-24 hours after purchase
        - carrier: 1-5 days after approval
        - delivered: 3-20 days after carrier
        - estimated: actual delivery + random variance (-3 to +5 days)

        For non-delivered orders, appropriate timestamps are cleared:
        - canceled: no carrier/delivery dates
        - shipped: no delivery date
        - unavailable/processing: no carrier/delivery dates

        Args:
            date (datetime): The date for which to generate orders

        Returns:
            pd.DataFrame: Orders with columns: order_id, customer_id, order_status,
                         order_purchase_timestamp, order_approved_at,
                         order_delivered_carrier_date, order_delivered_customer_date,
                         order_estimated_delivery_date
        """
        # Reset RNG for this date for deterministic generation
        date_seed = self.seed + int(date.strftime("%Y%m%d"))
        date_rng = random.Random(date_seed)

        # Calculate number of orders for this date
        num_orders = self.calculate_daily_orders(date)

        orders = []
        for sequence in range(num_orders):
            # Generate order ID
            order_id = self.generate_order_id(date, sequence)

            # Select customer
            customer_id = self._select_customer(date)
            if customer_id is None:
                # No eligible customers remaining
                break

            # Increment customer's order count
            self.customer_order_counts[customer_id] += 1

            # Assign order status
            status_roll = date_rng.random()
            if status_roll < 0.97:
                status = "delivered"
            elif status_roll < 0.98:
                status = "shipped"
            elif status_roll < 0.99:
                status = "canceled"
            elif status_roll < 0.995:
                status = "unavailable"
            else:
                status = "processing"

            # Generate timestamp flow
            # Purchase: random hour of the day
            purchase_hour = date_rng.randint(0, 23)
            purchase_minute = date_rng.randint(0, 59)
            purchase_second = date_rng.randint(0, 59)
            purchase_timestamp = datetime(
                date.year, date.month, date.day,
                purchase_hour, purchase_minute, purchase_second
            )

            # Approved: 0-24 hours after purchase
            approved_hours = date_rng.uniform(0, 24)
            approved_at = purchase_timestamp + timedelta(hours=approved_hours)

            # Initialize carrier and delivery dates
            carrier_date = None
            delivered_date = None
            estimated_date = None

            # Set timestamps based on status
            if status == "delivered":
                # Carrier: 1-5 days after approval
                carrier_days = date_rng.uniform(1, 5)
                carrier_date = approved_at + timedelta(days=carrier_days)

                # Delivered: 3-20 days after carrier
                delivery_days = date_rng.uniform(3, 20)
                delivered_date = carrier_date + timedelta(days=delivery_days)

                # Estimated: actual delivery + random variance (-3 to +5 days)
                estimate_variance = date_rng.uniform(-3, 5)
                estimated_date = delivered_date + timedelta(days=estimate_variance)

            elif status == "shipped":
                # Carrier: 1-5 days after approval, but not yet delivered
                carrier_days = date_rng.uniform(1, 5)
                carrier_date = approved_at + timedelta(days=carrier_days)

                # Estimated: carrier date + expected delivery time
                estimate_days = date_rng.uniform(5, 15)
                estimated_date = carrier_date + timedelta(days=estimate_days)

            # For canceled, unavailable, processing: no carrier/delivery dates

            orders.append({
                "order_id": order_id,
                "customer_id": customer_id,
                "order_status": status,
                "order_purchase_timestamp": purchase_timestamp,
                "order_approved_at": approved_at,
                "order_delivered_carrier_date": carrier_date,
                "order_delivered_customer_date": delivered_date,
                "order_estimated_delivery_date": estimated_date,
            })

        return pd.DataFrame(orders)
