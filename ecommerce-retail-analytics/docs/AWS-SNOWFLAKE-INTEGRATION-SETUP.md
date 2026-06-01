# AWS + Snowflake Integration Setup Guide

Complete step-by-step reference for connecting Snowflake to AWS S3 for the incremental data pipeline.

## Architecture Overview

```
Faker (Python)
    ↓
AWS S3 Bucket          ← your storage layer
    ↓
Snowflake External Stage  ← trust via IAM Role (not user keys)
    ↓
COPY INTO RAW Schema   ← Snowflake ingestion
    ↓
dbt incremental models ← transformation layer
```

The key security concept: Snowflake uses its **own** AWS IAM user to assume **your** IAM Role via a trust relationship. Your personal IAM user keys are only used for uploading files (Airflow → S3). Snowflake never touches your IAM user keys.

---

## Part 1: AWS S3 Setup

### 1.1 Create the S3 Bucket

- Go to **S3 → Create bucket**
- Bucket name: `ecommerce-retail-analytics-raw`
- Region: your preferred region (e.g. `us-east-1`)
- Block all public access: **ON** (default, keep it)
- Versioning: optional
- Click **Create bucket**

### 1.2 Create Folder Structure

Inside the bucket, create one folder per table that will receive generated data:

```
ecommerce-retail-analytics-raw/
├── orders/
├── order_items/
├── order_payments/
├── order_reviews/
└── customers/
```

**Skip these** — static catalog tables already loaded, won't change:
- `products/`, `sellers/`, `geolocation/`, `product_category_translation/`

---

## Part 2: AWS IAM Setup

Two IAM resources are needed:
1. **IAM Policy** — defines what S3 actions are allowed
2. **IAM User** — used by Airflow/Python to upload files to S3
3. **IAM Role** — used by Snowflake to read files from S3 (trust relationship)

### 2.1 Create the IAM Policy

- Go to **IAM → Policies → Create policy**
- Choose **JSON** tab and paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::ecommerce-retail-analytics-raw",
        "arn:aws:s3:::ecommerce-retail-analytics-raw/*"
      ]
    }
  ]
}
```

- Name: `ecommerce-s3-pipeline-policy`
- Click **Create policy**

### 2.2 Create the IAM User (for Airflow/Python uploads)

- Go to **IAM → Users → Create user**
- Username: `snowflake-data-engineer`
- **Do NOT** check "Provide user access to the AWS Management Console"
- Click **Next**
- Select **"Attach policies directly"**
- Search for and select `ecommerce-s3-pipeline-policy`
- Click **Next → Create user**

### 2.3 Generate Access Keys for the IAM User

- Click into the user → **Security credentials** tab
- Scroll to **Access keys → Create access key**
- Use case: **"Application running outside AWS"**
- Click through the warning → **Next → Create access key**
- ⚠️ **Download the CSV immediately — secret key shown only once**

Save to your `.env`:
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET=ecommerce-retail-analytics-raw
```

### 2.4 Configure AWS CLI and Verify

```bash
pip install awscli
aws configure
# Enter: Access Key ID, Secret Access Key, region, output format (json)
```

Test all three operations:
```bash
# List bucket (NOT aws s3 ls — that requires ListAllMyBuckets which is intentionally denied)
aws s3 ls s3://ecommerce-retail-analytics-raw/

# Upload test
echo "test" > test.txt
aws s3 cp test.txt s3://ecommerce-retail-analytics-raw/orders/test.txt

# Delete test
aws s3 rm s3://ecommerce-retail-analytics-raw/orders/test.txt
```

All three should succeed. `aws s3 ls` (without a path) will return `AccessDenied` — this is expected and correct; the policy only grants access to the specific bucket.

---

## Part 3: Snowflake Storage Integration

### 3.1 Create the Storage Integration

Run as `ACCOUNTADMIN` in Snowflake:

```sql
CREATE OR REPLACE STORAGE INTEGRATION s3_ecommerce_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::492751140572:role/snowflake-ecommerce-s3-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://ecommerce-retail-analytics-raw/');
```

> Note: `492751140572` is your AWS account ID. The role doesn't need to exist yet — you'll create it in the next step.

### 3.2 Get Snowflake's IAM Values

```sql
DESC INTEGRATION s3_ecommerce_integration;
```

From the output, copy these two values — you'll need them to configure the AWS trust policy:

