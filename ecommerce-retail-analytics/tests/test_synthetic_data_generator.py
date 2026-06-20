"""
Test suite for Synthetic Data Generator module.

This module tests the core customer segmentation logic using TDD approach.
Tests use mock customer lists rather than real Snowflake data.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from collections import Counter

from scripts.synthetic_data_generator import (
    SyntheticDataGenerator,
    CONFIG,
)


class TestConfig:
    """Test CONFIG dictionary structure and values."""

    def test_config_exists(self):
        """Verify CONFIG dictionary is defined."""
        assert CONFIG is not None

    def test_config_has_required_keys(self):
        """Verify CONFIG has all required keys."""
        required_keys = [
            "seed",
            "repeat_rate_target",
            "base_daily_orders",
            "max_daily_orders",
            "growth_end_date",
            "backfill_start_date",
            "customer_segments",
            "segment_max_orders",
            "segment_weights",
        ]
        for key in required_keys:
            assert key in CONFIG, f"Missing key: {key}"

    def test_config_segment_percentages_sum_to_one(self):
        """Verify customer segment percentages sum to 1.0."""
        segment_sum = sum(CONFIG["customer_segments"].values())
        assert abs(segment_sum - 1.0) < 0.001, f"Segment percentages sum to {segment_sum}, expected 1.0"

    def test_config_segment_consistency(self):
        """Verify all segments have corresponding max_orders and weights."""
        segments = set(CONFIG["customer_segments"].keys())
        max_order_segments = set(CONFIG["segment_max_orders"].keys())
        weight_segments = set(CONFIG["segment_weights"].keys())

        assert segments == max_order_segments, "Mismatch in segment_max_orders"
        assert segments == weight_segments, "Mismatch in segment_weights"


class TestSyntheticDataGenerator:
    """Test SyntheticDataGenerator class initialization and configuration."""

    def test_generator_initialization(self):
        """Verify generator can be instantiated with seed and config."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        assert gen is not None

    def test_generator_uses_seed(self):
        """Verify generator stores and uses the provided seed."""
        gen = SyntheticDataGenerator(seed=99, config=CONFIG)
        assert hasattr(gen, "seed") or hasattr(gen, "_seed")


