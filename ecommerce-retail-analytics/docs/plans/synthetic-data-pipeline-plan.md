# Synthetic Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an Airflow-orchestrated pipeline that generates synthetic order data (Oct 2018 → Jun 2026) with 30-40% repeat purchases, uploads to S3, and loads into Snowflake.

**Architecture:** Local Airflow (Docker Compose) runs two DAGs—backfill (manual, ~700K orders) and daily (scheduled, ~500 orders/day). Both use a shared Python generator module that creates deterministic synthetic data respecting existing customer/product/seller relationships.

**Tech Stack:** Python 3.12, Apache Airflow 2.9, Faker, boto3, snowflake-connector-python, Docker Compose

## Global Constraints

- Python 3.12 (matches pyproject.toml `requires-python = "==3.12.*"`)
- Seed = 42 for reproducibility
- Repeat rate target = 35% (within 30-40% spec range)
- Order ID format: `syn_{YYYYMMDD}_{sequence:06d}_{hash:8}`
- S3 bucket: `ecommerce-retail-analytics-raw`
- Snowflake stage: `raw_ecommerce_s3_stage`
- All synthetic orders reference existing customer_ids, product_ids, seller_ids only

---

## File Structure

```
ecommerce-retail-analytics/
├── airflow/
│   ├── docker-compose.yml           # Task 1
│   ├── Dockerfile                    # Task 1
│   ├── requirements.txt              # Task 1
│   ├── dags/
│   │   ├── backfill_synthetic_orders.py   # Task 5
│   │   └── daily_synthetic_orders.py      # Task 6
│   └── plugins/
│       └── .gitkeep                  # Task 1
│
├── scripts/
│   └── synthetic_data_generator.py   # Tasks 2, 3, 4
│
├── tests/
│   └── test_synthetic_data_generator.py  # Tasks 2, 3, 4
│
└── data/
    └── synthetic/
        └── .gitkeep                  # Task 1
```

---

### Task 1: Airflow Local Setup with Docker Compose

**Files:**
- Create: `airflow/docker-compose.yml`
- Create: `airflow/Dockerfile`
- Create: `airflow/requirements.txt`
- Create: `airflow/plugins/.gitkeep`
- Create: `airflow/config/.gitkeep`
- Create: `data/synthetic/.gitkeep`

**Interfaces:**
- Consumes: None
- Produces: Working local Airflow environment accessible at `http://localhost:8080`

- [ ] **Step 1: Create airflow directory structure**

```bash
cd ecommerce-retail-analytics
mkdir -p airflow/dags airflow/plugins airflow/config airflow/logs data/synthetic
touch airflow/plugins/.gitkeep airflow/config/.gitkeep data/synthetic/.gitkeep
```

- [ ] **Step 2: Create requirements.txt**

Create `airflow/requirements.txt`:

```text
apache-airflow==2.9.3
apache-airflow-providers-snowflake==5.6.0
apache-airflow-providers-amazon==8.22.0
faker==25.0.0
boto3==1.34.0
pandas==2.2.0
snowflake-connector-python[pandas]==3.10.0
python-dotenv==1.0.0
cryptography==42.0.0
```

- [ ] **Step 3: Create Dockerfile**

Create `airflow/Dockerfile`:

```dockerfile
FROM apache/airflow:2.9.3-python3.12

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy scripts module for import
COPY --chown=airflow:root ../scripts /opt/airflow/scripts
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"
```

- [ ] **Step 4: Create docker-compose.yml**

Create `airflow/docker-compose.yml`:

```yaml
version: '3.8'

x-airflow-common: &airflow-common
  build:
    context: .
    dockerfile: Dockerfile
  environment: &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth'
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG: 'true'
    # AWS credentials (loaded from .env)
    AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
    AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    AWS_REGION: ${AWS_REGION:-us-east-1}
    S3_BUCKET: ${S3_BUCKET:-ecommerce-retail-analytics-raw}
    # Snowflake credentials
    SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT}
    SNOWFLAKE_USER: ${SNOWFLAKE_USER}
    SNOWFLAKE_WAREHOUSE: ${SNOWFLAKE_WAREHOUSE}
    SNOWFLAKE_DATABASE: ${SNOWFLAKE_DATABASE}
    SNOWFLAKE_SCHEMA: ${SNOWFLAKE_SCHEMA:-RAW}
    SNOWFLAKE_ROLE: ${SNOWFLAKE_ROLE}
    SNOWFLAKE_PRIVATE_KEY_PASSPHRASE: ${SNOWFLAKE_PRIVATE_KEY_PASSPHRASE}
  volumes:
    - ./dags:/opt/airflow/dags
    - ./plugins:/opt/airflow/plugins
    - ./config:/opt/airflow/config
    - ./logs:/opt/airflow/logs
    - ../scripts:/opt/airflow/scripts:ro
    - ../data/synthetic:/opt/airflow/data/synthetic
    - ~/.snowflake:/home/airflow/.snowflake:ro
    - ../.env:/opt/airflow/.env:ro
  depends_on:
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        airflow db init
        airflow users create \
          --username admin \
          --firstname Admin \
          --lastname User \
          --role Admin \
          --email admin@example.com \
          --password admin
    depends_on:
      postgres:
        condition: service_healthy

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD-SHELL", "airflow jobs check --job-type SchedulerJob --hostname $(hostname)"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      airflow-init:
        condition: service_completed_successfully

volumes:
  postgres-db-volume:
```

- [ ] **Step 5: Add .gitignore entries**

Append to `airflow/.gitignore` (create if not exists):

```gitignore
logs/
*.pyc
__pycache__/
```

- [ ] **Step 6: Verify Airflow starts**

```bash
cd ecommerce-retail-analytics/airflow
docker compose up -d
# Wait 30-60 seconds for initialization
docker compose ps
# Expected: postgres, airflow-webserver, airflow-scheduler all "Up"
# Access http://localhost:8080 - login: admin/admin
docker compose down
```

- [ ] **Step 7: Commit**

