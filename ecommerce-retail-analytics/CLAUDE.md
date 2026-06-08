# CLAUDE.md

This file provides context for Claude Code when working on this project.

## Agentic Workflow

For structured development workflows, see **[.claude/AGENTS.md](.claude/AGENTS.md)**.

### Quick Reference: Skills

| Command | Purpose |
|---------|---------|
| `/develop` | Scaffold new models (SQL + YAML) |
| `/test` | Run tests & validate changes |
| `/deploy` | Commit & open PR |
| `/check-test-failures` | Diagnose production failures |
| `/refactor` | Optimize existing models |

### References (Load When Needed)

| Reference | Use For |
|-----------|---------|
| `.claude/references/dbt-conventions.md` | dbt best practices |
| `.claude/references/sql-conventions.md` | SQL style guide |
| `.claude/references/yaml-conventions.md` | YAML documentation |
| `.claude/references/data-warehouse.md` | Snowflake queries |

---

## Project Overview

E-Commerce Analytics project using dbt + Snowflake to analyze the Olist Brazilian E-Commerce dataset. The project implements RFM segmentation, cohort analysis, customer lifetime value, and other advanced SQL analytics patterns.

## Tech Stack

| Component | Tool | Version/Notes |
|-----------|------|---------------|
| Warehouse | Snowflake | DEV + PROD databases (Medallion architecture) |
| Transform | dbt | dbt-fusion 2.0.0-preview |
| CI/CD | GitHub Actions | Slim CI + Auto-deploy to Prod |
| Python | uv | Package manager |
| Visualization | Power BI | Connects to PROD.MARTS |

## Key Commands

```bash
# Navigate to dbt directory first (from project root)
cd dbt

# Run all models and tests
dbt build

# Run only models (no tests)
dbt run

# Run only tests
dbt test

# Run specific model
dbt run --select stg_ecommerce__orders

# Run staging models only
dbt run --select staging.*

# Check connection
dbt debug

# Generate documentation
dbt docs generate
dbt docs serve
```

## Project Structure

```
ecommerce-retail-analytics/          # Project root (within portfolio-projects repo)
├── CLAUDE.md                        # This file
├── README.md                        # Project overview
├── INSTALLATION.md                  # Setup guide
├── INSTRUCTIONS.md                  # Execution guide
├── .env                             # Environment variables (gitignored)
├── pyproject.toml                   # Python dependencies
│
├── .claude/                         # Claude Code configuration
│   ├── AGENTS.md                    # Agentic workflow guide
│   ├── skills/                      # Custom skills
│   └── references/                  # Reference documentation
│
├── docs/
│   ├── AWS-SNOWFLAKE-INTEGRATION-SETUP.md  # S3 integration guide
│   ├── CI-CD.md                            # CI/CD pipeline guide
│   └── SQL Analytical Patterns/            # SQL pattern study guides
│       ├── 01-rfm-analysis.md
│       ├── 02-cohort-analysis.md
│       ├── 03-customer-lifetime-value.md
│       └── 04-churn-indicators.md
│
├── snowflake/                       # Snowflake setup SQL scripts
│   ├── 1-roles-and-user-config.sql
│   ├── 2-warehouse-config.sql
│   ├── 3-database-schemas-config.sql
│   ├── 4-grant-access-config.sql
│   ├── 5-aws-storage-integration.sql  # S3 integration (ACCOUNTADMIN)
│   └── 6-stage-&-file-format.sql      # External stage + CSV format
│
├── scripts/
│   ├── download_kaggle_data.py
│   └── load_to_snowflake.py
│
├── data/                            # Downloaded CSV data (gitignored)
│
├── report/                          # Power BI PBIP files
│   ├── Ecommerce Analytics.Report/
│   └── Ecommerce Analytics.SemanticModel/
│
└── dbt/
    ├── dbt_project.yml
    ├── packages.yml                 # dbt_utils, audit_helper, codegen
    │
    ├── macros/
    │   ├── generate_schema_name.sql  # Custom schema naming
    │   └── generate_date_spine.sql   # Date spine generator for dim_dates
    │
    ├── seeds/
    │   └── rfm_segment_definitions.csv
    │
    └── models/
        ├── staging/                 # Clean and type raw data
        │   ├── _sources.yml
        │   ├── _stg_ecommerce_models.yml
        │   ├── _docs.md
        │   └── stg_ecommerce__*.sql
        │
        ├── intermediate/            # Join and enrich
        │   ├── _int_models.yml
        │   ├── int_orders_enriched.sql
        │   └── int_order_items_enriched.sql
        │
        └── marts/                   # Fact and dimension tables
            ├── core/                # Shared dimensions & facts
            │   ├── dim_customers.sql
            │   ├── dim_cohorts.sql
            │   ├── dim_dates.sql
            │   ├── dim_products.sql
            │   ├── dim_sellers.sql
            │   ├── fct_orders.sql
            │   └── fct_order_items.sql
            ├── customer/            # Customer analytics
            │   ├── fct_rfm_segments.sql
            │   ├── fct_cohort_retention.sql
            │   ├── fct_clv_customer.sql
            │   └── fct_churn_risk.sql
            ├── finance/             # Revenue & payment analytics
            │   ├── fct_daily_revenue.sql
            │   └── fct_payment_analysis.sql
            └── marketing/           # Category & geo analytics
                ├── fct_category_performance.sql
                └── fct_geo_performance.sql
```

