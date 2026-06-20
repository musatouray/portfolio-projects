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
