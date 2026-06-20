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

import os
import random
from datetime import datetime
from typing import Optional

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