## Snowflake Configuration

| Setting | Value |
|---------|-------|
| Warehouse | `ECOMMERCE_RETAIL_WH` |
| Role | `LEAD_DATA_ENGINEER_ROLE` |
| S3 Stage | `raw_ecommerce_s3_stage` |
| Storage Integration | `s3_ecommerce_integration` |

### AWS S3 Integration

For incremental data pipelines, Snowflake connects to S3 via storage integration:

```
S3 Bucket (ecommerce-retail-analytics-raw/)
    ↓
Snowflake Storage Integration (s3_ecommerce_integration)
    ↓
External Stage (raw_ecommerce_s3_stage)
    ↓
COPY INTO RAW tables
```

**Key Resources:**
- **S3 Bucket**: `ecommerce-retail-analytics-raw/` (folders per table)
- **IAM Role**: `snowflake-ecommerce-s3-role` (Snowflake assumes this)
- **IAM User**: `snowflake-data-engineer` (Airflow/Python uploads)

See `docs/AWS-SNOWFLAKE-INTEGRATION-SETUP.md` for complete setup guide.

### Medallion Architecture (2 Databases)

```
ECOMMERCE_RETAIL_DB_DEV (Bronze + Silver + Gold-Dev)
├── RAW           ← Bronze: Source data (single source of truth)
├── STAGING       ← Silver: Cleaned views (shared across environments)
├── INTERMEDIATE  ← Gold: Dev transformations
└── MARTS         ← Gold: Dev analytics tables

ECOMMERCE_RETAIL_DB_PROD (Gold-Prod Only)
├── INTERMEDIATE  ← Gold: Prod transformations
└── MARTS         ← Gold: Prod analytics (dashboards connect here)
```

| Database | Schemas | Purpose |
|----------|---------|---------|
| `ECOMMERCE_RETAIL_DB_DEV` | RAW, STAGING, INTERMEDIATE, MARTS | Development + Bronze/Silver layers |
| `ECOMMERCE_RETAIL_DB_PROD` | INTERMEDIATE, MARTS | Production Gold layer only |

### CI/CD Environment Mapping

| Environment | Database | What Gets Built |
|-------------|----------|-----------------|
| Local Dev | `_DEV` | All schemas |
| CI (PR) | `_DEV.CI_PR_xxx` | Isolated test schema |
| CD (Main) | `_PROD` | INTERMEDIATE + MARTS only |

Note: Mart models are organized into subfolders (`core/`, `customer/`, `finance/`, `marketing/`) for code organization, but all deploy to the single `MARTS` schema.

## dbt Conventions

### Schema Naming

The project uses a custom `generate_schema_name` macro that uses schema names directly (not appending to target schema):
- Models with `+schema: staging` → `STAGING` schema (not `RAW_staging`)

### Test Syntax (dbt-fusion 2.0)

Tests require the `arguments:` wrapper:

```yaml
# Correct syntax for column-level tests
columns:
  - name: order_id
    data_tests:
      - not_null
      - relationships:
          arguments:
            to: ref('stg_ecommerce__orders')
            field: order_id
  - name: payment_type
    data_tests:
      - accepted_values:
          arguments:
            values: ["credit_card", "boleto", "voucher"]

# Model-level tests (NOT column-level) - place at model level
models:
  - name: stg_ecommerce__order_items
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          arguments:
            combination_of_columns:
              - order_id
              - order_item_id
```

**Important**: `dbt_utils.unique_combination_of_columns` must be defined at the model level, not under a column. Placing it under a column causes a compilation error.

### Staging Model Pattern

All staging models follow this CTE pattern:

```sql
with source as (
    select * from {{ source('raw', 'table_name') }}
),

renamed as (
    select
        -- transformations here
    from source
)

select * from renamed
```

