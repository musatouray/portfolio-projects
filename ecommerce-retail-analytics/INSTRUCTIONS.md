# Setup and Execution Instructions

Step-by-step guide to build the E-Commerce Analytics pipeline.

## Prerequisites

Before starting, ensure you have:

- [ ] Python 3.10 or higher installed
- [ ] A Snowflake account (free trial works)
- [ ] A Kaggle account
- [ ] Power BI Desktop installed (for visualization)
- [ ] Git installed

---

## Phase 1: Environment Setup

### 1.1 Install uv Package Manager

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1.2 Create Project Structure

```bash
mkdir ecommerce-retail-analytics
cd ecommerce-retail-analytics

# Create directory structure
mkdir -p scripts
mkdir -p data/raw
mkdir -p dbt_project/models/staging/ecommerce
mkdir -p dbt_project/models/intermediate
mkdir -p dbt_project/models/marts/core
mkdir -p dbt_project/models/marts/finance
mkdir -p dbt_project/models/marts/marketing
mkdir -p dbt_project/macros
mkdir -p dbt_project/tests
mkdir -p dbt_project/seeds
```

### 1.3 Initialize Python Project

Create `pyproject.toml`:

```toml
[project]
name = "ecommerce-retail-analytics"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "dbt-snowflake>=1.7.0",
    "kaggle>=1.6.0",
    "snowflake-connector-python>=3.6.0",
    "pandas>=2.0.0",
    "python-dotenv>=1.0.0",
]
```

Install dependencies:

```bash
uv sync
```

### 1.4 Create Environment File

Create `.env` file (never commit this):

```env
# Snowflake
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_ROLE=LEAD_DATA_ENGINEER_ROLE
SNOWFLAKE_WAREHOUSE=ECOMMERCE_RETAIL_WH
SNOWFLAKE_DATABASE=ECOMMERCE_RETAIL_DB_DEV
SNOWFLAKE_SCHEMA=RAW
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase  # if key is encrypted

# Kaggle (optional if using kaggle.json)
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
```

**Note:** Use key-pair authentication instead of password for security and CI/CD.

### 1.5 Create .gitignore

```gitignore
# Environment
.env
*.env.local

# Data
data/raw/*.csv
data/raw/*.zip

# Python
__pycache__/
.venv/
.uv/

# dbt
dbt_project/target/
dbt_project/dbt_packages/
dbt_project/logs/
dbt_project/profiles.yml
```

---

## Phase 2: Kaggle Setup

### 2.1 Get Kaggle API Credentials

1. Go to https://www.kaggle.com/settings
2. Scroll to "API" section
3. Click "Create New Token"
4. Download `kaggle.json`

### 2.2 Place Credentials

```bash
# Windows
mkdir %USERPROFILE%\.kaggle
move kaggle.json %USERPROFILE%\.kaggle\

# macOS/Linux
mkdir -p ~/.kaggle
mv kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### 2.3 Create Download Script

Create `scripts/download_kaggle_data.py`:

**What it should do:**
1. Authenticate with Kaggle API
2. Download dataset `olistbr/brazilian-ecommerce`
3. Extract to `data/raw/` folder
4. Print list of downloaded files

### 2.4 Run Download

```bash
uv run python scripts/download_kaggle_data.py
```

**Expected output:** 9 CSV files in `data/raw/`

---

## Phase 3: Snowflake Setup

### 3.1 Create Snowflake Resources (Medallion Architecture)

Run the SQL scripts in `ecommerce-retail-analytics/snowflake/` folder in order:

```bash
# Execute in Snowflake worksheet (in order):
1-roles-and-user-config.sql      # Create roles and service account
2-warehouse-config.sql           # Create compute warehouse
3-database-schemas-config.sql    # Create DEV + PROD databases (medallion setup)
4-grant-access-config.sql        # Grant permissions to both databases
5-aws-storage-integration.sql    # (Optional) S3 integration - requires ACCOUNTADMIN
6-stage-&-file-format.sql        # (Optional) External stage + CSV file format
```

Or run this SQL directly for the 2-database medallion architecture:

```sql
-- Create warehouse
CREATE WAREHOUSE IF NOT EXISTS ECOMMERCE_RETAIL_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- DEV Database (Bronze + Silver + Gold)
CREATE DATABASE IF NOT EXISTS ECOMMERCE_RETAIL_DB_DEV
    COMMENT = 'Development: Bronze (RAW) + Silver (STAGING) + Gold (INT/MARTS)';

