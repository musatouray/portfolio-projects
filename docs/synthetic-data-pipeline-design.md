# Synthetic Data Pipeline Design

**Date:** 2026-06-19
**Status:** Approved
**Purpose:** Generate synthetic order data from Oct 2018 to present, enabling realistic analytics patterns (RFM, cohort retention, CLV, churn) with 30-40% repeat purchase rate

## Problem Statement

The original Olist dataset contains ~99,000 orders from Sep 2016 to Oct 2018 with 0% repeat buyers (every customer_id appears exactly once). This makes it impossible to demonstrate key analytics patterns:

- **RFM Segmentation:** Frequency dimension is meaningless with F=1
- **Cohort Retention:** 0% retention across all periods
- **CLV:** No purchase history to project future value
- **Churn:** Cannot identify lapsed customers without purchase history

## Requirements

1. **Extend timeline:** Generate orders from Oct 2018 to Jun 2026 (~7.7 years)
2. **Repeat purchases:** Target 30-40% of customers making multiple purchases
3. **Growth curve:** Daily volume grows from ~135 to ~500 orders/day
4. **Full order lifecycle:** Generate orders, order_items, order_payments, order_reviews
5. **Referential integrity:** Use existing customers, products, sellers
6. **Reproducible:** Deterministic seed-based generation
7. **Backfill + incremental:** One-time historical load + daily ongoing generation

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LOCAL AIRFLOW                                │
│  ┌─────────────────────┐      ┌─────────────────────┐               │
│  │ backfill_dag.py     │      │ daily_dag.py        │               │
│  │ (manual trigger)    │      │ (@daily schedule)   │               │
│  └──────────┬──────────┘      └──────────┬──────────┘               │
│             │                            │                           │
│             └────────────┬───────────────┘                           │
│                          ▼                                           │
│            ┌─────────────────────────┐                               │
│            │ synthetic_data_generator│  ← Shared Python module       │
│            │ (Faker + business logic)│                               │
│            └─────────────┬───────────┘                               │
└──────────────────────────┼───────────────────────────────────────────┘
                           ▼
              ┌─────────────────────────┐
              │     AWS S3 Bucket       │
              │ ecommerce-retail-       │
              │ analytics-raw/          │
              │  ├── orders/            │
              │  ├── order_items/       │
              │  ├── order_payments/    │
              │  └── order_reviews/     │
              └─────────────┬───────────┘
                            ▼
              ┌─────────────────────────┐
              │  Snowflake COPY INTO    │
              │  ECOMMERCE_RETAIL_DB_   │
              │  DEV.RAW.*              │
              └─────────────┬───────────┘
                            ▼
              ┌─────────────────────────┐
              │  dbt build              │
              │  (existing pipeline)    │
              │  staging → marts        │
              └─────────────────────────┘
```

## Data Generation Logic

### Customer Selection (30-40% Repeat Rate)

At generation start, pre-assign each existing customer to a segment:

| Segment | % of Customers | Behavior |
|---------|----------------|----------|
| One-time | 60% | Never selected again after original order |
| Occasional | 25% | 2-4 orders lifetime, weight decreases after each |
| Loyal | 12% | 5-10 orders lifetime, consistent weight |
| Champion | 3% | 10+ orders lifetime, high selection weight |

### Order Volume Growth Curve

```
Daily orders = 135 + (365 * days_since_oct_2018) / 2800

Oct 2018:  ~135 orders/day
Dec 2020:  ~250 orders/day
Jun 2023:  ~380 orders/day
Jun 2026:  ~500 orders/day

Total backfill: ~700,000 synthetic orders
```

### Order Items Generation

| Field | Generation Rule |
|-------|-----------------|
| Items per order | Weighted: 1 item (60%), 2-3 (30%), 4+ (10%) |
| Product selection | Random from existing 32,951 products |
| Seller selection | Use product's original seller (maintains relationship) |
| Price | Product's original price ± 10% variance |
| Freight | Based on product weight + random distance factor |

### Order Payments Generation

| Field | Generation Rule |
|-------|-----------------|
| Payment type | Weighted: credit_card (74%), boleto (19%), voucher (5%), debit_card (2%) |
| Installments | credit_card: 1-12 weighted toward lower; others: 1 |
| Payment value | Sum of (item prices + freight) for the order |

### Order Reviews Generation

| Field | Generation Rule |
|-------|-----------------|
| Review score | Weighted: 5 (57%), 4 (19%), 1 (12%), 3 (8%), 2 (4%) |
| Review title | Faker sentence or null (60% null) |
| Review message | Faker paragraph or null (58% null) |
| Timestamps | creation: 1-14 days after delivery; answer: 0-7 days after creation |

### Order Status & Timestamps

```
Status distribution:
├── delivered:    97%
├── shipped:      1%
├── canceled:     1%
├── unavailable:  0.5%
└── other:        0.5%