```bash
git add airflow/ data/synthetic/.gitkeep
git commit -m "feat(airflow): Add local Airflow setup with Docker Compose

- LocalExecutor with PostgreSQL backend
- Custom Dockerfile with Faker, boto3, snowflake dependencies
- Volume mounts for DAGs, scripts, credentials
- Configurable via .env file

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Synthetic Data Generator - Core Module and Customer Segmentation

**Files:**
- Create: `scripts/synthetic_data_generator.py`
- Create: `tests/test_synthetic_data_generator.py`

**Interfaces:**
- Consumes: Snowflake connection (existing .env credentials)
- Produces:
  - `CONFIG: dict` - generation parameters
  - `SyntheticDataGenerator.__init__(seed: int, config: dict)`
  - `SyntheticDataGenerator.load_reference_data() -> None`
  - `SyntheticDataGenerator.assign_customer_segments() -> dict[str, str]`
  - `SyntheticDataGenerator._select_customer(date: datetime) -> str`

- [ ] **Step 1: Create test file with customer segmentation tests**

Create `tests/test_synthetic_data_generator.py`:

```python
"""Tests for synthetic data generator."""

import pytest
from datetime import datetime
from collections import Counter


class TestCustomerSegmentation:
    """Test customer segment assignment and selection."""

    def test_segment_distribution_matches_config(self):
        """Verify 60/25/12/3 segment distribution."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        # Use mock customer list
        mock_customers = [f"cust_{i:05d}" for i in range(10000)]

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = mock_customers
        segments = gen.assign_customer_segments()

        # Count segments
        counts = Counter(segments.values())
        total = len(mock_customers)

        # Allow 2% tolerance
        assert abs(counts["one_time"] / total - 0.60) < 0.02
        assert abs(counts["occasional"] / total - 0.25) < 0.02
        assert abs(counts["loyal"] / total - 0.12) < 0.02
        assert abs(counts["champion"] / total - 0.03) < 0.02

    def test_deterministic_segmentation(self):
        """Same seed produces same segments."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        mock_customers = [f"cust_{i:05d}" for i in range(1000)]

        gen1 = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen1._customer_ids = mock_customers
        segments1 = gen1.assign_customer_segments()

        gen2 = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen2._customer_ids = mock_customers
        segments2 = gen2.assign_customer_segments()

        assert segments1 == segments2

    def test_customer_selection_respects_segments(self):
        """Champions selected more often than one-time."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        mock_customers = [f"cust_{i:05d}" for i in range(1000)]

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = mock_customers
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in mock_customers}  # All have 1 order

        # Select 5000 customers
        selections = Counter()
        test_date = datetime(2024, 1, 15)
        for i in range(5000):
            gen._rng_for_date = gen._rng  # Use same RNG for test
            customer = gen._select_customer(test_date)
            selections[customer] += 1

        # Champions (3% of customers) should have higher avg selection than one-time (60%)
        champion_customers = [c for c, s in gen._customer_segments.items() if s == "champion"]
        onetime_customers = [c for c, s in gen._customer_segments.items() if s == "one_time"]

        champion_avg = sum(selections.get(c, 0) for c in champion_customers) / len(champion_customers)
        onetime_avg = sum(selections.get(c, 0) for c in onetime_customers) / len(onetime_customers)

        assert champion_avg > onetime_avg * 5  # Champions should be selected 5x+ more often


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ecommerce-retail-analytics
python -m pytest tests/test_synthetic_data_generator.py -v
# Expected: ModuleNotFoundError or ImportError (module doesn't exist yet)
```

- [ ] **Step 3: Create synthetic_data_generator.py with CONFIG and customer logic**

Create `scripts/synthetic_data_generator.py`:

```python
"""
Synthetic data generator for e-commerce orders.