USE DATABASE ECOMMERCE_RETAIL_DB_DEV;
CREATE SCHEMA IF NOT EXISTS RAW COMMENT = 'Bronze Layer - Raw source data';
CREATE SCHEMA IF NOT EXISTS STAGING COMMENT = 'Silver Layer - Cleaned and typed';
CREATE SCHEMA IF NOT EXISTS INTERMEDIATE COMMENT = 'Gold Layer - Joined models (Dev)';
CREATE SCHEMA IF NOT EXISTS MARTS COMMENT = 'Gold Layer - Fact/Dim tables (Dev)';

-- PROD Database (Gold Only)
CREATE DATABASE IF NOT EXISTS ECOMMERCE_RETAIL_DB_PROD
    COMMENT = 'Production: Gold layer only - BI tools connect here';

USE DATABASE ECOMMERCE_RETAIL_DB_PROD;
CREATE SCHEMA IF NOT EXISTS INTERMEDIATE COMMENT = 'Gold Layer - Joined models (Prod)';
CREATE SCHEMA IF NOT EXISTS MARTS COMMENT = 'Gold Layer - Fact/Dim tables (Prod)';
```

### 3.2 Create Data Loading Script

Create `scripts/load_to_snowflake.py`:

**What it should do:**
1. Connect to Snowflake using credentials from `.env`
2. For each CSV file in `data/raw/`:
   - Create a table based on CSV structure
   - Use PUT command to upload file to internal stage
   - Use COPY INTO to load data
3. Print row counts for verification

**Table name mapping:**
| CSV File | Table Name |
|----------|------------|
| olist_orders_dataset.csv | orders |
| olist_customers_dataset.csv | customers |
| olist_order_items_dataset.csv | order_items |
| olist_order_payments_dataset.csv | order_payments |
| olist_order_reviews_dataset.csv | order_reviews |
| olist_products_dataset.csv | products |
| olist_sellers_dataset.csv | sellers |
| olist_geolocation_dataset.csv | geolocation |
| product_category_name_translation.csv | product_category_translation |

### 3.3 Run Data Load

```bash
uv run python scripts/load_to_snowflake.py
```

### 3.4 Verify Data in Snowflake

```sql
USE ECOMMERCE_RETAIL_DB_DEV.RAW;
SELECT 'orders' as table_name, COUNT(*) as row_count FROM orders
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products;

-- Verify medallion architecture setup
SELECT
    'DEV' as database_name, 'Bronze' as layer, 'RAW' as schema_name, COUNT(*) as table_count
FROM ECOMMERCE_RETAIL_DB_DEV.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'RAW'
UNION ALL
SELECT 'DEV', 'Silver', 'STAGING', COUNT(*)
FROM ECOMMERCE_RETAIL_DB_DEV.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'STAGING'
UNION ALL
SELECT 'PROD', 'Gold', 'MARTS', COUNT(*)
FROM ECOMMERCE_RETAIL_DB_PROD.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'MARTS';
```

---

## Phase 3.5: AWS S3 Integration (Optional)

If you plan to use the incremental data pipeline with generated data (Faker/Airflow), set up AWS S3 integration. Skip this phase if you're only using the static Kaggle dataset.

> **Full guide**: See `docs/AWS-SNOWFLAKE-INTEGRATION-SETUP.md` for detailed instructions.

### 3.5.1 AWS Setup

1. **Create S3 bucket**: `ecommerce-retail-analytics-raw`
2. **Create folder structure** for tables that will receive incremental data:
   ```
   orders/
   order_items/
   order_payments/
   order_reviews/
   customers/
   ```
3. **Create IAM resources**:
   - Policy: `ecommerce-s3-pipeline-policy` (S3 read/write permissions)
   - User: `snowflake-data-engineer` (for Airflow/Python to upload files)
   - Role: `snowflake-ecommerce-s3-role` (for Snowflake to assume)

### 3.5.2 Snowflake Storage Integration

Run `5-aws-storage-integration.sql` as **ACCOUNTADMIN**:

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE STORAGE INTEGRATION s3_ecommerce_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<your-account-id>:role/snowflake-ecommerce-s3-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://ecommerce-retail-analytics-raw/');

-- Get values for AWS trust policy
DESC INTEGRATION s3_ecommerce_integration;
-- Copy: STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID
```

### 3.5.3 Configure AWS Trust Relationship