class TestSegmentDistribution:
    """Test customer segment distribution matches CONFIG percentages."""

    @pytest.fixture
    def mock_customers(self):
        """Create a mock list of 1000 customer IDs."""
        return [f"CUST_{i:04d}" for i in range(1000)]

    @pytest.fixture
    def generator(self):
        """Create a SyntheticDataGenerator instance."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        return gen

    def test_segment_distribution_matches_config(self, generator, mock_customers):
        """
        Test Requirement 1: Assert 60/25/12/3 split with 2% tolerance.

        Given 1000 mock customers, verify that segment assignment produces:
        - one_time: 60% (600 ± 20)
        - occasional: 25% (250 ± 20)
        - loyal: 12% (120 ± 20)
        - champion: 3% (30 ± 20)
        """
        # Mock the load_reference_data to use mock customers
        generator.customer_ids = mock_customers

        # Assign segments
        customer_segments = generator.assign_customer_segments()

        # Count segment distribution
        segment_counts = Counter(customer_segments.values())

        # Expected counts with 2% tolerance (20 customers out of 1000)
        expected = {
            "one_time": 600,
            "occasional": 250,
            "loyal": 120,
            "champion": 30,
        }
        tolerance = 20  # 2% of 1000

        for segment, expected_count in expected.items():
            actual_count = segment_counts.get(segment, 0)
            assert abs(actual_count - expected_count) <= tolerance, (
                f"Segment '{segment}': expected {expected_count}±{tolerance}, "
                f"got {actual_count}"
            )

    def test_all_customers_assigned(self, generator, mock_customers):
        """Verify all customers are assigned to exactly one segment."""
        generator.customer_ids = mock_customers
        customer_segments = generator.assign_customer_segments()

        assert len(customer_segments) == len(mock_customers), (
            f"Expected {len(mock_customers)} assignments, "
            f"got {len(customer_segments)}"
        )


class TestDeterministicSegmentation:
    """Test that same seed produces same segment assignments."""

    @pytest.fixture
    def mock_customers(self):
        """Create a smaller mock list for determinism testing."""
        return [f"CUST_{i:03d}" for i in range(100)]

    def test_deterministic_segmentation(self, mock_customers):
        """
        Test Requirement 2: Same seed produces same segments.

        Run segmentation twice with same seed and verify identical results.
        """
        # First run
        gen1 = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen1.customer_ids = mock_customers
        segments1 = gen1.assign_customer_segments()

        # Second run with same seed
        gen2 = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen2.customer_ids = mock_customers
        segments2 = gen2.assign_customer_segments()

        # Verify identical assignments
        assert segments1 == segments2, "Same seed should produce identical segment assignments"

    def test_different_seed_produces_different_segments(self, mock_customers):
        """Verify different seeds produce different (but valid) distributions."""
        gen1 = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen1.customer_ids = mock_customers
        segments1 = gen1.assign_customer_segments()

        gen2 = SyntheticDataGenerator(seed=99, config=CONFIG)
        gen2.customer_ids = mock_customers
        segments2 = gen2.assign_customer_segments()

        # Should have some differences
        differences = sum(1 for cust_id in mock_customers if segments1[cust_id] != segments2[cust_id])
        assert differences > 0, "Different seeds should produce different assignments"


class TestCustomerSelection:
    """Test customer selection respects segment weights and order limits."""

    @pytest.fixture
    def generator_with_segments(self):
        """Create generator with pre-assigned segments."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Create small set of customers with known segments
        gen.customer_ids = [
            "CHAMPION_1", "CHAMPION_2",  # 2 champions
            "LOYAL_1", "LOYAL_2", "LOYAL_3",  # 3 loyal
            "OCCASIONAL_1", "OCCASIONAL_2", "OCCASIONAL_3", "OCCASIONAL_4",  # 4 occasional
            "ONETIME_1", "ONETIME_2", "ONETIME_3",  # 3 one-time
        ]

        # Manually assign segments for testing
        gen.customer_segments = {
            "CHAMPION_1": "champion",
            "CHAMPION_2": "champion",
            "LOYAL_1": "loyal",
            "LOYAL_2": "loyal",
            "LOYAL_3": "loyal",
            "OCCASIONAL_1": "occasional",
            "OCCASIONAL_2": "occasional",
            "OCCASIONAL_3": "occasional",
            "OCCASIONAL_4": "occasional",
            "ONETIME_1": "one_time",
            "ONETIME_2": "one_time",
            "ONETIME_3": "one_time",
        }

        # Initialize order counts
        gen.customer_order_counts = {cust_id: 0 for cust_id in gen.customer_ids}

        return gen

    def test_customer_selection_respects_segments(self, generator_with_segments):
        """
        Test Requirement 3: Champions selected more often than one-time customers.

        Simulate 100 order selections and verify champions are selected
        more frequently than one-time customers (due to higher weights).
        """
        gen = generator_with_segments
        test_date = datetime(2024, 1, 1)

        # Track selections
        selections = []
        for _ in range(100):
            selected = gen._select_customer(date=test_date)
            if selected:
                selections.append(selected)
                gen.customer_order_counts[selected] += 1

        # Count selections by segment
        champion_selections = sum(1 for s in selections if "CHAMPION" in s)
        onetime_selections = sum(1 for s in selections if "ONETIME" in s)

        # Champions should be selected more than one-time customers
        # (weight 10.0 vs 0.0, so one-time should get 0 selections after first order)
        assert champion_selections > onetime_selections, (
            f"Champions selected {champion_selections} times, "
            f"one-time selected {onetime_selections} times. "
            f"Champions should be selected more often."
        )

    def test_customer_selection_respects_max_orders(self, generator_with_segments):
        """Verify customers are not selected beyond their segment's max orders."""
        gen = generator_with_segments
        test_date = datetime(2024, 1, 1)

        # Force select one-time customer until exhausted
        onetime_customer = "ONETIME_1"

        # One-time customers have max 1 order
        for _ in range(5):  # Try to select 5 times
            selected = gen._select_customer(date=test_date)
            if selected == onetime_customer:
                gen.customer_order_counts[onetime_customer] += 1

        # Verify one-time customer has at most 1 order
        max_orders_onetime = CONFIG["segment_max_orders"]["one_time"]
        actual_orders = gen.customer_order_counts[onetime_customer]

        assert actual_orders <= max_orders_onetime, (
            f"One-time customer has {actual_orders} orders, "
            f"max allowed is {max_orders_onetime}"
        )


