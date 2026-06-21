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

        # Product data for order items generation
        self._product_data = pd.DataFrame()  # DataFrame with product_id, seller_id, avg_price, avg_freight
        self._product_seller_map = {}  # dict mapping product_id -> seller_id

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
            private_key_file=os.path.expanduser("~/.snowflake/rsa_key.p8"),
            private_key_file_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
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

            # Load product data (for backward compatibility)
            cursor.execute("""
                SELECT product_id, product_category_name_english, price
                FROM dim_products
                WHERE price IS NOT NULL
                ORDER BY product_id
            """)
            self.product_data = cursor.fetchall()

            # Load product data for order items generation
            cursor.execute("""
                SELECT
                    p.product_id,
                    COALESCE(fi.seller_id, 'UNKNOWN') as seller_id,
                    COALESCE(AVG(fi.price), 100.0) as avg_price,
                    COALESCE(AVG(fi.freight_value), 10.0) as avg_freight
                FROM dim_products p
                LEFT JOIN fct_order_items fi ON p.product_id = fi.product_id
                WHERE p.price IS NOT NULL
                GROUP BY p.product_id, fi.seller_id
                ORDER BY p.product_id
            """)
            product_rows = cursor.fetchall()

            # Convert to DataFrame
            self._product_data = pd.DataFrame(
                product_rows,
                columns=["product_id", "seller_id", "avg_price", "avg_freight"]
            )

            # Build product-seller mapping
            self._product_seller_map = dict(
                zip(self._product_data["product_id"], self._product_data["seller_id"])
            )

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

    def generate_order_items(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate order items for given orders.

        Creates line items for each order with product assignments, pricing,
        and shipping information. Number of items per order follows distribution:
        - 1 item: 60%
        - 2-3 items: 30%
        - 4+ items: 10%

        Product selection is random from _product_data. Price and freight values
        have realistic variance around the product's average values.

        Args:
            orders_df (pd.DataFrame): Orders DataFrame with order_id column

        Returns:
            pd.DataFrame: Order items with columns: order_id, order_item_id,
                         product_id, seller_id, shipping_limit_date, price,
                         freight_value

        Example:
            >>> orders = generate_orders_for_date(datetime(2024, 1, 15))
            >>> items = generate_order_items(orders)
            >>> items.head()
        """
        # Initialize items list
        items = []

        for _, order in orders_df.iterrows():
            order_id = order["order_id"]
            purchase_timestamp = order["order_purchase_timestamp"]

            # Determine number of items for this order
            # 1 item: 60%, 2-3 items: 30%, 4+ items: 10%
            items_roll = self.rng.random()
            if items_roll < 0.60:
                num_items = 1
            elif items_roll < 0.90:
                num_items = self.rng.randint(2, 3)
            else:
                num_items = self.rng.randint(4, 8)

            # Generate items for this order
            for item_seq in range(1, num_items + 1):
                # Select random product
                product = self._product_data.sample(n=1, random_state=self.rng.randint(0, 2**32-1)).iloc[0]
                product_id = product["product_id"]
                seller_id = self._product_seller_map[product_id]

                # Calculate price with ±10% variance
                avg_price = product["avg_price"]
                price_variance = self.rng.uniform(-0.10, 0.10)
                price = avg_price * (1 + price_variance)

                # Calculate freight with ±20% variance
                avg_freight = product["avg_freight"]
                freight_variance = self.rng.uniform(-0.20, 0.20)
                freight_value = avg_freight * (1 + freight_variance)

                # Shipping limit: 7-14 days after purchase
                shipping_days = self.rng.uniform(7, 14)
                shipping_limit_date = purchase_timestamp + timedelta(days=shipping_days)

                items.append({
                    "order_id": order_id,
                    "order_item_id": item_seq,
                    "product_id": product_id,
                    "seller_id": seller_id,
                    "shipping_limit_date": shipping_limit_date,
                    "price": round(price, 2),
                    "freight_value": round(freight_value, 2),
                })

        return pd.DataFrame(items)

    def generate_order_payments(
        self, orders_df: pd.DataFrame, items_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate payment records for orders.

        Creates payment entries with realistic payment type distribution and
        installment plans. Payment value equals sum of (price + freight) for
        all items in the order.

        Payment type distribution:
        - credit_card: 74%
        - boleto: 19%
        - voucher: 5%
        - debit_card: 2%

        Installments: credit_card can have 1-12 installments (weighted toward lower),
        other payment types always have 1 installment.

        Args:
            orders_df (pd.DataFrame): Orders DataFrame
            items_df (pd.DataFrame): Order items DataFrame

        Returns:
            pd.DataFrame: Payments with columns: order_id, payment_sequential,
                         payment_type, payment_installments, payment_value

        Example:
            >>> orders = generate_orders_for_date(datetime(2024, 1, 15))
            >>> items = generate_order_items(orders)
            >>> payments = generate_order_payments(orders, items)
        """
        # Calculate order totals from items
        order_totals = items_df.groupby("order_id").apply(
            lambda x: (x["price"] + x["freight_value"]).sum()
        ).to_dict()

        payments = []

        for _, order in orders_df.iterrows():
            order_id = order["order_id"]
            payment_value = order_totals.get(order_id, 0.0)

            # Determine payment type
            payment_roll = self.rng.random()
            if payment_roll < 0.74:
                payment_type = "credit_card"
            elif payment_roll < 0.93:  # 0.74 + 0.19
                payment_type = "boleto"
            elif payment_roll < 0.98:  # 0.93 + 0.05
                payment_type = "voucher"
            else:
                payment_type = "debit_card"

            # Determine installments
            if payment_type == "credit_card":
                # Weighted toward lower installments
                # 1: 40%, 2: 20%, 3: 15%, 4-6: 15%, 7-12: 10%
                installment_roll = self.rng.random()
                if installment_roll < 0.40:
                    installments = 1
                elif installment_roll < 0.60:
                    installments = 2
                elif installment_roll < 0.75:
                    installments = 3
                elif installment_roll < 0.90:
                    installments = self.rng.randint(4, 6)
                else:
                    installments = self.rng.randint(7, 12)
            else:
                installments = 1

            payments.append({
                "order_id": order_id,
                "payment_sequential": 1,
                "payment_type": payment_type,
                "payment_installments": installments,
                "payment_value": round(payment_value, 2),
            })

        return pd.DataFrame(payments)

    def generate_order_reviews(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate review records for delivered orders.

        Creates reviews only for orders with status='delivered'. Review scores
        follow a realistic distribution skewed toward positive ratings.

        Score distribution:
        - 5: 57%
        - 4: 19%
        - 1: 12%
        - 3: 8%
        - 2: 4%

        Review attributes:
        - Title: Faker sentence or null (60% null)
        - Message: Faker paragraph or null (58% null)
        - Creation: 1-14 days after delivery
        - Answer: 0-7 days after creation (or null)
        - Review ID: syn_{MD5(seed_orderid_review)[:16]}

        Args:
            orders_df (pd.DataFrame): Orders DataFrame with order_status column

        Returns:
            pd.DataFrame: Reviews with columns: review_id, order_id, review_score,
                         review_comment_title, review_comment_message,
                         review_creation_date, review_answer_timestamp

        Example:
            >>> orders = generate_orders_for_date(datetime(2024, 1, 15))
            >>> reviews = generate_order_reviews(orders)
        """
        # Filter for delivered orders only
        delivered_orders = orders_df[orders_df["order_status"] == "delivered"].copy()

        reviews = []

        for _, order in delivered_orders.iterrows():
            order_id = order["order_id"]
            delivery_date = order["order_delivered_customer_date"]

            # Generate review score
            score_roll = self.rng.random()
            if score_roll < 0.57:
                score = 5
            elif score_roll < 0.76:  # 0.57 + 0.19
                score = 4
            elif score_roll < 0.88:  # 0.76 + 0.12
                score = 1
            elif score_roll < 0.96:  # 0.88 + 0.08
                score = 3
            else:
                score = 2

            # Generate review title (60% null)
            title = None
            if self.rng.random() > 0.60:
                title = self.faker.sentence()

            # Generate review message (58% null)
            message = None
            if self.rng.random() > 0.58:
                message = self.faker.paragraph()

            # Review creation: 1-14 days after delivery
            creation_days = self.rng.uniform(1, 14)
            creation_date = delivery_date + timedelta(days=creation_days)

            # Review answer: 0-7 days after creation (or null)
            answer_timestamp = None
            if self.rng.random() > 0.50:  # 50% chance of seller response
                answer_days = self.rng.uniform(0, 7)
                answer_timestamp = creation_date + timedelta(days=answer_days)

            # Generate deterministic review ID
            hash_input = f"{self.seed}_{order_id}_review"
            hash_digest = hashlib.md5(hash_input.encode()).hexdigest()[:16]
            review_id = f"syn_{hash_digest}"

            reviews.append({
                "review_id": review_id,
                "order_id": order_id,
                "review_score": score,
                "review_comment_title": title,
                "review_comment_message": message,
                "review_creation_date": creation_date,
                "review_answer_timestamp": answer_timestamp,
            })

        return pd.DataFrame(reviews)

    def generate_all_for_date(self, date: datetime) -> dict[str, pd.DataFrame]:
        """
        Generate all data (orders, items, payments, reviews) for a single date.

        This orchestrator method calls all generation methods in the correct order
        and returns a complete set of related data for the given date.

        Args:
            date (datetime): The date for which to generate data

        Returns:
            dict[str, pd.DataFrame]: Dictionary with keys:
                - "orders": Orders DataFrame
                - "order_items": Order items DataFrame
                - "order_payments": Order payments DataFrame
                - "order_reviews": Order reviews DataFrame

        Example:
            >>> gen = SyntheticDataGenerator(seed=42, config=CONFIG)
            >>> gen.load_reference_data()
            >>> gen.assign_customer_segments()
            >>> data = gen.generate_all_for_date(datetime(2024, 1, 15))
            >>> print(f"Generated {len(data['orders'])} orders")
        """
        # Generate orders
        orders_df = self.generate_orders_for_date(date)

        # Generate order items
        items_df = self.generate_order_items(orders_df)

        # Generate payments
        payments_df = self.generate_order_payments(orders_df, items_df)

        # Generate reviews
        reviews_df = self.generate_order_reviews(orders_df)

        return {
            "orders": orders_df,
            "order_items": items_df,
            "order_payments": payments_df,
            "order_reviews": reviews_df,
        }
