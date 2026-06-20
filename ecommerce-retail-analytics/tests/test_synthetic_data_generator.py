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