class TestLoadReferenceData:
    """Test loading reference data from Snowflake."""

    @patch('scripts.synthetic_data_generator.snowflake.connector.connect')
    def test_load_reference_data_connects_to_snowflake(self, mock_connect):
        """Verify load_reference_data attempts to connect to Snowflake."""
        # Mock connection and cursor
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("CUST_001",), ("CUST_002",)]
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen.load_reference_data()

        # Verify connection was attempted
        mock_connect.assert_called_once()

    @patch('scripts.synthetic_data_generator.snowflake.connector.connect')
    def test_load_reference_data_populates_customer_ids(self, mock_connect):
        """Verify customer_ids are populated from Snowflake query."""
        # Mock connection and cursor
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("CUST_001",),
            ("CUST_002",),
            ("CUST_003",),
        ]
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen.load_reference_data()

        # Verify customer_ids are set
        assert hasattr(gen, "customer_ids")
        assert len(gen.customer_ids) == 3
        assert "CUST_001" in gen.customer_ids


class TestOrderGeneration:
    """Test order generation methods for daily orders, order IDs, and order dataframes."""

    def test_daily_order_volume_growth(self):
        """
        Test Requirement 1: Verify 135→500 growth curve.

        Tests the calculate_daily_orders method across key dates:
        - Oct 2018: ~135 orders/day
        - Jun 2023: ~380 orders/day
        - Jun 2026: ~500 orders/day
        """
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Test start date (Oct 2018)
        start_date = datetime(2018, 10, 18)
        start_orders = gen.calculate_daily_orders(start_date)
        assert 130 <= start_orders <= 140, f"Expected ~135 orders at start, got {start_orders}"

        # Test mid date (Jun 2023)
        mid_date = datetime(2023, 6, 19)
        mid_orders = gen.calculate_daily_orders(mid_date)
        assert 350 <= mid_orders <= 390, f"Expected ~360 orders at mid point, got {mid_orders}"

        # Test end date (Jun 2026)
        end_date = datetime(2026, 6, 19)
        end_orders = gen.calculate_daily_orders(end_date)
        assert 495 <= end_orders <= 505, f"Expected ~500 orders at end, got {end_orders}"

    def test_order_id_format(self):
        """
        Test Requirement 2: Verify syn_YYYYMMDD_NNNNNN_HHHHHHHH format.

        Order ID should be exactly 28 characters with correct structure.
        """
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        test_date = datetime(2024, 1, 15)
        sequence = 42

        order_id = gen.generate_order_id(test_date, sequence)

        # Check total length (syn_YYYYMMDD_NNNNNN_HHHHHHHH = 4+8+7+9 = 28)
        assert len(order_id) == 28, f"Expected length 28, got {len(order_id)}"

        # Check format structure
        parts = order_id.split("_")
        assert len(parts) == 4, f"Expected 4 parts separated by underscores, got {len(parts)}"
        assert parts[0] == "syn", f"Expected prefix 'syn', got '{parts[0]}'"
        assert parts[1] == "20240115", f"Expected date '20240115', got '{parts[1]}'"
        assert parts[2] == "000042", f"Expected sequence '000042', got '{parts[2]}'"
        assert len(parts[3]) == 8, f"Expected 8-char hash, got {len(parts[3])}"

        # Verify sequence is zero-padded to 6 digits
        assert parts[2].isdigit(), "Sequence should be numeric"

    def test_order_id_deterministic(self):
        """
        Test Requirement 3: Same inputs = same ID.

        Multiple calls with same date and sequence should produce identical order IDs.
        """
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        test_date = datetime(2024, 1, 15)
        sequence = 123

        # Generate same order ID twice
        order_id_1 = gen.generate_order_id(test_date, sequence)
        order_id_2 = gen.generate_order_id(test_date, sequence)

        assert order_id_1 == order_id_2, "Same inputs should produce same order ID"

        # Generate with different sequence - should be different
        order_id_3 = gen.generate_order_id(test_date, 124)
        assert order_id_1 != order_id_3, "Different sequence should produce different order ID"

    def test_generate_orders_returns_dataframe(self):
        """
        Test Requirement 4: Correct columns, non-empty.

        generate_orders_for_date should return a DataFrame with all required columns.
        """
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Setup minimal customer data
        gen.customer_ids = [f"CUST_{i:04d}" for i in range(100)]
        gen.assign_customer_segments()

        test_date = datetime(2024, 1, 15)
        orders_df = gen.generate_orders_for_date(test_date)

        # Check it's a DataFrame
        import pandas as pd
        assert isinstance(orders_df, pd.DataFrame), "Should return a pandas DataFrame"

        # Check non-empty
        assert len(orders_df) > 0, "Should generate at least some orders"

        # Check required columns
        required_columns = [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
        for col in required_columns:
            assert col in orders_df.columns, f"Missing required column: {col}"

    def test_order_status_distribution(self):
        """
        Test Requirement 5: ~97% delivered.

        Status distribution should match:
        - delivered: 97%
        - shipped: 1%
        - canceled: 1%
        - unavailable: 0.5%
        - processing: 0.5%
        """
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Setup minimal customer data
        gen.customer_ids = [f"CUST_{i:04d}" for i in range(500)]
        gen.assign_customer_segments()

        # Generate orders for a date with expected ~380 orders
        test_date = datetime(2023, 6, 19)
        orders_df = gen.generate_orders_for_date(test_date)

        # Count status distribution
        status_counts = orders_df["order_status"].value_counts(normalize=True)

        # Check delivered is ~97% (allow 5% tolerance due to randomness)
        delivered_pct = status_counts.get("delivered", 0)
        assert 0.92 <= delivered_pct <= 1.0, f"Expected ~97% delivered, got {delivered_pct:.1%}"

        # Check that delivered is the most common status
        assert status_counts.idxmax() == "delivered", "Delivered should be the most common status"

        # Check that we have at least some variety in statuses (not all the same)
        assert len(status_counts) >= 2, "Should have at least 2 different statuses"


class TestOrderItemsGeneration:
    """Test order items generation with product and seller assignment."""

    @pytest.fixture
    def generator_with_product_data(self):
        """Create generator with mock product data."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Mock _product_data DataFrame
        import pandas as pd
        gen._product_data = pd.DataFrame({
            "product_id": ["PROD_001", "PROD_002", "PROD_003", "PROD_004", "PROD_005"],
            "seller_id": ["SELLER_A", "SELLER_B", "SELLER_A", "SELLER_C", "SELLER_B"],
            "avg_price": [100.0, 200.0, 50.0, 150.0, 75.0],
            "avg_freight": [10.0, 20.0, 5.0, 15.0, 8.0],
        })

        # Mock _product_seller_map
        gen._product_seller_map = {
            "PROD_001": "SELLER_A",
            "PROD_002": "SELLER_B",
            "PROD_003": "SELLER_A",
            "PROD_004": "SELLER_C",
            "PROD_005": "SELLER_B",
        }

        return gen

    @pytest.fixture
    def sample_orders(self):
        """Create sample orders DataFrame for testing."""
        import pandas as pd
        from datetime import datetime

        return pd.DataFrame({
            "order_id": ["ORDER_001", "ORDER_002", "ORDER_003", "ORDER_004"],
            "customer_id": ["CUST_001", "CUST_002", "CUST_003", "CUST_004"],
            "order_status": ["delivered", "delivered", "shipped", "delivered"],
            "order_purchase_timestamp": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 11, 0, 0),
                datetime(2024, 1, 1, 12, 0, 0),
                datetime(2024, 1, 1, 13, 0, 0),
            ],
            "order_approved_at": [
                datetime(2024, 1, 1, 11, 0, 0),
                datetime(2024, 1, 1, 12, 0, 0),
                datetime(2024, 1, 1, 13, 0, 0),
                datetime(2024, 1, 1, 14, 0, 0),
            ],
            "order_delivered_carrier_date": [
                datetime(2024, 1, 3, 10, 0, 0),
                datetime(2024, 1, 3, 11, 0, 0),
                datetime(2024, 1, 3, 12, 0, 0),
                datetime(2024, 1, 3, 13, 0, 0),
            ],
            "order_delivered_customer_date": [
                datetime(2024, 1, 10, 10, 0, 0),
                datetime(2024, 1, 10, 11, 0, 0),
                None,
                datetime(2024, 1, 10, 13, 0, 0),
            ],
            "order_estimated_delivery_date": [
                datetime(2024, 1, 12, 10, 0, 0),
                datetime(2024, 1, 12, 11, 0, 0),
                datetime(2024, 1, 12, 12, 0, 0),
                datetime(2024, 1, 12, 13, 0, 0),
            ],
        })

    def test_items_per_order_distribution(self, generator_with_product_data, sample_orders):
        """
        Test Requirement 1: Verify 60/30/10 split for items per order.

        - 1 item: 60%
        - 2-3 items: 30%
        - 4+ items: 10%
        """
        gen = generator_with_product_data

        # Generate items for many orders to test distribution
        large_orders = sample_orders.copy()
        for i in range(100):
            large_orders = pd.concat([large_orders, sample_orders.copy()], ignore_index=True)

        # Reset order IDs to be unique
        large_orders["order_id"] = [f"ORDER_{i:05d}" for i in range(len(large_orders))]

        items_df = gen.generate_order_items(large_orders)

        # Count items per order
        items_per_order = items_df.groupby("order_id").size()

        # Calculate distribution
        one_item_pct = (items_per_order == 1).sum() / len(items_per_order)
        two_three_items_pct = ((items_per_order >= 2) & (items_per_order <= 3)).sum() / len(items_per_order)
        four_plus_items_pct = (items_per_order >= 4).sum() / len(items_per_order)

        # Allow 10% tolerance due to randomness
        assert 0.50 <= one_item_pct <= 0.70, f"Expected ~60% with 1 item, got {one_item_pct:.1%}"
        assert 0.20 <= two_three_items_pct <= 0.40, f"Expected ~30% with 2-3 items, got {two_three_items_pct:.1%}"
        assert 0.05 <= four_plus_items_pct <= 0.15, f"Expected ~10% with 4+ items, got {four_plus_items_pct:.1%}"

    def test_items_have_required_columns(self, generator_with_product_data, sample_orders):
        """
        Test Requirement 2: All 7 columns present.

        Columns: order_id, order_item_id, product_id, seller_id,
                 shipping_limit_date, price, freight_value
        """
        gen = generator_with_product_data
        items_df = gen.generate_order_items(sample_orders)

        required_columns = [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ]

        for col in required_columns:
            assert col in items_df.columns, f"Missing required column: {col}"

        # Check non-empty
        assert len(items_df) > 0, "Should generate at least some order items"

    def test_item_price_variance(self, generator_with_product_data, sample_orders):
        """Verify price is product's avg_price ± 10% variance."""
        gen = generator_with_product_data
        items_df = gen.generate_order_items(sample_orders)

        # Check each item's price is within 10% of the product's avg_price
        for _, item in items_df.iterrows():
            product_id = item["product_id"]
            product_avg_price = gen._product_data[
                gen._product_data["product_id"] == product_id
            ]["avg_price"].values[0]

            price = item["price"]
            lower_bound = product_avg_price * 0.9
            upper_bound = product_avg_price * 1.1

            assert lower_bound <= price <= upper_bound, (
                f"Price {price} for {product_id} not within ±10% of avg {product_avg_price}"
            )

    def test_item_seller_mapping(self, generator_with_product_data, sample_orders):
        """Verify seller matches product's seller from _product_seller_map."""
        gen = generator_with_product_data
        items_df = gen.generate_order_items(sample_orders)

        for _, item in items_df.iterrows():
            product_id = item["product_id"]
            seller_id = item["seller_id"]
            expected_seller = gen._product_seller_map[product_id]

            assert seller_id == expected_seller, (
                f"Product {product_id} should have seller {expected_seller}, got {seller_id}"
            )


class TestOrderPaymentsGeneration:
    """Test order payments generation with correct totals and types."""

    @pytest.fixture
    def generator_with_product_data(self):
        """Create generator with mock product data."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        import pandas as pd
        gen._product_data = pd.DataFrame({
            "product_id": ["PROD_001", "PROD_002", "PROD_003"],
            "seller_id": ["SELLER_A", "SELLER_B", "SELLER_A"],
            "avg_price": [100.0, 200.0, 50.0],
            "avg_freight": [10.0, 20.0, 5.0],
        })

        gen._product_seller_map = {
            "PROD_001": "SELLER_A",
            "PROD_002": "SELLER_B",
            "PROD_003": "SELLER_A",
        }

        return gen

    @pytest.fixture
    def sample_orders_and_items(self, generator_with_product_data):
        """Create sample orders and items for payment testing."""
        import pandas as pd
        from datetime import datetime

        orders_df = pd.DataFrame({
            "order_id": ["ORDER_001", "ORDER_002"],
            "customer_id": ["CUST_001", "CUST_002"],
            "order_status": ["delivered", "delivered"],
            "order_purchase_timestamp": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 11, 0, 0),
            ],
            "order_approved_at": [
                datetime(2024, 1, 1, 11, 0, 0),
                datetime(2024, 1, 1, 12, 0, 0),
            ],
            "order_delivered_carrier_date": [
                datetime(2024, 1, 3, 10, 0, 0),
                datetime(2024, 1, 3, 11, 0, 0),
            ],
            "order_delivered_customer_date": [
                datetime(2024, 1, 10, 10, 0, 0),
                datetime(2024, 1, 10, 11, 0, 0),
            ],
            "order_estimated_delivery_date": [
                datetime(2024, 1, 12, 10, 0, 0),
                datetime(2024, 1, 12, 11, 0, 0),
            ],
        })

        items_df = pd.DataFrame({
            "order_id": ["ORDER_001", "ORDER_001", "ORDER_002"],
            "order_item_id": [1, 2, 1],
            "product_id": ["PROD_001", "PROD_002", "PROD_003"],
            "seller_id": ["SELLER_A", "SELLER_B", "SELLER_A"],
            "price": [100.0, 200.0, 50.0],
            "freight_value": [10.0, 20.0, 5.0],
            "shipping_limit_date": [
                datetime(2024, 1, 10),
                datetime(2024, 1, 10),
                datetime(2024, 1, 10),
            ],
        })

        return orders_df, items_df

    def test_payment_type_distribution(self, generator_with_product_data):
        """
        Test Requirement 3: Verify 74/19/5/2 split for payment types.

        - credit_card: 74%
        - boleto: 19%
        - voucher: 5%
        - debit_card: 2%
        """
        gen = generator_with_product_data

        # Create many orders to test distribution
        import pandas as pd
        from datetime import datetime

        orders_df = pd.DataFrame({
            "order_id": [f"ORDER_{i:05d}" for i in range(1000)],
            "customer_id": [f"CUST_{i:05d}" for i in range(1000)],
            "order_status": ["delivered"] * 1000,
            "order_purchase_timestamp": [datetime(2024, 1, 1, 10, 0, 0)] * 1000,
            "order_approved_at": [datetime(2024, 1, 1, 11, 0, 0)] * 1000,
            "order_delivered_carrier_date": [datetime(2024, 1, 3, 10, 0, 0)] * 1000,
            "order_delivered_customer_date": [datetime(2024, 1, 10, 10, 0, 0)] * 1000,
            "order_estimated_delivery_date": [datetime(2024, 1, 12, 10, 0, 0)] * 1000,
        })

        items_df = pd.DataFrame({
            "order_id": [f"ORDER_{i:05d}" for i in range(1000)],
            "order_item_id": [1] * 1000,
            "product_id": ["PROD_001"] * 1000,
            "seller_id": ["SELLER_A"] * 1000,
            "price": [100.0] * 1000,
            "freight_value": [10.0] * 1000,
            "shipping_limit_date": [datetime(2024, 1, 10)] * 1000,
        })

        payments_df = gen.generate_order_payments(orders_df, items_df)

        # Count payment type distribution
        payment_counts = payments_df["payment_type"].value_counts(normalize=True)

        # Allow 5% tolerance
        credit_card_pct = payment_counts.get("credit_card", 0)
        boleto_pct = payment_counts.get("boleto", 0)
        voucher_pct = payment_counts.get("voucher", 0)
        debit_card_pct = payment_counts.get("debit_card", 0)

        assert 0.69 <= credit_card_pct <= 0.79, f"Expected ~74% credit_card, got {credit_card_pct:.1%}"
        assert 0.14 <= boleto_pct <= 0.24, f"Expected ~19% boleto, got {boleto_pct:.1%}"
        assert 0.02 <= voucher_pct <= 0.08, f"Expected ~5% voucher, got {voucher_pct:.1%}"
        assert 0.00 <= debit_card_pct <= 0.05, f"Expected ~2% debit_card, got {debit_card_pct:.1%}"

    def test_payment_value_matches_items(self, generator_with_product_data, sample_orders_and_items):
        """
        Test Requirement 4: Payment value = sum of (price + freight) for all items.
        """
        gen = generator_with_product_data
        orders_df, items_df = sample_orders_and_items

        payments_df = gen.generate_order_payments(orders_df, items_df)

        # Calculate expected totals
        expected_totals = items_df.groupby("order_id").apply(
            lambda x: (x["price"] + x["freight_value"]).sum()
        )

        # Check each order's payment value
        for order_id in orders_df["order_id"]:
            expected_value = expected_totals[order_id]
            actual_value = payments_df[payments_df["order_id"] == order_id]["payment_value"].sum()

            assert abs(actual_value - expected_value) < 0.01, (
                f"Order {order_id}: expected payment value {expected_value}, got {actual_value}"
            )

    def test_payments_have_required_columns(self, generator_with_product_data, sample_orders_and_items):
        """Verify all required payment columns are present."""
        gen = generator_with_product_data
        orders_df, items_df = sample_orders_and_items

        payments_df = gen.generate_order_payments(orders_df, items_df)

        required_columns = [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ]

        for col in required_columns:
            assert col in payments_df.columns, f"Missing required column: {col}"


class TestOrderReviewsGeneration:
    """Test order reviews generation for delivered orders."""

    @pytest.fixture
    def sample_delivered_orders(self):
        """Create sample delivered orders for review testing."""
        import pandas as pd
        from datetime import datetime

        return pd.DataFrame({
            "order_id": ["ORDER_001", "ORDER_002", "ORDER_003", "ORDER_004"],
            "customer_id": ["CUST_001", "CUST_002", "CUST_003", "CUST_004"],
            "order_status": ["delivered", "delivered", "shipped", "delivered"],
            "order_purchase_timestamp": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 11, 0, 0),
                datetime(2024, 1, 1, 12, 0, 0),
                datetime(2024, 1, 1, 13, 0, 0),
            ],
            "order_approved_at": [
                datetime(2024, 1, 1, 11, 0, 0),
                datetime(2024, 1, 1, 12, 0, 0),
                datetime(2024, 1, 1, 13, 0, 0),
                datetime(2024, 1, 1, 14, 0, 0),
            ],
            "order_delivered_carrier_date": [
                datetime(2024, 1, 3, 10, 0, 0),
                datetime(2024, 1, 3, 11, 0, 0),
                datetime(2024, 1, 3, 12, 0, 0),
                datetime(2024, 1, 3, 13, 0, 0),
            ],
            "order_delivered_customer_date": [
                datetime(2024, 1, 10, 10, 0, 0),
                datetime(2024, 1, 10, 11, 0, 0),
                None,  # Shipped, not delivered
                datetime(2024, 1, 10, 13, 0, 0),
            ],
            "order_estimated_delivery_date": [
                datetime(2024, 1, 12, 10, 0, 0),
                datetime(2024, 1, 12, 11, 0, 0),
                datetime(2024, 1, 12, 12, 0, 0),
                datetime(2024, 1, 12, 13, 0, 0),
            ],
        })

    def test_reviews_only_for_delivered_orders(self, sample_delivered_orders):
        """Verify reviews are only generated for delivered orders."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        reviews_df = gen.generate_order_reviews(sample_delivered_orders)

        # Should only have 3 reviews (ORDER_001, ORDER_002, ORDER_004)
        # ORDER_003 is shipped, not delivered
        assert len(reviews_df) == 3, f"Expected 3 reviews for delivered orders, got {len(reviews_df)}"

        # Check that only delivered orders have reviews
        reviewed_orders = set(reviews_df["order_id"])
        delivered_orders = set(
            sample_delivered_orders[
                sample_delivered_orders["order_status"] == "delivered"
            ]["order_id"]
        )

        assert reviewed_orders == delivered_orders, "Reviews should only be for delivered orders"

    def test_review_score_distribution(self):
        """
        Test Requirement 5: Verify 57/19/12/8/4 split for review scores.

        - 5: 57%
        - 4: 19%
        - 1: 12%
        - 3: 8%
        - 2: 4%
        """
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Create many delivered orders
        import pandas as pd
        from datetime import datetime

        orders_df = pd.DataFrame({
            "order_id": [f"ORDER_{i:05d}" for i in range(1000)],
            "customer_id": [f"CUST_{i:05d}" for i in range(1000)],
            "order_status": ["delivered"] * 1000,
            "order_purchase_timestamp": [datetime(2024, 1, 1, 10, 0, 0)] * 1000,
            "order_approved_at": [datetime(2024, 1, 1, 11, 0, 0)] * 1000,
            "order_delivered_carrier_date": [datetime(2024, 1, 3, 10, 0, 0)] * 1000,
            "order_delivered_customer_date": [datetime(2024, 1, 10, 10, 0, 0)] * 1000,
            "order_estimated_delivery_date": [datetime(2024, 1, 12, 10, 0, 0)] * 1000,
        })

        reviews_df = gen.generate_order_reviews(orders_df)

        # Count score distribution
        score_counts = reviews_df["review_score"].value_counts(normalize=True)

        # Allow 5% tolerance
        score_5_pct = score_counts.get(5, 0)
        score_4_pct = score_counts.get(4, 0)
        score_1_pct = score_counts.get(1, 0)
        score_3_pct = score_counts.get(3, 0)
        score_2_pct = score_counts.get(2, 0)

        assert 0.52 <= score_5_pct <= 0.62, f"Expected ~57% score 5, got {score_5_pct:.1%}"
        assert 0.14 <= score_4_pct <= 0.24, f"Expected ~19% score 4, got {score_4_pct:.1%}"
        assert 0.07 <= score_1_pct <= 0.17, f"Expected ~12% score 1, got {score_1_pct:.1%}"
        assert 0.03 <= score_3_pct <= 0.13, f"Expected ~8% score 3, got {score_3_pct:.1%}"
        assert 0.00 <= score_2_pct <= 0.09, f"Expected ~4% score 2, got {score_2_pct:.1%}"

    def test_reviews_have_required_columns(self, sample_delivered_orders):
        """
        Test Requirement 6: All 7 columns present.

        Columns: review_id, order_id, review_score, review_comment_title,
                 review_comment_message, review_creation_date, review_answer_timestamp
        """
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        reviews_df = gen.generate_order_reviews(sample_delivered_orders)

        required_columns = [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ]

        for col in required_columns:
            assert col in reviews_df.columns, f"Missing required column: {col}"

    def test_review_id_format(self, sample_delivered_orders):
        """Verify review ID format: syn_{MD5(seed_orderid_review)[:16]}."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        reviews_df = gen.generate_order_reviews(sample_delivered_orders)

        for _, review in reviews_df.iterrows():
            review_id = review["review_id"]

            # Check format
            assert review_id.startswith("syn_"), f"Review ID should start with 'syn_', got {review_id}"

            # Check length (syn_ + 16 chars = 20)
            assert len(review_id) == 20, f"Review ID should be 20 chars, got {len(review_id)}"

            # Check hash part is hex
            hash_part = review_id[4:]
            assert all(c in "0123456789abcdef" for c in hash_part), (
                f"Hash part should be hex, got {hash_part}"
            )


class TestGenerateAllForDate:
    """Test the generate_all_for_date orchestrator method."""

    @pytest.fixture
    def generator_with_full_setup(self):
        """Create generator with all required mock data."""
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Mock customer data
        gen.customer_ids = [f"CUST_{i:04d}" for i in range(100)]
        gen.assign_customer_segments()

        # Mock product data
        import pandas as pd
        gen._product_data = pd.DataFrame({
            "product_id": [f"PROD_{i:03d}" for i in range(10)],
            "seller_id": [f"SELLER_{i % 3}" for i in range(10)],
            "avg_price": [100.0 + i * 10 for i in range(10)],
            "avg_freight": [10.0 + i for i in range(10)],
        })

        gen._product_seller_map = {
            f"PROD_{i:03d}": f"SELLER_{i % 3}" for i in range(10)
        }

        return gen

    def test_generate_all_returns_four_dataframes(self, generator_with_full_setup):
        """
        Test Requirement 7: Returns all 4 keys.

        Should return dict with keys: orders, order_items, order_payments, order_reviews
        """
        gen = generator_with_full_setup
        test_date = datetime(2024, 1, 15)

        result = gen.generate_all_for_date(test_date)

        # Check it's a dict
        assert isinstance(result, dict), "Should return a dictionary"

        # Check all 4 keys exist
        expected_keys = ["orders", "order_items", "order_payments", "order_reviews"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

        # Check all values are DataFrames
        import pandas as pd
        for key, value in result.items():
            assert isinstance(value, pd.DataFrame), f"{key} should be a DataFrame"

    def test_referential_integrity(self, generator_with_full_setup):
        """
        Test Requirement 8: All item/payment order_ids exist in orders.
        """
        gen = generator_with_full_setup
        test_date = datetime(2024, 1, 15)

        result = gen.generate_all_for_date(test_date)

        orders_df = result["orders"]
        items_df = result["order_items"]
        payments_df = result["order_payments"]
        reviews_df = result["order_reviews"]

        # Get set of order IDs
        order_ids = set(orders_df["order_id"])

        # Check all item order_ids exist in orders
        item_order_ids = set(items_df["order_id"])
        assert item_order_ids.issubset(order_ids), "All item order_ids should exist in orders"

        # Check all payment order_ids exist in orders
        payment_order_ids = set(payments_df["order_id"])
        assert payment_order_ids.issubset(order_ids), "All payment order_ids should exist in orders"

        # Check all review order_ids exist in orders
        review_order_ids = set(reviews_df["order_id"])
        assert review_order_ids.issubset(order_ids), "All review order_ids should exist in orders"