Update the IAM role's trust policy with values from `DESC INTEGRATION`:
- **Principal**: Use `STORAGE_AWS_IAM_USER_ARN` (Snowflake's IAM user)
- **ExternalId**: Use `STORAGE_AWS_EXTERNAL_ID`

### 3.5.4 Create Stage and File Format

Run `6-stage-&-file-format.sql` as **LEAD_DATA_ENGINEER_ROLE**:

```sql
USE ROLE LEAD_DATA_ENGINEER_ROLE;
USE DATABASE ECOMMERCE_RETAIL_DB_DEV;
USE SCHEMA RAW;

CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  NULL_IF = ('NULL', 'null', '')
  EMPTY_FIELD_AS_NULL = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"';

CREATE OR REPLACE STAGE raw_ecommerce_s3_stage
  STORAGE_INTEGRATION = s3_ecommerce_integration
  URL = 's3://ecommerce-retail-analytics-raw/'
  FILE_FORMAT = csv_format;
```

### 3.5.5 Verify Integration

```sql
-- Should list files in S3 bucket (empty is OK if no files uploaded yet)
LIST @raw_ecommerce_s3_stage;

-- Test upload from terminal, then verify in Snowflake
-- aws s3 cp test.csv s3://ecommerce-retail-analytics-raw/orders/test.csv
-- LIST @raw_ecommerce_s3_stage/orders/;
```

---

## Phase 4: dbt Project Setup

### 4.1 Create dbt_project.yml

Create `dbt_project/dbt_project.yml`:

```yaml
name: 'ecommerce_analytics'
version: '1.0.0'
config-version: 2

profile: 'ecommerce_analytics'

model-paths: ["models"]
test-paths: ["tests"]
macro-paths: ["macros"]
seed-paths: ["seeds"]

models:
  ecommerce_analytics:
    staging:
      +schema: staging
      +materialized: view
    intermediate:
      +schema: intermediate
      +materialized: view
    marts:
      +schema: marts
      +materialized: table
```

### 4.2 Create profiles.yml

Create `~/.dbt/profiles.yml` (or `dbt_project/profiles.yml`):

```yaml
ecommerce_retail_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      database: ECOMMERCE_RETAIL_DB_DEV
      schema: RAW
      threads: 4
      private_key_path: ~/.snowflake/rsa_key.p8
      private_key_passphrase: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE') }}"

    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      database: ECOMMERCE_RETAIL_DB_PROD
      schema: MARTS
      threads: 4
      private_key_path: ~/.snowflake/rsa_key.p8
      private_key_passphrase: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE') }}"
```

**Note:** Use key-pair authentication (recommended) instead of password for security and CI/CD compatibility.

### 4.3 Create packages.yml

Create `dbt_project/packages.yml`:

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: ">=1.1.0"
```

### 4.4 Test Connection

```bash
cd dbt_project
uv run dbt debug
uv run dbt deps
```

---

## Phase 5: Build dbt Models

### 5.1 Create Sources

Create `dbt_project/models/staging/ecommerce/_sources.yml`:

**Define sources for all 9 RAW tables with:**
- Database: `ECOMMERCE_RETAIL_DB_DEV` (Bronze layer - single source of truth)
- Schema: `RAW`
- Column descriptions

### 5.2 Create Staging Models

Create one staging model per source table:

| Model | Purpose |
|-------|---------|
| `stg_ecommerce__orders.sql` | Standardize timestamps, clean status |
| `stg_ecommerce__customers.sql` | Clean city/state names |
| `stg_ecommerce__order_items.sql` | Cast prices, add total_item_value |
| `stg_ecommerce__order_payments.sql` | Standardize payment types |
| `stg_ecommerce__order_reviews.sql` | Parse timestamps |
| `stg_ecommerce__products.sql` | Join with translation table |
| `stg_ecommerce__sellers.sql` | Clean city/state names |
| `stg_ecommerce__geolocation.sql` | Deduplicate by zip code |

### 5.3 Create Intermediate Models

| Model | Purpose |
|-------|---------|
| `int_orders_enriched.sql` | Join orders with customers, aggregate items, payments, reviews |
| `int_order_items_enriched.sql` | Join items with products, sellers, orders |

### 5.4 Create Mart Models

**Core:**
| Model | Purpose |
|-------|---------|
| `fct_orders.sql` | Order fact table with all metrics |
| `dim_customers.sql` | Customer dimension with lifetime value, segments |
| `dim_products.sql` | Product dimension with categories |
| `dim_sellers.sql` | Seller dimension with tiers |

**Finance:**
| Model | Purpose |
|-------|---------|
| `fct_daily_revenue.sql` | Daily revenue aggregates |
| `fct_payment_analysis.sql` | Payment method performance |

**Marketing:**
| Model | Purpose |
|-------|---------|
| `fct_category_performance.sql` | Category sales by month |
| `fct_geo_performance.sql` | Geographic performance |

### 5.5 Add Tests

Create `_schema.yml` files with:
- `unique` tests on primary keys
- `not_null` tests on required fields
- `accepted_values` for enums (order_status, payment_type)
- `relationships` for foreign keys

### 5.6 Run dbt

```bash
cd dbt_project

# Run all models
uv run dbt run

# Run tests
uv run dbt test

# Generate docs
uv run dbt docs generate
uv run dbt docs serve
```

---

## Phase 6: Power BI Connection

### 6.1 Connect to Snowflake (Production)

1. Open Power BI Desktop
2. Get Data → Snowflake
3. Server: `your_account.snowflakecomputing.com`
4. Warehouse: `ECOMMERCE_RETAIL_WH`
5. Sign in with Snowflake credentials

**Important:** Connect to the **PROD** database for production dashboards.

### 6.2 Import Tables

From `ECOMMERCE_RETAIL_DB_PROD.MARTS` schema:
- dim_customers
- dim_dates
- dim_products
- dim_sellers
- fct_orders
- fct_daily_revenue
- fct_payment_analysis
- fct_category_performance
- fct_geo_performance

### 6.3 Create Relationships

Connect dimension tables to fact tables:
- dim_customers → fct_orders (customer_unique_id)
- dim_products → fct_orders (via fct_order_items if needed)
- dim_sellers → fct_orders (via fct_order_items if needed)

### 6.4 Build Dashboards

**Suggested visuals:**
- Revenue trend (line chart by date)
- Revenue by state (map)
- Top categories (bar chart)
- Payment method distribution (pie chart)
- Delivery performance (KPI cards)
- Customer segments (donut chart)

---

## Phase 7: CI/CD Setup (GitHub Actions)

### 7.1 Branch Protection

Configure branch protection rules in GitHub (Settings > Branches):
- Require pull request reviews before merging
- Require status checks to pass (dbt-build job)
- Require branches to be up to date

### 7.2 GitHub Secrets

Configure these secrets (Settings > Secrets and variables > Actions):

| Secret | Description |
|--------|-------------|
| `SNOWFLAKE_ACCOUNT` | Account identifier |
| `SNOWFLAKE_USER` | Service account username |
| `SNOWFLAKE_ROLE` | Role with permissions |
| `SNOWFLAKE_WAREHOUSE` | Compute warehouse |
| `SNOWFLAKE_DATABASE_DEV` | `ECOMMERCE_RETAIL_DB_DEV` |
| `SNOWFLAKE_DATABASE_PROD` | `ECOMMERCE_RETAIL_DB_PROD` |
| `SNOWFLAKE_PRIVATE_KEY` | Private key content (full key with headers) |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Key passphrase (if encrypted) |

### 7.3 CI/CD Workflow

The project includes two GitHub Actions workflows:

**CI Pipeline (`.github/workflows/dbt-ci.yml`)**:
- Triggers on PR to main branch
- Runs SQLFluff linting (lenient mode)
- Runs Slim CI (only modified models + downstream)
- Tests in isolated `CI_PR_xxx` schema
- Comments results on PR

**CD Pipeline (`.github/workflows/dbt-cd.yml`)**:
- Triggers on merge to main branch
- Deploys to PROD database
- Generates documentation
- Saves production manifest for Slim CI

---

## Useful Commands Reference

```bash
# Download data
uv run python scripts/download_kaggle_data.py

# Load to Snowflake
uv run python scripts/load_to_snowflake.py

# dbt commands (run from dbt_project/)
uv run dbt debug          # Test connection
uv run dbt deps           # Install packages
uv run dbt run            # Run all models
uv run dbt run --select staging   # Run staging only
uv run dbt run --select +fct_orders  # Run model with dependencies
uv run dbt test           # Run all tests
uv run dbt docs generate  # Generate documentation
uv run dbt docs serve     # View documentation
```

---

## Troubleshooting

### Kaggle API errors
- Ensure `kaggle.json` is in the correct location
- Check file permissions (chmod 600 on Linux/Mac)

### Snowflake connection errors
- Verify account name format: `account.region` (e.g., `abc123.us-east-1`)
- Check warehouse is not suspended
- Verify role has proper permissions

### dbt errors
- Run `dbt debug` to verify connection
- Check that profiles.yml is in `~/.dbt/` or project folder
- Ensure environment variables are loaded (restart terminal after `.env` changes)

### Power BI connection issues
- Use the full Snowflake URL: `account.snowflakecomputing.com`
- Ensure your IP is whitelisted if using network policies

### AWS S3 integration errors
- `sts:AssumeRole` error: Update IAM role trust policy with `STORAGE_AWS_IAM_USER_ARN` from `DESC INTEGRATION`
- `AccessDenied` on `aws s3 ls`: Use explicit bucket path `aws s3 ls s3://your-bucket/`
- `LIST @stage` returns empty: This is OK if no files uploaded yet - not an error
- See `docs/AWS-SNOWFLAKE-INTEGRATION-SETUP.md` for detailed troubleshooting