Generates deterministic synthetic orders, order_items, order_payments, and order_reviews
that reference existing customers, products, and sellers.
"""

import hashlib
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from faker import Faker

# Load environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_FILE)


CONFIG = {
    "seed": 42,
    "repeat_rate_target": 0.35,
    "base_daily_orders": 135,
    "max_daily_orders": 500,
    "growth_end_date": "2026-06-19",
    "backfill_start_date": "2018-10-18",
    "customer_segments": {
        "one_time": 0.60,
        "occasional": 0.25,
        "loyal": 0.12,
        "champion": 0.03,
    },
    "segment_max_orders": {
        "one_time": 1,      # Already had 1 order, won't order again
        "occasional": 4,    # 2-4 total lifetime orders
        "loyal": 10,        # 5-10 total lifetime orders
        "champion": 50,     # 10+ orders, cap at 50 for sanity
    },
    "segment_weights": {
        "one_time": 0,       # Never selected (already has their 1 order)
        "occasional": 1.0,   # Base weight
        "loyal": 3.0,        # 3x more likely than occasional
        "champion": 10.0,    # 10x more likely than occasional
    },
}


class SyntheticDataGenerator:
    """Generate synthetic e-commerce order data."""

    def __init__(self, seed: int = 42, config: Optional[dict] = None):
        """
        Initialize generator with seed for reproducibility.

        Args:
            seed: Random seed for deterministic generation
            config: Configuration dict (defaults to CONFIG)
        """
        self.seed = seed
        self.config = config or CONFIG
        self._rng = random.Random(seed)
        self._faker = Faker()
        Faker.seed(seed)

        # Reference data (loaded from Snowflake)
        self._customer_ids: list[str] = []
        self._product_data: pd.DataFrame = pd.DataFrame()
        self._seller_ids: list[str] = []
        self._product_seller_map: dict[str, str] = {}

        # Customer tracking
        self._customer_segments: dict[str, str] = {}
        self._customer_order_counts: dict[str, int] = {}

    def load_reference_data(self) -> None:
        """Load existing customers, products, sellers from Snowflake."""
        from snowflake.connector import connect
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        # Load private key
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

        conn = connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            private_key=private_key_bytes,
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )

        try:
            cursor = conn.cursor()

            # Load customer IDs
            cursor.execute("SELECT DISTINCT CUSTOMER_ID FROM CUSTOMERS")
            self._customer_ids = [row[0] for row in cursor.fetchall()]

            # Load product data with prices
            cursor.execute("""
                SELECT DISTINCT
                    p.PRODUCT_ID,
                    oi.SELLER_ID,
                    AVG(oi.PRICE) as AVG_PRICE,
                    AVG(oi.FREIGHT_VALUE) as AVG_FREIGHT,
                    AVG(p.PRODUCT_WEIGHT_G) as WEIGHT_G
                FROM PRODUCTS p
                JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
                GROUP BY p.PRODUCT_ID, oi.SELLER_ID
            """)
            rows = cursor.fetchall()
            self._product_data = pd.DataFrame(rows, columns=[
                "product_id", "seller_id", "avg_price", "avg_freight", "weight_g"
            ])

            # Build product -> seller mapping (use most common seller per product)
            for product_id in self._product_data["product_id"].unique():
                product_rows = self._product_data[self._product_data["product_id"] == product_id]
                # Pick the first seller (deterministic)
                self._product_seller_map[product_id] = product_rows.iloc[0]["seller_id"]

            # Load seller IDs
            cursor.execute("SELECT DISTINCT SELLER_ID FROM SELLERS")
            self._seller_ids = [row[0] for row in cursor.fetchall()]

        finally:
            conn.close()

        # Initialize order counts (all existing customers have 1 order)
        self._customer_order_counts = {c: 1 for c in self._customer_ids}

        # Assign segments
        self._customer_segments = self.assign_customer_segments()

    def assign_customer_segments(self) -> dict[str, str]:
        """
        Assign each customer to a segment based on config distribution.

        Returns:
            Dict mapping customer_id -> segment name
        """
        segments = {}
        segment_rng = random.Random(self.seed)  # Separate RNG for segment assignment

        segment_names = list(self.config["customer_segments"].keys())
        segment_weights = list(self.config["customer_segments"].values())

        for customer_id in self._customer_ids:
            # Use weighted random choice
            segment = segment_rng.choices(segment_names, weights=segment_weights, k=1)[0]
            segments[customer_id] = segment

        return segments

    def _select_customer(self, date: datetime) -> str:
        """
        Select a customer for a new order based on segment weights.

        Args:
            date: Order date (used for date-specific seeding if needed)

        Returns:
            Selected customer_id
        """
        # Build weighted list of eligible customers
        eligible = []
        weights = []

        for customer_id in self._customer_ids:
            segment = self._customer_segments[customer_id]
            current_orders = self._customer_order_counts.get(customer_id, 0)
            max_orders = self.config["segment_max_orders"][segment]

            # Skip if customer has reached their order limit
            if current_orders >= max_orders:
                continue

            base_weight = self.config["segment_weights"][segment]
            if base_weight <= 0:
                continue

            # Reduce weight as customer approaches their limit
            remaining_capacity = max_orders - current_orders
            adjusted_weight = base_weight * (remaining_capacity / max_orders)

            eligible.append(customer_id)
            weights.append(adjusted_weight)

        if not eligible:
            # Fallback: pick any non-one-time customer
            eligible = [c for c, s in self._customer_segments.items()
                       if s != "one_time"]
            weights = [1.0] * len(eligible)

        return self._rng.choices(eligible, weights=weights, k=1)[0]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ecommerce-retail-analytics
python -m pytest tests/test_synthetic_data_generator.py -v
# Expected: All 3 tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add scripts/synthetic_data_generator.py tests/test_synthetic_data_generator.py
git commit -m "feat(synthetic): Add generator core with customer segmentation

- CONFIG with segment distributions (60/25/12/3)
- SyntheticDataGenerator class with Snowflake data loading
- Customer segment assignment (deterministic)
- Weighted customer selection respecting segment limits
- Tests for distribution, determinism, and selection weighting

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Synthetic Data Generator - Order Generation

**Files:**
- Modify: `scripts/synthetic_data_generator.py`
- Modify: `tests/test_synthetic_data_generator.py`

**Interfaces:**
- Consumes: `SyntheticDataGenerator` from Task 2
- Produces:
  - `SyntheticDataGenerator.calculate_daily_orders(date: datetime) -> int`
  - `SyntheticDataGenerator.generate_order_id(date: datetime, sequence: int) -> str`
  - `SyntheticDataGenerator.generate_orders_for_date(date: datetime) -> pd.DataFrame`

- [ ] **Step 1: Add order generation tests**

Append to `tests/test_synthetic_data_generator.py`:

```python
class TestOrderGeneration:
    """Test order generation logic."""

    def test_daily_order_volume_growth(self):
        """Verify growth curve from 135 to 500 orders/day."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        # Oct 2018: ~135
        orders_oct_2018 = gen.calculate_daily_orders(datetime(2018, 10, 20))
        assert 130 <= orders_oct_2018 <= 140

        # Jun 2023: ~380
        orders_jun_2023 = gen.calculate_daily_orders(datetime(2023, 6, 15))
        assert 350 <= orders_jun_2023 <= 410

        # Jun 2026: ~500
        orders_jun_2026 = gen.calculate_daily_orders(datetime(2026, 6, 15))
        assert 480 <= orders_jun_2026 <= 520

    def test_order_id_format(self):
        """Verify order ID format: syn_YYYYMMDD_NNNNNN_HHHHHHHH."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)

        order_id = gen.generate_order_id(datetime(2024, 1, 15), 42)

        assert order_id.startswith("syn_20240115_000042_")
        assert len(order_id) == 28  # syn_ + 8 + _ + 6 + _ + 8 = 28

    def test_order_id_deterministic(self):
        """Same inputs produce same order ID."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen1 = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen2 = SyntheticDataGenerator(seed=42, config=CONFIG)

        id1 = gen1.generate_order_id(datetime(2024, 1, 15), 42)
        id2 = gen2.generate_order_id(datetime(2024, 1, 15), 42)

        assert id1 == id2

    def test_generate_orders_returns_dataframe(self):
        """generate_orders_for_date returns DataFrame with correct columns."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        # Mock reference data
        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(1000)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}

        orders_df = gen.generate_orders_for_date(datetime(2024, 1, 15))

        expected_columns = [
            "order_id", "customer_id", "order_status",
            "order_purchase_timestamp", "order_approved_at",
            "order_delivered_carrier_date", "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]

        assert list(orders_df.columns) == expected_columns
        assert len(orders_df) > 0

    def test_order_status_distribution(self):
        """Verify ~97% delivered, rest split among other statuses."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(1000)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}

        # Generate multiple days to get good sample
        all_orders = []
        for day in range(10):
            date = datetime(2024, 1, 15) + timedelta(days=day)
            gen._rng = random.Random(42 + day)  # Reset RNG per day
            orders_df = gen.generate_orders_for_date(date)
            all_orders.append(orders_df)

        combined = pd.concat(all_orders, ignore_index=True)
        status_pct = combined["order_status"].value_counts(normalize=True)

        assert status_pct.get("delivered", 0) > 0.90  # At least 90% delivered
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ecommerce-retail-analytics
python -m pytest tests/test_synthetic_data_generator.py::TestOrderGeneration -v
# Expected: AttributeError (methods don't exist yet)
```

- [ ] **Step 3: Add order generation methods to SyntheticDataGenerator**

Add to `scripts/synthetic_data_generator.py` inside the `SyntheticDataGenerator` class:

```python
    def calculate_daily_orders(self, date: datetime) -> int:
        """
        Calculate number of orders to generate for a given date.

        Growth curve: 135 + (365 * days_since_oct_2018) / 2800

        Args:
            date: The date to calculate orders for

        Returns:
            Number of orders to generate
        """
        start_date = datetime.strptime(self.config["backfill_start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(self.config["growth_end_date"], "%Y-%m-%d")

        days_elapsed = (date - start_date).days
        max_days = (end_date - start_date).days

        base = self.config["base_daily_orders"]
        max_orders = self.config["max_daily_orders"]

        # Linear growth
        if days_elapsed <= 0:
            return base
        if days_elapsed >= max_days:
            return max_orders

        growth = (max_orders - base) * days_elapsed / max_days
        return int(base + growth)

    def generate_order_id(self, date: datetime, sequence: int) -> str:
        """
        Generate deterministic order ID.

        Format: syn_{YYYYMMDD}_{sequence:06d}_{hash:8}

        Args:
            date: Order date
            sequence: Sequence number within the day

        Returns:
            Order ID string
        """
        date_str = date.strftime("%Y%m%d")

        # Create deterministic hash from seed + date + sequence
        hash_input = f"{self.seed}_{date_str}_{sequence}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]

        return f"syn_{date_str}_{sequence:06d}_{hash_value}"

    def generate_orders_for_date(self, date: datetime) -> pd.DataFrame:
        """
        Generate orders DataFrame for a single date.

        Args:
            date: The date to generate orders for

        Returns:
            DataFrame with order records
        """
        num_orders = self.calculate_daily_orders(date)

        # Reset RNG for this date (deterministic per-date generation)
        date_seed = self.seed + int(date.strftime("%Y%m%d"))
        self._rng = random.Random(date_seed)
        self._faker = Faker()
        Faker.seed(date_seed)

        orders = []

        status_weights = {
            "delivered": 0.97,
            "shipped": 0.01,
            "canceled": 0.01,
            "unavailable": 0.005,
            "processing": 0.005,
        }
        statuses = list(status_weights.keys())
        weights = list(status_weights.values())

        for seq in range(num_orders):
            order_id = self.generate_order_id(date, seq)
            customer_id = self._select_customer(date)

            # Update customer order count
            self._customer_order_counts[customer_id] = \
                self._customer_order_counts.get(customer_id, 0) + 1

            status = self._rng.choices(statuses, weights=weights, k=1)[0]

            # Generate timestamps
            # Purchase time: random hour of the day
            hour = self._rng.randint(0, 23)
            minute = self._rng.randint(0, 59)
            second = self._rng.randint(0, 59)
            purchase_ts = date.replace(hour=hour, minute=minute, second=second)

            # Approved: 0-24 hours after purchase
            approved_at = purchase_ts + timedelta(hours=self._rng.uniform(0, 24))

            # Carrier date: 1-5 days after approval
            carrier_date = approved_at + timedelta(days=self._rng.uniform(1, 5))

            # Delivery: 3-20 days after carrier
            delivery_days = self._rng.uniform(3, 20)
            delivered_date = carrier_date + timedelta(days=delivery_days)

            # Estimated delivery: actual + random variance (-3 to +5 days)
            est_variance = self._rng.uniform(-3, 5)
            estimated_date = delivered_date + timedelta(days=est_variance)

            # For non-delivered orders, clear delivery timestamps
            if status in ("canceled", "unavailable", "processing"):
                delivered_date = None
                carrier_date = None if status == "canceled" else carrier_date
            elif status == "shipped":
                delivered_date = None

            orders.append({
                "order_id": order_id,
                "customer_id": customer_id,
                "order_status": status,
                "order_purchase_timestamp": purchase_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "order_approved_at": approved_at.strftime("%Y-%m-%d %H:%M:%S") if approved_at else None,
                "order_delivered_carrier_date": carrier_date.strftime("%Y-%m-%d %H:%M:%S") if carrier_date else None,
                "order_delivered_customer_date": delivered_date.strftime("%Y-%m-%d %H:%M:%S") if delivered_date else None,
                "order_estimated_delivery_date": estimated_date.strftime("%Y-%m-%d") if estimated_date else None,
            })

        return pd.DataFrame(orders)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ecommerce-retail-analytics
python -m pytest tests/test_synthetic_data_generator.py::TestOrderGeneration -v
# Expected: All 5 tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add scripts/synthetic_data_generator.py tests/test_synthetic_data_generator.py
git commit -m "feat(synthetic): Add order generation with growth curve

- calculate_daily_orders: linear growth 135 → 500 orders/day
- generate_order_id: deterministic format syn_YYYYMMDD_NNNNNN_HHHHHHHH
- generate_orders_for_date: full order DataFrame with timestamps
- Status distribution: 97% delivered, 3% other
- Timestamp flow: purchase → approved → carrier → delivered

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Synthetic Data Generator - Order Items, Payments, and Reviews

**Files:**
- Modify: `scripts/synthetic_data_generator.py`
- Modify: `tests/test_synthetic_data_generator.py`

**Interfaces:**
- Consumes: `generate_orders_for_date()` from Task 3
- Produces:
  - `SyntheticDataGenerator.generate_order_items(orders_df: pd.DataFrame) -> pd.DataFrame`
  - `SyntheticDataGenerator.generate_order_payments(orders_df: pd.DataFrame, items_df: pd.DataFrame) -> pd.DataFrame`
  - `SyntheticDataGenerator.generate_order_reviews(orders_df: pd.DataFrame) -> pd.DataFrame`
  - `SyntheticDataGenerator.generate_all_for_date(date: datetime) -> dict[str, pd.DataFrame]`

- [ ] **Step 1: Add tests for items, payments, reviews**

Append to `tests/test_synthetic_data_generator.py`:

```python
class TestOrderItems:
    """Test order items generation."""

    def test_items_per_order_distribution(self):
        """Verify 60% single item, 30% 2-3 items, 10% 4+ items."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(1000)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}
        gen._product_data = pd.DataFrame({
            "product_id": [f"prod_{i:05d}" for i in range(100)],
            "seller_id": [f"seller_{i % 10:03d}" for i in range(100)],
            "avg_price": [50.0 + i for i in range(100)],
            "avg_freight": [10.0 + i * 0.1 for i in range(100)],
            "weight_g": [500 + i * 10 for i in range(100)],
        })
        gen._product_seller_map = {f"prod_{i:05d}": f"seller_{i % 10:03d}" for i in range(100)}

        # Generate many orders
        orders = []
        for day in range(30):
            date = datetime(2024, 1, 1) + timedelta(days=day)
            orders.append(gen.generate_orders_for_date(date))
        orders_df = pd.concat(orders, ignore_index=True)

        items_df = gen.generate_order_items(orders_df)

        # Count items per order
        items_per_order = items_df.groupby("order_id").size()
        total_orders = len(items_per_order)

        single_item = (items_per_order == 1).sum() / total_orders
        two_three = ((items_per_order >= 2) & (items_per_order <= 3)).sum() / total_orders
        four_plus = (items_per_order >= 4).sum() / total_orders

        # Allow 10% tolerance
        assert 0.50 <= single_item <= 0.70
        assert 0.20 <= two_three <= 0.40
        assert 0.05 <= four_plus <= 0.20

    def test_items_have_required_columns(self):
        """Verify order_items has all required columns."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(100)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}
        gen._product_data = pd.DataFrame({
            "product_id": [f"prod_{i:05d}" for i in range(50)],
            "seller_id": [f"seller_{i % 5:03d}" for i in range(50)],
            "avg_price": [50.0] * 50,
            "avg_freight": [10.0] * 50,
            "weight_g": [500] * 50,
        })
        gen._product_seller_map = {f"prod_{i:05d}": f"seller_{i % 5:03d}" for i in range(50)}

        orders_df = gen.generate_orders_for_date(datetime(2024, 1, 15))
        items_df = gen.generate_order_items(orders_df)

        expected_columns = [
            "order_id", "order_item_id", "product_id", "seller_id",
            "shipping_limit_date", "price", "freight_value"
        ]
        assert list(items_df.columns) == expected_columns


class TestOrderPayments:
    """Test order payments generation."""

    def test_payment_type_distribution(self):
        """Verify credit_card 74%, boleto 19%, voucher 5%, debit 2%."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(1000)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}
        gen._product_data = pd.DataFrame({
            "product_id": [f"prod_{i:05d}" for i in range(100)],
            "seller_id": [f"seller_{i % 10:03d}" for i in range(100)],
            "avg_price": [100.0] * 100,
            "avg_freight": [15.0] * 100,
            "weight_g": [500] * 100,
        })
        gen._product_seller_map = {f"prod_{i:05d}": f"seller_{i % 10:03d}" for i in range(100)}

        # Generate payments for many orders
        orders = []
        for day in range(30):
            date = datetime(2024, 1, 1) + timedelta(days=day)
            orders.append(gen.generate_orders_for_date(date))
        orders_df = pd.concat(orders, ignore_index=True)
        items_df = gen.generate_order_items(orders_df)
        payments_df = gen.generate_order_payments(orders_df, items_df)

        payment_pct = payments_df["payment_type"].value_counts(normalize=True)

        # Allow 5% tolerance
        assert 0.69 <= payment_pct.get("credit_card", 0) <= 0.79
        assert 0.14 <= payment_pct.get("boleto", 0) <= 0.24

    def test_payment_value_matches_items(self):
        """Verify payment value equals sum of item prices + freight."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(100)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}
        gen._product_data = pd.DataFrame({
            "product_id": [f"prod_{i:05d}" for i in range(50)],
            "seller_id": [f"seller_{i % 5:03d}" for i in range(50)],
            "avg_price": [100.0] * 50,
            "avg_freight": [15.0] * 50,
            "weight_g": [500] * 50,
        })
        gen._product_seller_map = {f"prod_{i:05d}": f"seller_{i % 5:03d}" for i in range(50)}

        orders_df = gen.generate_orders_for_date(datetime(2024, 1, 15))
        items_df = gen.generate_order_items(orders_df)
        payments_df = gen.generate_order_payments(orders_df, items_df)

        # Check a few orders
        for order_id in orders_df["order_id"].head(10):
            order_items = items_df[items_df["order_id"] == order_id]
            expected_total = order_items["price"].sum() + order_items["freight_value"].sum()

            order_payments = payments_df[payments_df["order_id"] == order_id]
            actual_total = order_payments["payment_value"].sum()

            assert abs(expected_total - actual_total) < 0.01


class TestOrderReviews:
    """Test order reviews generation."""

    def test_review_score_distribution(self):
        """Verify score distribution: 5 (57%), 4 (19%), 1 (12%), 3 (8%), 2 (4%)."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(1000)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}

        # Generate reviews for many orders
        orders = []
        for day in range(30):
            date = datetime(2024, 1, 1) + timedelta(days=day)
            orders.append(gen.generate_orders_for_date(date))
        orders_df = pd.concat(orders, ignore_index=True)

        # Only delivered orders get reviews
        delivered_orders = orders_df[orders_df["order_status"] == "delivered"]
        reviews_df = gen.generate_order_reviews(delivered_orders)

        score_pct = reviews_df["review_score"].value_counts(normalize=True)

        # Allow 5% tolerance
        assert 0.52 <= score_pct.get(5, 0) <= 0.62
        assert 0.14 <= score_pct.get(4, 0) <= 0.24

    def test_reviews_have_required_columns(self):
        """Verify reviews DataFrame has all required columns."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(100)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}

        orders_df = gen.generate_orders_for_date(datetime(2024, 1, 15))
        delivered_orders = orders_df[orders_df["order_status"] == "delivered"]
        reviews_df = gen.generate_order_reviews(delivered_orders)

        expected_columns = [
            "review_id", "order_id", "review_score",
            "review_comment_title", "review_comment_message",
            "review_creation_date", "review_answer_timestamp"
        ]
        assert list(reviews_df.columns) == expected_columns


class TestGenerateAll:
    """Test the combined generate_all_for_date method."""

    def test_generate_all_returns_four_dataframes(self):
        """generate_all_for_date returns dict with orders, items, payments, reviews."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(100)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}
        gen._product_data = pd.DataFrame({
            "product_id": [f"prod_{i:05d}" for i in range(50)],
            "seller_id": [f"seller_{i % 5:03d}" for i in range(50)],
            "avg_price": [100.0] * 50,
            "avg_freight": [15.0] * 50,
            "weight_g": [500] * 50,
        })
        gen._product_seller_map = {f"prod_{i:05d}": f"seller_{i % 5:03d}" for i in range(50)}

        result = gen.generate_all_for_date(datetime(2024, 1, 15))

        assert set(result.keys()) == {"orders", "order_items", "order_payments", "order_reviews"}
        assert len(result["orders"]) > 0
        assert len(result["order_items"]) > 0
        assert len(result["order_payments"]) > 0

    def test_referential_integrity(self):
        """All order_items and payments reference valid orders."""
        from scripts.synthetic_data_generator import SyntheticDataGenerator, CONFIG

        gen = SyntheticDataGenerator(seed=42, config=CONFIG)
        gen._customer_ids = [f"cust_{i:05d}" for i in range(100)]
        gen._customer_segments = gen.assign_customer_segments()
        gen._customer_order_counts = {c: 1 for c in gen._customer_ids}
        gen._product_data = pd.DataFrame({
            "product_id": [f"prod_{i:05d}" for i in range(50)],
            "seller_id": [f"seller_{i % 5:03d}" for i in range(50)],
            "avg_price": [100.0] * 50,
            "avg_freight": [15.0] * 50,
            "weight_g": [500] * 50,
        })
        gen._product_seller_map = {f"prod_{i:05d}": f"seller_{i % 5:03d}" for i in range(50)}

        result = gen.generate_all_for_date(datetime(2024, 1, 15))

        order_ids = set(result["orders"]["order_id"])

        # All order_items reference valid orders
        item_order_ids = set(result["order_items"]["order_id"])
        assert item_order_ids.issubset(order_ids)

        # All payments reference valid orders
        payment_order_ids = set(result["order_payments"]["order_id"])
        assert payment_order_ids.issubset(order_ids)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ecommerce-retail-analytics
python -m pytest tests/test_synthetic_data_generator.py::TestOrderItems -v
python -m pytest tests/test_synthetic_data_generator.py::TestOrderPayments -v
python -m pytest tests/test_synthetic_data_generator.py::TestOrderReviews -v
python -m pytest tests/test_synthetic_data_generator.py::TestGenerateAll -v
# Expected: AttributeError (methods don't exist)
```

- [ ] **Step 3: Add generate_order_items method**

Add to `scripts/synthetic_data_generator.py`:

```python
    def generate_order_items(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate order items for given orders.

        Distribution: 60% single item, 30% 2-3 items, 10% 4+ items

        Args:
            orders_df: Orders DataFrame

        Returns:
            DataFrame with order item records
        """
        items = []

        # Items per order weights
        item_count_options = [1, 2, 3, 4, 5, 6]
        item_count_weights = [0.60, 0.15, 0.15, 0.05, 0.03, 0.02]

        product_ids = self._product_data["product_id"].tolist()

        for _, order in orders_df.iterrows():
            order_id = order["order_id"]
            purchase_ts = datetime.strptime(order["order_purchase_timestamp"], "%Y-%m-%d %H:%M:%S")

            # Determine number of items
            num_items = self._rng.choices(item_count_options, weights=item_count_weights, k=1)[0]

            # Select products (no duplicates within order)
            selected_products = self._rng.sample(product_ids, min(num_items, len(product_ids)))

            for item_seq, product_id in enumerate(selected_products, start=1):
                # Get product info
                product_row = self._product_data[self._product_data["product_id"] == product_id].iloc[0]
                seller_id = self._product_seller_map.get(product_id, product_row["seller_id"])

                # Price with ±10% variance
                base_price = float(product_row["avg_price"])
                price = base_price * self._rng.uniform(0.90, 1.10)

                # Freight based on weight + variance
                base_freight = float(product_row["avg_freight"])
                freight = base_freight * self._rng.uniform(0.80, 1.20)

                # Shipping limit: 7-14 days after purchase
                shipping_days = self._rng.randint(7, 14)
                shipping_limit = purchase_ts + timedelta(days=shipping_days)

                items.append({
                    "order_id": order_id,
                    "order_item_id": item_seq,
                    "product_id": product_id,
                    "seller_id": seller_id,
                    "shipping_limit_date": shipping_limit.strftime("%Y-%m-%d %H:%M:%S"),
                    "price": round(price, 2),
                    "freight_value": round(freight, 2),
                })

        return pd.DataFrame(items)

    def generate_order_payments(self, orders_df: pd.DataFrame, items_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate order payments matching item totals.

        Distribution: credit_card 74%, boleto 19%, voucher 5%, debit 2%

        Args:
            orders_df: Orders DataFrame
            items_df: Order items DataFrame

        Returns:
            DataFrame with payment records
        """
        payments = []

        payment_types = ["credit_card", "boleto", "voucher", "debit_card"]
        payment_weights = [0.74, 0.19, 0.05, 0.02]

        # Calculate order totals
        order_totals = items_df.groupby("order_id").agg({
            "price": "sum",
            "freight_value": "sum"
        }).reset_index()
        order_totals["total"] = order_totals["price"] + order_totals["freight_value"]

        for _, order in orders_df.iterrows():
            order_id = order["order_id"]

            # Get order total
            total_row = order_totals[order_totals["order_id"] == order_id]
            if total_row.empty:
                continue
            total_value = float(total_row["total"].iloc[0])

            # Select payment type
            payment_type = self._rng.choices(payment_types, weights=payment_weights, k=1)[0]

            # Installments (credit_card only, others = 1)
            if payment_type == "credit_card":
                # Weighted toward lower installments
                installment_options = [1, 2, 3, 4, 5, 6, 8, 10, 12]
                installment_weights = [0.30, 0.20, 0.15, 0.10, 0.08, 0.07, 0.05, 0.03, 0.02]
                installments = self._rng.choices(installment_options, weights=installment_weights, k=1)[0]
            else:
                installments = 1

            payments.append({
                "order_id": order_id,
                "payment_sequential": 1,
                "payment_type": payment_type,
                "payment_installments": installments,
                "payment_value": round(total_value, 2),
            })

        return pd.DataFrame(payments)

    def generate_order_reviews(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate reviews for delivered orders.

        Score distribution: 5 (57%), 4 (19%), 1 (12%), 3 (8%), 2 (4%)

        Args:
            orders_df: Orders DataFrame (should be filtered to delivered only)

        Returns:
            DataFrame with review records
        """
        reviews = []

        score_options = [5, 4, 1, 3, 2]
        score_weights = [0.57, 0.19, 0.12, 0.08, 0.04]

        for _, order in orders_df.iterrows():
            order_id = order["order_id"]

            # Parse delivery date
            delivered_str = order.get("order_delivered_customer_date")
            if not delivered_str or pd.isna(delivered_str):
                # Skip non-delivered orders
                continue

            delivered_date = datetime.strptime(delivered_str, "%Y-%m-%d %H:%M:%S")

            # Review creation: 1-14 days after delivery
            review_days = self._rng.randint(1, 14)
            review_creation = delivered_date + timedelta(days=review_days)

            # Answer: 0-7 days after creation
            answer_days = self._rng.randint(0, 7)
            answer_ts = review_creation + timedelta(days=answer_days)

            # Score
            score = self._rng.choices(score_options, weights=score_weights, k=1)[0]

            # Title and message (60% and 58% null respectively)
            title = None
            message = None

            if self._rng.random() > 0.60:
                title = self._faker.sentence(nb_words=self._rng.randint(3, 8))

            if self._rng.random() > 0.58:
                message = self._faker.paragraph(nb_sentences=self._rng.randint(1, 3))

            # Generate review ID
            review_hash = hashlib.md5(f"{self.seed}_{order_id}_review".encode()).hexdigest()[:16]
            review_id = f"syn_{review_hash}"

            reviews.append({
                "review_id": review_id,
                "order_id": order_id,
                "review_score": score,
                "review_comment_title": title,
                "review_comment_message": message,
                "review_creation_date": review_creation.strftime("%Y-%m-%d %H:%M:%S"),
                "review_answer_timestamp": answer_ts.strftime("%Y-%m-%d %H:%M:%S"),
            })

        return pd.DataFrame(reviews)

    def generate_all_for_date(self, date: datetime) -> dict[str, pd.DataFrame]:
        """
        Generate all synthetic data for a single date.

        Args:
            date: The date to generate data for

        Returns:
            Dict with keys: orders, order_items, order_payments, order_reviews
        """
        orders_df = self.generate_orders_for_date(date)
        items_df = self.generate_order_items(orders_df)
        payments_df = self.generate_order_payments(orders_df, items_df)

        # Reviews only for delivered orders
        delivered_orders = orders_df[orders_df["order_status"] == "delivered"]
        reviews_df = self.generate_order_reviews(delivered_orders)

        return {
            "orders": orders_df,
            "order_items": items_df,
            "order_payments": payments_df,
            "order_reviews": reviews_df,
        }
```

- [ ] **Step 4: Run all tests**

```bash
cd ecommerce-retail-analytics
python -m pytest tests/test_synthetic_data_generator.py -v
# Expected: All tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add scripts/synthetic_data_generator.py tests/test_synthetic_data_generator.py
git commit -m "feat(synthetic): Add order items, payments, and reviews generation

- generate_order_items: 60% single item, 30% 2-3, 10% 4+
- generate_order_payments: credit_card 74%, boleto 19%, voucher 5%, debit 2%
- generate_order_reviews: score distribution 5(57%)/4(19%)/1(12%)/3(8%)/2(4%)
- generate_all_for_date: combined method returning all 4 DataFrames
- Price variance ±10%, freight variance ±20%
- Review timestamps relative to delivery date

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Backfill DAG

**Files:**
- Create: `airflow/dags/backfill_synthetic_orders.py`

**Interfaces:**
- Consumes: `SyntheticDataGenerator.generate_all_for_date()` from Task 4
- Produces: Airflow DAG `backfill_synthetic_orders` with tasks for generation, S3 upload, Snowflake COPY

- [ ] **Step 1: Create backfill DAG**

Create `airflow/dags/backfill_synthetic_orders.py`:

```python
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
```

- [ ] **Step 2: Verify DAG syntax**

```bash
cd ecommerce-retail-analytics/airflow
docker compose up -d
# Wait for services to start
docker compose exec airflow-webserver airflow dags list | grep backfill
# Expected: backfill_synthetic_orders listed
docker compose down
```

- [ ] **Step 3: Commit**

```bash
git add airflow/dags/backfill_synthetic_orders.py
git commit -m "feat(airflow): Add backfill DAG for synthetic orders

- Manual trigger with start_date/end_date params
- Tasks: load_reference_data → generate_batch → upload_to_s3 → copy_into → cleanup
- Parallel COPY INTO for all 4 tables
- 4-hour execution timeout for full backfill
- Retry configuration per task type

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 6: Daily DAG

**Files:**
- Create: `airflow/dags/daily_synthetic_orders.py`

**Interfaces:**
- Consumes: `SyntheticDataGenerator.generate_all_for_date()` from Task 4
- Produces: Airflow DAG `daily_synthetic_orders` scheduled @daily

- [ ] **Step 1: Create daily DAG**

Create `airflow/dags/daily_synthetic_orders.py`:

```python
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
ON_ERROR = 'CONTINUE';
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
```

- [ ] **Step 2: Verify DAG syntax**

```bash
cd ecommerce-retail-analytics/airflow
docker compose up -d
docker compose exec airflow-webserver airflow dags list | grep daily
# Expected: daily_synthetic_orders listed
docker compose down
```

- [ ] **Step 3: Commit**

```bash
git add airflow/dags/daily_synthetic_orders.py
git commit -m "feat(airflow): Add daily DAG for synthetic orders

- Scheduled @daily at 2:00 AM UTC
- Generates previous day's data
- Dynamic COPY SQL with date from XCom
- Parallel COPY INTO for all 4 tables
- Start date: 2026-06-20 (after backfill)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Airflow Snowflake Connection Setup

**Files:**
- Modify: `airflow/docker-compose.yml` (add connection setup)

**Interfaces:**
- Consumes: Snowflake credentials from `.env`
- Produces: `snowflake_default` Airflow connection

- [ ] **Step 1: Add connection creation to airflow-init**

Update the `airflow-init` service in `airflow/docker-compose.yml`:

```yaml
  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        airflow db init
        airflow users create \
          --username admin \
          --firstname Admin \
          --lastname User \
          --role Admin \
          --email admin@example.com \
          --password admin

        # Create Snowflake connection
        airflow connections add snowflake_default \
          --conn-type snowflake \
          --conn-host "${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com" \
          --conn-login "${SNOWFLAKE_USER}" \
          --conn-schema "${SNOWFLAKE_SCHEMA:-RAW}" \
          --conn-extra "{
            \"account\": \"${SNOWFLAKE_ACCOUNT}\",
            \"warehouse\": \"${SNOWFLAKE_WAREHOUSE}\",
            \"database\": \"${SNOWFLAKE_DATABASE}\",
            \"role\": \"${SNOWFLAKE_ROLE}\",
            \"private_key_path\": \"/home/airflow/.snowflake/rsa_key.p8\",
            \"private_key_passphrase\": \"${SNOWFLAKE_PRIVATE_KEY_PASSPHRASE}\"
          }" || true
    depends_on:
      postgres:
        condition: service_healthy
```

- [ ] **Step 2: Rebuild and verify connection**

```bash
cd ecommerce-retail-analytics/airflow
docker compose down -v  # Remove volumes to reset DB
docker compose up -d
# Wait for init to complete
sleep 60
docker compose exec airflow-webserver airflow connections get snowflake_default
# Expected: Connection details displayed
docker compose down
```

- [ ] **Step 3: Commit**

```bash
git add airflow/docker-compose.yml
git commit -m "feat(airflow): Add Snowflake connection setup in init

- Creates snowflake_default connection on startup
- Uses private key authentication
- Reads credentials from environment variables

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 8: End-to-End Validation

**Files:**
- Create: `scripts/validate_synthetic_data.py`

**Interfaces:**
- Consumes: Snowflake RAW tables with synthetic data
- Produces: Validation report printed to console

- [ ] **Step 1: Create validation script**

Create `scripts/validate_synthetic_data.py`:

```python
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
    status = "✓ PASS" if 30 <= repeat_rate <= 40 else "✗ FAIL"
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

    # Orders → Customers
    cursor.execute("""
        SELECT COUNT(*) FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_id LIKE 'syn_%' AND c.customer_id IS NULL
    """)
    orphan_orders = cursor.fetchone()[0]
    status = "✓ PASS" if orphan_orders == 0 else "✗ FAIL"
    print(f"   Orders with invalid customer_id: {orphan_orders} {status}")

    # Order items → Orders
    cursor.execute("""
        SELECT COUNT(*) FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.order_id
        WHERE oi.order_id LIKE 'syn_%' AND o.order_id IS NULL
    """)
    orphan_items = cursor.fetchone()[0]
    status = "✓ PASS" if orphan_items == 0 else "✗ FAIL"
    print(f"   Order items with invalid order_id: {orphan_items} {status}")

    # Order items → Products
    cursor.execute("""
        SELECT COUNT(*) FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id LIKE 'syn_%' AND p.product_id IS NULL
    """)
    orphan_products = cursor.fetchone()[0]
    status = "✓ PASS" if orphan_products == 0 else "✗ FAIL"
    print(f"   Order items with invalid product_id: {orphan_products} {status}")

    # 5. Null checks
    print("\n5. NULL CHECKS")
    cursor.execute("""
        SELECT COUNT(*) FROM orders
        WHERE order_id LIKE 'syn_%'
        AND (order_id IS NULL OR customer_id IS NULL OR order_status IS NULL)
    """)
    null_orders = cursor.fetchone()[0]
    status = "✓ PASS" if null_orders == 0 else "✗ FAIL"
    print(f"   Orders with null required fields: {null_orders} {status}")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run_validation()
```

- [ ] **Step 2: Run validation (after backfill)**

```bash
cd ecommerce-retail-analytics
python scripts/validate_synthetic_data.py
# Expected: All checks PASS
```

- [ ] **Step 3: Commit**

```bash
git add scripts/validate_synthetic_data.py
git commit -m "feat(scripts): Add synthetic data validation script

- Validates repeat purchase rate (30-40%)
- Checks order volume growth curve
- Verifies referential integrity (customers, products)
- Null checks on required fields

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Summary

| Task | Description | Key Files |
|------|-------------|-----------|
| 1 | Airflow Docker setup | `airflow/docker-compose.yml`, `Dockerfile`, `requirements.txt` |
| 2 | Generator core + customer segments | `scripts/synthetic_data_generator.py` |
| 3 | Order generation | `scripts/synthetic_data_generator.py` |
| 4 | Items, payments, reviews | `scripts/synthetic_data_generator.py` |
| 5 | Backfill DAG | `airflow/dags/backfill_synthetic_orders.py` |
| 6 | Daily DAG | `airflow/dags/daily_synthetic_orders.py` |
| 7 | Snowflake connection | `airflow/docker-compose.yml` |
| 8 | Validation script | `scripts/validate_synthetic_data.py` |

**Total estimated commits:** 8
