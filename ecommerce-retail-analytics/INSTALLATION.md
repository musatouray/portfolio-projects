# Installation Guide

## Prerequisites

- Python 3.12 (dbt doesn't support Python 3.13+ yet)
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Snowflake account with key-pair authentication
- Kaggle account (for data download)
- AWS account with S3 access (for incremental data pipeline)

## Snowflake Architecture (Medallion Pattern)

This project uses a **2-database medallion architecture** for environment isolation:

### ECOMMERCE_RETAIL_DB_DEV (Development)

| Schema | Medallion Layer | Purpose |
|--------|-----------------|---------|
| `RAW` | Bronze | Source data from Kaggle CSV (immutable) |
| `STAGING` | Silver | Cleaned, typed, validated views |
| `INTERMEDIATE` | Gold | Joined and enriched views |
| `MARTS` | Gold | Fact and dimension tables (Dev) |

### ECOMMERCE_RETAIL_DB_PROD (Production)

| Schema | Medallion Layer | Purpose |
|--------|-----------------|---------|
| `INTERMEDIATE` | Gold | Reads from DEV.STAGING |
| `MARTS` | Gold | Production analytics (BI tools connect here) |

**Key Points:**
- Bronze + Silver layers exist only in DEV (no data duplication)
- PROD reads from DEV.STAGING via cross-database reference
- CI runs in isolated `CI_PR_xxx` schema in DEV database
- CD deploys Gold layer to PROD on merge to main

## 1. Clone the Repository

```bash
git clone https://github.com/musatouray/portfolio-projects.git
cd portfolio-projects/ecommerce-retail-analytics
```

## 2. Install Python 3.12 and Dependencies

```bash
# Install Python 3.12 via uv
uv python install 3.12

# Create virtual environment with Python 3.12
uv venv --python 3.12

# Install dependencies
uv sync
```

## 3. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
```

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier | `abc123.us-east-1` |
| `SNOWFLAKE_USER` | Your Snowflake username | `LEAD_DATA_ENGINEER` |
| `SNOWFLAKE_DATABASE` | Dev database name | `ECOMMERCE_RETAIL_DB_DEV` |
| `SNOWFLAKE_WAREHOUSE` | Compute warehouse name | `ECOMMERCE_RETAIL_WH` |
| `SNOWFLAKE_SCHEMA` | Default schema | `RAW` |
| `SNOWFLAKE_ROLE` | Your Snowflake role | `LEAD_DATA_ENGINEER_ROLE` |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Passphrase for private key (if encrypted) | |
| `KAGGLE_USERNAME` | Your Kaggle username | |
| `KAGGLE_KEY` | Your Kaggle API key | |
| `AWS_ACCESS_KEY_ID` | AWS IAM user access key (for S3 uploads) | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM user secret key | |
| `AWS_REGION` | AWS region for S3 bucket | `us-east-1` |
| `S3_BUCKET` | S3 bucket name for raw data | `ecommerce-retail-analytics-raw` |

### GitHub Secrets (for CI/CD)

Configure these in your repository settings (Settings > Secrets and variables > Actions):

| Secret | Description |
|--------|-------------|
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier |
| `SNOWFLAKE_USER` | Service account username |
| `SNOWFLAKE_ROLE` | Role with appropriate permissions |
| `SNOWFLAKE_WAREHOUSE` | Compute warehouse |
| `SNOWFLAKE_DATABASE_DEV` | Dev database (`ECOMMERCE_RETAIL_DB_DEV`) |
| `SNOWFLAKE_DATABASE_PROD` | Prod database (`ECOMMERCE_RETAIL_DB_PROD`) |
| `SNOWFLAKE_PRIVATE_KEY` | Private key content (paste full key including headers) |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Private key passphrase (if encrypted) |

## 4. Set Up Snowflake Key-Pair Authentication

Key-pair authentication is more secure than password authentication and bypasses MFA prompts.

### Generate RSA Key Pair

```bash
# Create directory for keys
mkdir ~/.snowflake
cd ~/.snowflake

# Generate private key (without passphrase)
openssl genrsa -out rsa_key_temp.pem 2048
openssl pkcs8 -topk8 -inform PEM -in rsa_key_temp.pem -out rsa_key.p8 -nocrypt
rm rsa_key_temp.pem

# Or with passphrase (more secure)
openssl genrsa -out rsa_key_temp.pem 2048
openssl pkcs8 -topk8 -inform PEM -in rsa_key_temp.pem -out rsa_key.p8 -v2 aes256
rm rsa_key_temp.pem

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

### Assign Public Key to Snowflake User

1. View your public key:
   ```bash
   cat ~/.snowflake/rsa_key.pub
   ```

2. Copy the key content (remove `-----BEGIN PUBLIC KEY-----` and `-----END PUBLIC KEY-----`, join into one line)

3. In Snowflake, run:
   ```sql
   ALTER USER YOUR_USERNAME SET RSA_PUBLIC_KEY='your_public_key_content_here';
   ```

4. Verify it worked:
   ```sql
   DESC USER YOUR_USERNAME;
   ```
   Look for `RSA_PUBLIC_KEY_FP` — it should show a fingerprint.

## 5. Configure dbt Profile

Create `~/.dbt/profiles.yml`:

```yaml
ecommerce_retail_analytics:
  target: dev
  outputs:
    # Development - uses ECOMMERCE_RETAIL_DB_DEV
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

    # Production - uses ECOMMERCE_RETAIL_DB_PROD (CD pipeline only)
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

**Note:** The staging models are configured to always deploy to DEV database via `dbt_project.yml`, regardless of target. Only Gold layer (intermediate + marts) goes to the target database.

## 6. Verify Connection

```bash
# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Load environment variables and test
cd dbt
dbt debug
```

You should see:
```
All checks passed!
```

## 7. AWS S3 Integration (Optional - for Incremental Pipeline)

If you plan to use the incremental data pipeline with Faker-generated data, you need to set up AWS S3 integration.

See **[docs/AWS-SNOWFLAKE-INTEGRATION-SETUP.md](docs/AWS-SNOWFLAKE-INTEGRATION-SETUP.md)** for the complete guide.

### Quick Overview

1. **Create S3 bucket**: `ecommerce-retail-analytics-raw` with folders per table
2. **Create IAM resources**:
   - Policy: `ecommerce-s3-pipeline-policy`
   - User: `snowflake-data-engineer` (for Airflow/Python uploads)
   - Role: `snowflake-ecommerce-s3-role` (for Snowflake to assume)
3. **Run Snowflake SQL scripts**:
   ```bash
   # In Snowflake worksheet (as ACCOUNTADMIN):
   snowflake/5-aws-storage-integration.sql

   # Then (as LEAD_DATA_ENGINEER_ROLE):
   snowflake/6-stage-&-file-format.sql
   ```
4. **Configure AWS trust relationship** using values from `DESC INTEGRATION s3_ecommerce_integration`

### Verify Integration

```sql
-- Test the stage connection
LIST @ECOMMERCE_RETAIL_DB_DEV.RAW.raw_ecommerce_s3_stage;
```

---

## Troubleshooting

### Python version errors
dbt currently supports Python 3.9 - 3.12. If you see import errors, ensure you're using Python 3.12:
```bash
uv venv --python 3.12
uv sync
```

### MFA required error
This means you need to set up key-pair authentication (Step 4) instead of password authentication.

### Environment variables not found
Make sure to load your `.env` file before running dbt:
```bash
# Linux/Mac
set -a && source .env && set +a

# Windows PowerShell
Get-Content .env | ForEach-Object {
  if ($_ -match '^([^#][^=]+)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
  }
}
```