Timestamp flow:
purchase → approved (0-24h) → carrier (1-5 days) → delivered (3-20 days)
```

## File Structure

```
ecommerce-retail-analytics/
├── airflow/
│   ├── docker-compose.yml                # Local Airflow setup
│   ├── Dockerfile                        # Custom image with dependencies
│   ├── requirements.txt                  # Airflow + Faker + boto3 + snowflake
│   │
│   ├── dags/
│   │   ├── backfill_synthetic_orders.py  # Manual trigger, date range params
│   │   └── daily_synthetic_orders.py     # @daily schedule
│   │
│   ├── plugins/
│   │
│   └── config/
│
├── scripts/
│   ├── synthetic_data_generator.py       # Core generation logic
│   ├── transform_to_us_geography.py      # Existing
│   └── load_to_snowflake.py              # Existing
│
├── data/
│   └── synthetic/                        # Local staging before S3 upload
│
└── docs/
    └── synthetic-data-pipeline-design.md # This document
```

## S3 & Snowflake Integration

### S3 File Naming

```
s3://ecommerce-retail-analytics-raw/
├── orders/
│   ├── orders_2018-10-18.csv
│   ├── orders_2018-10-19.csv
│   └── ...
├── order_items/
│   ├── order_items_2018-10-18.csv
│   └── ...
├── order_payments/
│   ├── order_payments_2018-10-18.csv
│   └── ...
└── order_reviews/
    ├── order_reviews_2018-10-18.csv
    └── ...
```

### Snowflake COPY Strategy

Append with deduplication in staging:

```sql
COPY INTO RAW.ORDERS
FROM @raw_ecommerce_s3_stage/orders/orders_{date}.csv
FILE_FORMAT = csv_format
ON_ERROR = 'CONTINUE';
```

Staging models already deduplicate via `ROW_NUMBER() OVER (PARTITION BY order_id ...)`.

### Order ID Generation

```python
def generate_order_id(date: str, sequence: int, seed: int) -> str:
    """
    Format: syn_{YYYYMMDD}_{sequence:06d}_{hash:8}
    Example: syn_20240115_000042_a3f8c921

    - 'syn_' prefix distinguishes from original data
    - Date + sequence ensures uniqueness within day
    - Hash from seed ensures reproducibility
    """
```

## Airflow DAGs

### Backfill DAG

```
DAG: backfill_synthetic_orders
├── Schedule: None (manual trigger)
├── Params: start_date, end_date
│
└── Tasks:
    load_reference_data
        ↓
    generate_batch (loop through dates)
        ↓
    upload_to_s3
        ↓
    copy_into_snowflake
        ↓
    cleanup_local_files
```

**Trigger:** `airflow dags trigger backfill_synthetic_orders --conf '{"start_date": "2018-10-18", "end_date": "2026-06-19"}'`

### Daily DAG

```
DAG: daily_synthetic_orders
├── Schedule: @daily
├── Start date: 2026-06-20
│
└── Tasks:
    load_reference_data
        ↓
    generate_daily
        ↓
    upload_to_s3
        ↓
    copy_into_snowflake
        ↓
    trigger_dbt_build (optional)
```

### Configuration

```python
CONFIG = {
    "seed": 42,
    "repeat_rate_target": 0.35,
    "base_daily_orders": 135,
    "max_daily_orders": 500,
    "growth_end_date": "2026-06-19",
    "customer_segments": {
        "one_time": 0.60,
        "occasional": 0.25,
        "loyal": 0.12,
        "champion": 0.03
    }
}
```

## Error Handling & Idempotency

### Retry Strategy

| Task | Retries | Retry Delay |
|------|---------|-------------|
| load_reference_data | 3 | 60s |
| generate_batch/daily | 1 | 30s |
| upload_to_s3 | 3 | 60s |
| copy_into_snowflake | 3 | 120s |

### Idempotency Chain

1. Generator uses deterministic seed → same date + seed = same orders
2. S3 upload overwrites by filename → orders_2024-01-15.csv replaces previous
3. Snowflake COPY appends → staging model deduplicates on order_id

**Result:** Re-running any date is safe.

## Testing Strategy

### Unit Tests

- `test_customer_segment_distribution()` - Assert 60/25/12/3 split
- `test_repeat_purchase_rate()` - Assert 30-40% from repeat customers
- `test_order_volume_growth_curve()` - Assert growth from 135 to 500/day
- `test_deterministic_output()` - Same seed + date = identical DataFrame
- `test_referential_integrity()` - All FKs valid

### Validation Queries

```sql
-- Repeat purchase rate (target: 30-40%)
SELECT
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END) * 100.0
    / COUNT(DISTINCT customer_id) AS repeat_rate
FROM (
    SELECT customer_id, COUNT(*) as order_count
    FROM raw.orders
    WHERE order_id LIKE 'syn_%'
    GROUP BY customer_id
);

-- Order volume growth
SELECT
    DATE_TRUNC('year', order_purchase_timestamp) AS year,
    COUNT(*) / 365 AS avg_daily_orders
FROM raw.orders
WHERE order_id LIKE 'syn_%'
GROUP BY 1 ORDER BY 1;
```

## Out of Scope

- New customers, sellers, or products (use existing only)
- Modifying original 2016-2018 data
- Cloud Airflow deployment (local only)
- Real-time streaming (batch only)
- dbt model changes (existing models handle synthetic data)

## Dependencies

- Python 3.11+
- Apache Airflow 2.x (local Docker setup)
- Faker library
- boto3 (S3 uploads)
- snowflake-connector-python
- Existing S3 integration (`s3_ecommerce_integration`)
- Existing Snowflake stage (`raw_ecommerce_s3_stage`)