### Data Cleaning Conventions

- `trim()` on all string columns
- `initcap()` for city names
- `upper()` for state codes
- `lpad(..., 5, '0')` for zip codes
- `::date` or `::timestamp` for date conversions
- `::numeric(10,2)` for monetary values
- `ROW_NUMBER()` for deduplication when needed

## Source Tables (RAW Schema)

| Table | Primary Key | Notes |
|-------|-------------|-------|
| customers | customer_id | |
| orders | order_id | |
| order_items | (order_id, order_item_id) | Composite key |
| order_payments | (order_id, payment_sequential) | Composite key |
| order_reviews | review_id | Source has duplicates, dedupe in staging |
| products | product_id | |
| sellers | seller_id | |
| geolocation | zip_code | Multiple rows per zip, aggregate in staging |
| product_category_translation | product_category_name | |

## Staging Models

| Model | Key Transformations |
|-------|---------------------|
| stg_ecommerce__customers | Zip code padding, city/state formatting |
| stg_ecommerce__geolocation | GROUP BY zip_code with AVG(lat/lng) |
| stg_ecommerce__orders | Timestamp conversions, status validation |
| stg_ecommerce__order_items | Renamed shipping_deadline |
| stg_ecommerce__order_payments | Payment type validation |
| stg_ecommerce__order_reviews | ROW_NUMBER deduplication on review_id |
| stg_ecommerce__product_category_translation | Portuguese to English category translation |
| stg_ecommerce__products | Fixed typos, joins translation for English category |
| stg_ecommerce__sellers | Zip code padding, city/state formatting |

## Intermediate Models

| Model | Grain | Description |
|-------|-------|-------------|
| int_orders_enriched | order_id | Orders joined with customers, aggregated items/payments/reviews. Excludes canceled/unavailable orders. |
| int_order_items_enriched | (order_id, order_item_id) | Order items joined with orders, products, sellers. Includes English category names. |

## Mart Models

### Core (`marts/core/`)

| Model | Grain | Description |
|-------|-------|-------------|
| dim_customers | customer_unique_id | Customer dimension with attributes, location, and cohort assignment |
| dim_cohorts | cohort_month | Acquisition cohort dimension with cohort attributes (cohort_size for filtering) |
| dim_dates | date | Date dimension generated from order date range |
| dim_products | product_id | Product dimension with English category names |
| dim_sellers | seller_id | Seller dimension with location |
| fct_orders | order_id | Order fact table with metrics |
| fct_order_items | (order_id, order_item_id) | Order item fact table with product and seller details |

### Customer (`marts/customer/`)

| Model | Grain | Description |
|-------|-------|-------------|
| fct_rfm_segments | customer_unique_id | RFM scoring and segmentation with segment_id for sorting |
| fct_cohort_retention | (cohort_month, period_number) | Cohort retention rates, period revenue, and orders by period |
| fct_clv_customer | customer_unique_id | Customer Lifetime Value with predictions and segments |
| fct_churn_risk | customer_unique_id | Churn risk scoring and status (Active, Cooling, At Risk, Churned) |

### Finance (`marts/finance/`)

| Model | Grain | Description |
|-------|-------|-------------|
| fct_daily_revenue | date | Daily revenue aggregates |
| fct_payment_analysis | payment_type, month | Payment method performance by month |

### Marketing (`marts/marketing/`)

| Model | Grain | Description |
|-------|-------|-------------|
| fct_category_performance | category, month | Category sales metrics by month |
| fct_geo_performance | state, month | Geographic performance by month |

## Custom Macros

| Macro | Purpose |
|-------|---------|
| `generate_schema_name` | Uses schema names directly without appending to target |
| `get_order_date_spine` | Generates date spine from min/max order dates using dbt_utils.date_spine |

## Testing Strategy

- **Sources**: Basic integrity (not_null, unique on PKs)
- **Staging**: Full coverage (not_null, unique, relationships, accepted_values, composite key tests)
- **Intermediate**: Key validation (not_null, unique on grain, composite key tests)
- **Marts**: Primary key validation (not_null, unique on grain)

## Known Data Issues

1. **order_reviews.review_id**: Source has duplicates - handled with ROW_NUMBER in staging
2. **geolocation**: Multiple lat/lng per zip code - handled with GROUP BY and AVG
3. **Source column typos**: `product_name_lenght` → fixed to `name_length` in staging

## dbt Packages

- `dbt-labs/dbt_utils` - Utility macros and tests
- `dbt-labs/audit_helper` - Data auditing
- `dbt-labs/codegen` - Code generation helpers
