# Data Warehouse Reference

## Snowflake Environment

### Connection Details

| Setting | Value |
|---------|-------|
| Warehouse | `ECOMMERCE_RETAIL_WH` |
| Role | `LEAD_DATA_ENGINEER_ROLE` |
| Auth | Keypair (RSA) |

### Databases

| Database | Purpose |
|----------|---------|
| `ECOMMERCE_RETAIL_DB_DEV` | Development + Bronze/Silver |
| `ECOMMERCE_RETAIL_DB_PROD` | Production Gold layer |

### Schema Map

```
ECOMMERCE_RETAIL_DB_DEV
├── RAW              ← Bronze: Source data (Olist CSVs)
├── STAGING          ← Silver: Cleaned views
├── INTERMEDIATE     ← Gold-Dev: Enriched models
└── MARTS            ← Gold-Dev: Analytics tables

ECOMMERCE_RETAIL_DB_PROD
├── INTERMEDIATE     ← Gold-Prod: Enriched models
└── MARTS            ← Gold-Prod: Analytics tables (Power BI connects here)
```

### S3 Integration (Incremental Pipeline)

| Resource | Value |
|----------|-------|
| S3 Bucket | `s3://ecommerce-retail-analytics-raw/` |
| Storage Integration | `s3_ecommerce_integration` |
| External Stage | `raw_ecommerce_s3_stage` |
| File Format | `csv_format` |

```sql
-- List files in S3 stage
LIST @ECOMMERCE_RETAIL_DB_DEV.RAW.raw_ecommerce_s3_stage;

-- Load data from S3 to table
COPY INTO orders
FROM @raw_ecommerce_s3_stage/orders/
PATTERN = '.*\.csv'
ON_ERROR = 'CONTINUE';
```

## Source Tables (RAW Schema)

| Table | Primary Key | Row Count | Notes |
|-------|-------------|-----------|-------|
| `customers` | customer_id | ~99k | May have duplicates per customer_unique_id |
| `orders` | order_id | ~99k | Statuses: created → approved → shipped → delivered |
| `order_items` | (order_id, order_item_id) | ~113k | Composite key |
| `order_payments` | (order_id, payment_sequential) | ~104k | Composite key |
| `order_reviews` | review_id | ~100k | Has duplicates, dedupe in staging |
| `products` | product_id | ~33k | |
| `sellers` | seller_id | ~3k | |
| `geolocation` | zip_code (aggregated) | ~1M | Multiple rows per zip, aggregate |
| `product_category_translation` | product_category_name | 71 | Portuguese to English |

## Staging Models (STAGING Schema)

| Model | Grain | Key Transformations |
|-------|-------|---------------------|
| `stg_ecommerce__customers` | customer_id | Zip padding, city/state formatting |
| `stg_ecommerce__orders` | order_id | Timestamp casting, status validation |
| `stg_ecommerce__order_items` | (order_id, order_item_id) | Column renaming |
| `stg_ecommerce__order_payments` | (order_id, payment_sequential) | Payment type validation |
| `stg_ecommerce__order_reviews` | review_id | ROW_NUMBER deduplication |
| `stg_ecommerce__products` | product_id | Joins translation table |
| `stg_ecommerce__sellers` | seller_id | Zip padding, formatting |
| `stg_ecommerce__geolocation` | zip_code | GROUP BY with AVG(lat/lng) |

## Mart Models (MARTS Schema)

### Core Dimensions

| Model | Grain | Description |
|-------|-------|-------------|
| `dim_customers` | customer_unique_id | Customer attributes, segments |
| `dim_products` | product_id | Product attributes, categories |
| `dim_sellers` | seller_id | Seller attributes, performance |
| `dim_cohorts` | cohort_month | Acquisition cohort metrics |
| `dim_dates` | date | Date dimension (calendar) |

### Core Facts

| Model | Grain | Description |
|-------|-------|-------------|
| `fct_orders` | order_id | Order-level metrics |
| `fct_order_items` | (order_id, order_item_id) | Line-item detail |

### Customer Analytics

| Model | Grain | Description |
|-------|-------|-------------|
| `fct_rfm_segments` | customer_unique_id | RFM scoring (1-5) and segments |
| `fct_cohort_retention` | (cohort_month, period_number) | Retention rates by cohort |
| `fct_clv_customer` | customer_unique_id | Probabilistic CLV prediction |
| `fct_churn_risk` | customer_unique_id | Churn risk scoring |

### Finance Analytics

| Model | Grain | Description |
|-------|-------|-------------|
| `fct_daily_revenue` | date | Daily revenue aggregates |
| `fct_payment_analysis` | (payment_type, month) | Payment method performance |

### Marketing Analytics

| Model | Grain | Description |
|-------|-------|-------------|
| `fct_category_performance` | (category, month) | Category sales metrics |
| `fct_geo_performance` | (state, month) | Geographic performance |

## Useful Queries

### Check Table Sizes

```sql
SELECT
    table_schema,
    table_name,
    row_count,
    bytes / 1e6 as mb
FROM information_schema.tables
WHERE table_catalog = 'ECOMMERCE_RETAIL_DB_DEV'
ORDER BY row_count DESC;
```

### Check Recent Model Runs

```sql
SELECT
    query_text,
    start_time,
    total_elapsed_time / 1000 as seconds,
    rows_produced
FROM snowflake.account_usage.query_history
WHERE query_text ILIKE '%create%table%marts%'
ORDER BY start_time DESC
LIMIT 20;
```

### Profile a Table

```sql
-- Row count and column stats
SELECT
    COUNT(*) as rows,
    COUNT(DISTINCT customer_unique_id) as unique_customers,
    MIN(created_at) as earliest,
    MAX(created_at) as latest
FROM ECOMMERCE_RETAIL_DB_DEV.MARTS.dim_customers;
```

### Check for Duplicates

```sql
SELECT <grain_columns>, COUNT(*) as cnt
FROM <schema>.<table>
GROUP BY <grain_columns>
HAVING COUNT(*) > 1;
```

### Check NULL Distribution

```sql
SELECT
    COUNT(*) as total,
    COUNT(<column>) as non_null,
    COUNT(*) - COUNT(<column>) as null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(<column>)) / COUNT(*), 2) as null_pct
FROM <schema>.<table>;
```

## Data Quality Notes

### Known Issues

| Table | Issue | Handling |
|-------|-------|----------|
| `order_reviews` | Duplicate review_ids | ROW_NUMBER in staging |
| `geolocation` | Multiple lat/lng per zip | GROUP BY + AVG in staging |
| `orders` | 38 records with delivery < approval | Warn-only test |

### Date Range

- Orders: 2016-09-04 to 2018-10-17
- ~2 years of data
- Seasonal patterns visible

### Currency

- All monetary values in BRL (Brazilian Real)
- No currency conversion needed
