# Installation Guide

Complete setup guide for the E-Commerce Analytics platform.

## Prerequisites

- Python 3.12 (dbt doesn't support Python 3.13+ yet)
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Airflow)
- Snowflake account with key-pair authentication
- Kaggle account (for base dataset download)
- AWS account with S3 access (for data pipeline)
- Power BI Desktop (for dashboards)

---

## 1. Clone and Install

```bash
git clone https://github.com/musatouray/ecommerce-retail-pipeline.git
cd ecommerce-retail-pipeline

# Install Python 3.12 and dependencies
uv python install 3.12
uv venv --python 3.12
uv sync
```

---

## 2. Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

| Variable | Description |
|----------|-------------|
| `SNOWFLAKE_ACCOUNT` | Account identifier (e.g., `abc123.us-east-1`) |
| `SNOWFLAKE_USER` | Username |
| `SNOWFLAKE_DATABASE` | Dev database (`ECOMMERCE_RETAIL_DB_DEV`) |
| `SNOWFLAKE_DATABASE_PROD` | Prod database (`ECOMMERCE_RETAIL_DB_PROD`) |
| `SNOWFLAKE_WAREHOUSE` | Warehouse name |
| `SNOWFLAKE_SCHEMA` | Default schema (`RAW`) |
| `SNOWFLAKE_ROLE` | Role name |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Key passphrase (if encrypted) |
| `KAGGLE_USERNAME` | Kaggle username |
| `KAGGLE_KEY` | Kaggle API key |
| `AWS_ACCESS_KEY_ID` | AWS access key (for S3) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region |
| `S3_BUCKET` | S3 bucket name |
| `SLACK_WEBHOOK_URL` | Slack webhook (optional) |

**GitHub Secrets** (for CI/CD): Add the same Snowflake variables to repository Settings > Secrets > Actions.

---

## 3. Kaggle Dataset

```bash
# Place kaggle.json in ~/.kaggle/ (get from kaggle.com/settings)
uv run python scripts/download_kaggle_data.py
```

---

## 4. Snowflake Key-Pair Authentication

```bash
mkdir ~/.snowflake && cd ~/.snowflake

# Generate keys (without passphrase)
openssl genrsa -out rsa_key_temp.pem 2048
openssl pkcs8 -topk8 -inform PEM -in rsa_key_temp.pem -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
rm rsa_key_temp.pem
```

Assign public key in Snowflake:
```sql
-- Copy content of rsa_key.pub (without headers, as one line)
ALTER USER YOUR_USERNAME SET RSA_PUBLIC_KEY='your_public_key_here';
```

---

## 5. Configure dbt Profile

Create `~/.dbt/profiles.yml`:

```yaml
ecommerce_retail_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      threads: 4
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      database: ECOMMERCE_RETAIL_DB_DEV
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      schema: RAW
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      private_key_path: ~/.snowflake/rsa_key.p8
      private_key_passphrase: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE') }}"

    prod:
      type: snowflake
      threads: 4
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      database: ECOMMERCE_RETAIL_DB_PROD
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      schema: MARTS
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      private_key_path: ~/.snowflake/rsa_key.p8
      private_key_passphrase: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE') }}"
```

Verify connection:
```bash
cd dbt && dbt debug
```

---

## 6. Load Initial Data

```bash
uv run python scripts/load_to_snowflake.py
```

Verify in Snowflake:
```sql
USE ECOMMERCE_RETAIL_DB_DEV.RAW;
SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products;
```

---

## 7. Airflow Setup (Docker)

```bash
cd airflow
docker-compose build
docker-compose up -d
```

- **Web UI**: http://localhost:8080 (airflow/airflow)
- **DAGs**: `daily_synthetic_orders` (11 AM UTC), `backfill_synthetic_orders` (manual)

```bash
docker-compose down      # Stop
docker-compose logs -f   # View logs
```

---

## 8. AWS S3 Integration

Required for the incremental data pipeline. See **[docs/AWS-Snowflake-Integration-Guide.md](docs/AWS-Snowflake-Integration-Guide.md)** for the complete guide.

---

## 9. Power BI Connection

1. **Get Data** > **Snowflake**
2. **Server**: `your_account.snowflakecomputing.com`
3. **Warehouse**: `ECOMMERCE_RETAIL_WH`
4. Import from `ECOMMERCE_RETAIL_DB_PROD.MARTS`:
   - dim_customers, dim_dates, dim_products, dim_sellers
   - fct_orders, fct_order_items, fct_rfm_segments, fct_cohort_retention, fct_clv_customer

**Note**: Surrogate keys are 64-bit integers. After `dbt build --full-refresh`, refresh the semantic model to pick up new key values.

---

## Snowflake Architecture

```
ECOMMERCE_RETAIL_DB_DEV          ECOMMERCE_RETAIL_DB_PROD
├── RAW (Bronze)                 ├── INTERMEDIATE (Gold)
├── STAGING (Silver)       →     └── MARTS (Gold) ← Power BI
├── INTERMEDIATE (Gold)
└── MARTS (Gold)
```

- Bronze + Silver exist only in DEV (no duplication)
- PROD reads from DEV.STAGING via cross-database reference
- CI runs in isolated `CI_PR_xxx` schema