| Property | Description | Example |
|----------|-------------|---------|
| `STORAGE_AWS_IAM_USER_ARN` | Snowflake's own IAM user that will assume your role | `arn:aws:iam::379195789461:user/17pi1000-s` |
| `STORAGE_AWS_EXTERNAL_ID` | Security token to prevent confused deputy attacks | `ABC123_SFCRole=2_xxxx=` |

> ⚠️ **Important**: The account ID in `STORAGE_AWS_IAM_USER_ARN` (e.g. `379195789461`) is **Snowflake's** AWS account — not yours. This is the identity you must trust in AWS.

---

## Part 4: AWS IAM Role (for Snowflake)

### 4.1 Create the Role

- Go to **IAM → Roles → Create role**
- Trusted entity type: **AWS account**
- Select **"Another AWS account"**
- Account ID: the account number from `STORAGE_AWS_IAM_USER_ARN` (digits after `iam::`)
  - e.g. `379195789461` (Snowflake's account — not your account)
- Check **"Require external ID"**
- External ID: paste your `STORAGE_AWS_EXTERNAL_ID` value
- Click **Next**
- Attach `ecommerce-s3-pipeline-policy`
- Role name: `snowflake-ecommerce-s3-role`
- Click **Create role**

### 4.2 Verify the Trust Policy

After creation, click into the role → **Trust relationships** tab. It should look like:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::379195789461:user/17pi1000-s"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<your-STORAGE_AWS_EXTERNAL_ID>"
        }
      }
    }
  ]
}
```

> If the `STORAGE_AWS_IAM_USER_ARN` you got from Snowflake doesn't match what's in the trust policy, the `AssumeRole` call will fail. This was the fix applied during setup — Snowflake's IAM user ARN must be in the Principal, not your personal IAM user ARN.

---

## Part 5: Snowflake Stage and File Format

Run in `ECOMMERCE_RETAIL_DB_DEV.RAW`:

```sql
USE DATABASE ECOMMERCE_RETAIL_DB_DEV;
USE SCHEMA RAW;

-- File format for CSV files generated by Faker/pandas
CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  NULL_IF = ('NULL', 'null', '')
  EMPTY_FIELD_AS_NULL = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"';  -- handles quoted strings from pandas

-- External stage pointing to S3 via the storage integration
CREATE OR REPLACE STAGE raw_ecommerce_s3_stage
  STORAGE_INTEGRATION = s3_ecommerce_integration
  URL = 's3://ecommerce-retail-analytics-raw/'
  FILE_FORMAT = csv_format;
```

---

## Part 6: Verification

### End-to-end test

```bash
# 1. Upload a test file from terminal
echo "test_col1,test_col2
val1,val2" > test.csv
aws s3 cp test.csv s3://ecommerce-retail-analytics-raw/orders/test.csv
```

```sql
-- 2. Verify Snowflake can see it
LIST @raw_ecommerce_s3_stage;
-- Expected: s3://ecommerce-retail-analytics-raw/orders/test.csv

-- 3. Clean up
REMOVE @raw_ecommerce_s3_stage/orders/test.csv;
```

```bash
# 4. Confirm deletion
aws s3 ls s3://ecommerce-retail-analytics-raw/orders/
# Expected: empty
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `not authorized to perform: sts:AssumeRole` | Wrong IAM user ARN in trust policy | Update trust policy with `STORAGE_AWS_IAM_USER_ARN` from `DESC INTEGRATION` |
| `Query produced no results` on `LIST` | No files in bucket | This is success — upload a file and retry |
| `AccessDenied` on `aws s3 ls` (no path) | `ListAllMyBuckets` not in policy | Use `aws s3 ls s3://your-bucket/` with explicit path |
| `STORAGE_ALLOWED_LOCATIONS` error | File path outside allowed prefix | Ensure S3 URL in stage matches `STORAGE_ALLOWED_LOCATIONS` |

---

## Summary: What Each Resource Does

| Resource | Where | Purpose |
|----------|-------|---------|
| `ecommerce-retail-analytics-raw` | AWS S3 | Stores generated CSV files |
| `ecommerce-s3-pipeline-policy` | AWS IAM | Defines S3 permissions |
| `snowflake-data-engineer` (user) | AWS IAM | Airflow/Python uses this to upload files |
| `snowflake-ecommerce-s3-role` | AWS IAM | Snowflake assumes this role to read from S3 |
| `s3_ecommerce_integration` | Snowflake | Trust bridge between Snowflake and AWS |
| `csv_format` | Snowflake RAW | Defines how CSV files are parsed |
| `raw_ecommerce_s3_stage` | Snowflake RAW | Named pointer to S3 bucket via integration |
