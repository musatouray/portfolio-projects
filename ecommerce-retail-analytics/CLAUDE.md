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

> **IMPORTANT FOR CLAUDE:** These are **project-specific skills** stored in `.claude/skills/<skill-name>/SKILL.md`. Do NOT use the `Skill` tool - it will fail with "Unknown skill". Instead, **read the SKILL.md file directly** and follow its instructions. For example, for `/deploy`, read `.claude/skills/deploy/SKILL.md`.

### References (Load When Needed)

| Reference | Use For |
|-----------|---------|
| `.claude/references/dbt-conventions.md` | dbt best practices |
| `.claude/references/sql-conventions.md` | SQL style guide |
| `.claude/references/yaml-conventions.md` | YAML documentation |
| `.claude/references/data-warehouse.md` | Snowflake queries |

---

## Project Overview

An end-to-end e-commerce analytics platform built on **Snowflake** and **dbt**. It features a fully automated data pipeline with **Airflow**, **AWS S3** for staging, **CI/CD with GitHub Actions**, real-time **Slack alerting**, advanced SQL analytical dbt modeling, and interactive **Power BI** dashboards. This project demonstrates production-grade data engineering practices—from raw data ingestion through dimensional modeling to business intelligence delivery.

### The Problem It Solves

Retail businesses generate massive transaction data but struggle to extract actionable insights. This platform transforms raw e-commerce data into analytics-ready models that answer critical business questions:

- *Which customers are most valuable and which are about to churn?*
- *How do customer cohorts retain and generate revenue over time?*
- *What products are frequently purchased together?*
- *What is the predicted lifetime value of each customer?*

### Technical Scope

**Data Warehouse (Snowflake)**
- Medallion architecture with Bronze (RAW), Silver (STAGING), and Gold (MARTS) layers
- Separate DEV and PROD databases with environment isolation
- Private key authentication and role-based access control
- External stage integration with AWS S3 for data loading

**Transformation Layer (dbt)**
- 20+ models across staging, intermediate, and marts layers
- Dimensional modeling with fact and dimension tables (Kimball methodology)
- Comprehensive test coverage: referential integrity, uniqueness, accepted values
- Custom macros for schema management and code generation
- Incremental processing patterns for large datasets

**Orchestration (Airflow)**
- Dockerized Airflow deployment with LocalExecutor
- Synthetic data generation simulating real-time business operations
- Multi-step DAGs: generate → S3 upload → Snowflake COPY → dbt build → validation
- Slack integration for failure alerts and success notifications
- Differentiated error handling (SKIP_FILE vs ABORT_STATEMENT)

**CI/CD (GitHub Actions)**
- Pull request validation with isolated test schemas
- Automated production deployment on merge
- Scheduled daily refreshes for production marts
- Slim CI using state comparison for modified models only

### Advanced Analytics Models

| Model | Pattern | Business Value |
|-------|---------|----------------|
| **RFM Segmentation** | 12-month rolling snapshots with Sankey migration tracking | Identify Champions, High-Value New, Slipping Whales, and One-and-Done Lost segments (optimized for single-purchase datasets) |
| **Cohort Retention** | Time-based cohort analysis with GRR/NRR metrics | Measure customer retention and revenue retention by acquisition month |
| **Customer Lifetime Value** | Predictive modeling with behavioral inputs | 12-month CLV projection using purchase frequency and monetary value |
| **Churn Risk Scoring** | Multi-factor risk assessment | Early warning system based on recency, frequency decline, and value trends |
| **Market Basket Analysis** | Product co-occurrence matrix | Cross-sell and bundle recommendations from purchase patterns |

### Power BI Dashboards

The reporting layer goes beyond basic metrics to deliver interactive analytical experiences:

- **Customer Analytics**: RFM segment distribution, migration flows, CLV distributions, churn risk heatmaps
- **Cohort Insights**: Retention curves, revenue cohort triangles, period-over-period comparisons
- **Geographic Analysis**: State-level performance maps, regional comparisons, delivery metrics
- **Time Intelligence**: Trend analysis, seasonality patterns, YoY/MoM growth calculations
- **Product Performance**: Category analysis, basket analysis visualization, seller rankings

All dashboards connect directly to Snowflake production marts with scheduled refresh aligned to the data pipeline.

### What Makes This Production-Grade

| Aspect | Implementation |
|--------|----------------|
| **Data Quality** | dbt tests on every model, row count validation, referential integrity checks |
| **Observability** | Slack alerts on failure, success summaries with metrics, Airflow task logging |
| **Environment Isolation** | DEV for development/testing, PROD for dashboards, CI schemas for PRs |
| **Automation** | Zero manual intervention—data flows from generation to dashboard daily |
| **Documentation** | dbt docs, implementation logs, comprehensive CLAUDE.md |
| **Version Control** | Git-based workflow with PR reviews and protected branches |

## Tech Stack

| Component | Tool | Version/Notes |
|-----------|------|---------------|
| Warehouse | Snowflake | DEV + PROD databases (Medallion architecture) |
| Transform | dbt | dbt-core 1.11.8, dbt-snowflake 1.11.4 |
| Orchestration | Airflow | 2.9.3 (Dockerized) |
| CI/CD | GitHub Actions | Slim CI + Scheduled CD |
| Storage | AWS S3 | Raw data staging |
| Python | uv | Package manager |
| Visualization | Power BI | Connects to PROD.MARTS |
| Notifications | Slack | Pipeline alerts |

---

## Data Pipeline Architecture

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DAILY PIPELINE (11 AM UTC)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Airflow DAG: daily_synthetic_orders                                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │ Generate │ → │ Upload   │ → │ COPY to  │ → │ Validate │ → │ dbt build│  │
│  │ Synthetic│   │ to S3    │   │ Snowflake│   │ + Slack  │   │ DEV      │  │
│  │ Data     │   │          │   │ RAW      │   │          │   │          │  │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCHEDULED CD (12 PM UTC)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GitHub Actions: dbt-cd.yml                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ dbt build PROD (reads from DEV.STAGING → writes to PROD.MARTS)       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              POWER BI                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Connects to ECOMMERCE_RETAIL_DB_PROD.MARTS                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Medallion Architecture

```
ECOMMERCE_RETAIL_DB_DEV (Bronze + Silver + Gold-Dev)
├── RAW           ← Bronze: Source data (Airflow loads here)
├── STAGING       ← Silver: Cleaned views (shared across environments)
├── INTERMEDIATE  ← Gold: Dev transformations
└── MARTS         ← Gold: Dev analytics tables

ECOMMERCE_RETAIL_DB_PROD (Gold-Prod Only)
├── INTERMEDIATE  ← Gold: Prod transformations
└── MARTS         ← Gold: Prod analytics (Power BI connects here)
```

### Pipeline Schedules

| Pipeline | Schedule (UTC) | Trigger | Target |
|----------|----------------|---------|--------|
| Daily Airflow DAG | 11:00 AM | Cron | DEV |
| CD Workflow | 12:00 PM | Cron + code merge | PROD |
| CI Workflow | On PR | Pull request | DEV (isolated schema) |

---

## Project Structure

```
ecommerce-retail-analytics/
├── CLAUDE.md                        # This file
├── README.md                        # Project overview
├── INSTALLATION.md                  # Complete setup guide
├── .env                             # Environment variables (gitignored)
├── .env.example                     # Environment template
├── pyproject.toml                   # Python dependencies
│
├── .claude/                         # Claude Code configuration
│   ├── AGENTS.md                    # Agentic workflow guide
│   ├── skills/                      # Custom skills (/deploy, /test, etc.)
│   └── references/                  # Reference documentation
│
├── airflow/                         # Airflow orchestration
│   ├── Dockerfile                   # Airflow + dbt image
│   ├── docker-compose.yml           # Service definitions
│   ├── requirements.txt             # Python dependencies (incl. dbt)
│   ├── dbt_profiles/                # dbt profiles for Airflow
│   │   └── profiles.yml             # Points to DEV database
│   ├── dags/
│   │   ├── daily_synthetic_orders.py    # Daily data pipeline
│   │   ├── backfill_synthetic_orders.py # Historical data backfill
│   │   └── utils/
│   │       └── slack_alerts.py      # Slack notification utilities
│   ├── logs/                        # Airflow logs (gitignored)
│   ├── plugins/                     # Custom Airflow plugins
│   └── config/                      # Airflow configuration
│
├── scripts/
│   ├── download_kaggle_data.py      # Download base dataset from Kaggle
│   ├── load_to_snowflake.py         # Initial data load
│   ├── synthetic_data_generator.py  # Generate synthetic orders
│   └── validate_synthetic_data.py   # Post-load validation
│
├── docs/
│   ├── AWS-SNOWFLAKE-INTEGRATION-SETUP.md
│   ├── CI-CD.md
│   ├── implementation-logs/         # Development history
│   │   ├── progress-ledger.md       # Task completion audit trail
│   │   └── airflow-dag-hardening/   # Implementation briefs & reports
│   ├── superpowers/
│   │   ├── specs/                   # Design specifications
│   │   └── plans/                   # Implementation plans
│   └── SQL Analytical Patterns/
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
│   ├── 5-aws-storage-integration.sql
│   └── 6-stage-&-file-format.sql
│
├── data/                            # Local data (gitignored)
│
├── report/                          # Power BI PBIP files
│   ├── Ecommerce Analytics.Report/
│   └── Ecommerce Analytics.SemanticModel/
│
└── dbt/
    ├── dbt_project.yml
    ├── packages.yml
    ├── macros/
    │   └── generate_schema_name.sql
    ├── seeds/
    │   └── rfm_segment_definitions.csv
    └── models/
        ├── staging/
        ├── intermediate/
        └── marts/
            ├── core/
            ├── customer/
            ├── finance/
            └── marketing/
```

---

## Airflow Pipeline

For setup instructions, see **[INSTALLATION.md](INSTALLATION.md#7-airflow-setup-docker)**.

### DAGs

| DAG | Purpose | Schedule |
|-----|---------|----------|
| `daily_synthetic_orders` | Generate daily synthetic data, load to Snowflake, run dbt DEV | 11 AM UTC |
| `backfill_synthetic_orders` | One-time historical data generation (manual trigger) | Manual |

### Daily DAG Tasks

```
generate_daily → upload_to_s3 → copy_* (4 tables) → validate_copy_results → dbt_build_dev → cleanup
```

1. **generate_daily**: Generate synthetic orders for previous day
2. **upload_to_s3**: Upload CSV files to S3 bucket
3. **copy_***: COPY INTO Snowflake RAW tables (parallel)
4. **validate_copy_results**: Query row counts, send Slack success message
5. **dbt_build_dev**: Run `dbt build` against DEV database
6. **cleanup**: Remove local CSV files

### Slack Notifications

- **Failure alerts**: Automatic on any task failure (`on_failure_callback`)
- **Success summary**: Row counts and duration after validation

Configure via `SLACK_WEBHOOK_URL` environment variable.

### Error Handling

| DAG | ON_ERROR Strategy | Rationale |
|-----|-------------------|-----------|
| Backfill | `SKIP_FILE` | Continue with good files, log bad ones |
| Daily | `ABORT_STATEMENT` | Fail fast, alert, investigate |

---

## CI/CD Workflows

### dbt CI (`dbt-ci.yml`)

- **Trigger**: Pull requests to main
- **Target**: DEV database (isolated CI schema)
- **Actions**: `dbt build --select state:modified+`

### dbt CD (`dbt-cd.yml`)

- **Triggers**:
  - Push to main (when `dbt/**` files change)
  - Daily schedule (12 PM UTC)
  - Manual dispatch
- **Target**: PROD database
- **Actions**: `dbt build` (full refresh available via manual trigger)

### Fabric Git Integration

Power BI reports are deployed to Microsoft Fabric via Git integration:

| Branch | Fabric Workspace | Purpose |
|--------|------------------|---------|
| `main` | (Dev workspace) | Development and testing |
| `fabric-prod` | Production workspace | End-user dashboards |

**Workflow:**
```
feature branch → PR → main → PR/merge → fabric-prod → Fabric auto-syncs
```

**Fabric Settings:**
- **Branch**: `fabric-prod`
- **Folder**: `ecommerce-retail-analytics/report`
- Fabric only syncs the `report/` folder (ignores dbt, airflow, scripts)

---

## Snowflake Configuration

| Setting | Value |
|---------|-------|
| Warehouse | `ECOMMERCE_RETAIL_WH` |
| Role | `LEAD_DATA_ENGINEER_ROLE` |
| S3 Stage | `raw_ecommerce_s3_stage` |
| Storage Integration | `s3_ecommerce_integration` |
| S3 Bucket | `ecommerce-retail-analytics-raw` |

For authentication setup (private key), see **[INSTALLATION.md](INSTALLATION.md#4-set-up-snowflake-key-pair-authentication)**.

---

## Synthetic Data Generation

The `synthetic_data_generator.py` script generates realistic e-commerce orders with US geography:

- **Orders**: 50-200 per day (configurable)
- **Order Items**: 1-5 items per order
- **Payments**: Credit card, boleto, voucher, debit card
- **Reviews**: Random scores and comments
- **Geography**: US states and cities

Uses existing reference data (customers, sellers, products, geolocation) from Snowflake RAW tables to ensure referential integrity.

**Data Timeline:**
- Historical base data: 2016-2018
- Synthetic extension: 2018-present (generated daily)

### Key Fix (June 2024)
The generator uses `customer_id` (not `customer_unique_id`) to maintain referential integrity with the ORDERS table.

---

## dbt Models

### Staging (Silver Layer)

| Model | Key Transformations |
|-------|---------------------|
| stg_ecommerce__customers | Zip code padding, city/state formatting |
| stg_ecommerce__geolocation | GROUP BY zip_code with AVG(lat/lng) |
| stg_ecommerce__orders | Timestamp conversions, status validation |
| stg_ecommerce__order_items | Renamed shipping_deadline |
| stg_ecommerce__order_payments | Payment type validation |
| stg_ecommerce__order_reviews | ROW_NUMBER deduplication |
| stg_ecommerce__products | Fixed typos, English category translation |
| stg_ecommerce__sellers | Zip code padding, city/state formatting |

### Marts (Gold Layer)

| Domain | Models |
|--------|--------|
| Core | dim_customers, dim_dates, dim_products, dim_sellers, fct_orders, fct_order_items |
| Customer | fct_rfm_segments, fct_cohort_retention, fct_clv_customer |
| Finance | fct_order_payments |
| Marketing | fct_market_basket |

---

## Surrogate Key Strategy

### Design Decision

Using Snowflake's native `HASH()` function for surrogate keys instead of `dbt_utils.generate_surrogate_key` for two reasons:

1. **Power BI memory optimization**: 8-byte integers compress significantly better than 32-character hex strings (~70% memory reduction on key columns)
2. **Snowflake-native**: This project is purpose-built for Snowflake; cross-platform portability isn't a requirement

**Tradeoff accepted**: Platform-specific implementation in exchange for substantial memory reduction in Power BI semantic models.

### Implementation

A custom macro `generate_int_surrogate_key` uses `MD5_NUMBER_LOWER64` for stable, deterministic hashing:

```sql
-- Usage (identical interface to dbt_utils.generate_surrogate_key)
{{ generate_int_surrogate_key(['order_id', 'product_id']) }}

-- Compiles to:
MD5_NUMBER_LOWER64(concat(coalesce(cast(order_id as varchar), ''), '-', coalesce(cast(product_id as varchar), '')))
```

### Why MD5_NUMBER_LOWER64 over HASH()

Snowflake's `HASH()` is **not guaranteed stable across releases**—the algorithm can change during Snowflake upgrades, silently breaking surrogate keys. `MD5_NUMBER_LOWER64` uses the standardized MD5 algorithm (RFC 1321) which will never change.

### Key Characteristics

| Aspect | Detail |
|--------|--------|
| Output type | BIGINT (64-bit signed integer) |
| Algorithm | MD5 lower 64 bits (standardized, version-stable) |
| Delimiter | Hyphen (`-`) between fields prevents collision |
| NULL handling | Coalesces to empty string (matches dbt_utils behavior) |
| Collision risk | Negligible at < 100M rows (~0.00027% probability) |

### Migration Notes

When deploying this change, run a **full refresh** to regenerate all surrogate keys:

```bash
dbt build --full-refresh --target prod
```

Power BI semantic model relationships must be rebuilt after refresh since all key values change.

---

## Key Commands

### dbt

```bash
cd dbt
dbt build                    # Run all models + tests
dbt run --select staging.*   # Run only staging models
dbt test                     # Run all tests
dbt docs generate && dbt docs serve  # Generate docs
```

### Airflow

See **[INSTALLATION.md](INSTALLATION.md#7-airflow-setup-docker)** for Docker commands.

### Git/Deployment

```bash
git checkout -b feature/name  # Create feature branch
git add . && git commit -m "feat: description"
git push -u origin feature/name
gh pr create                  # Create PR
gh pr merge --squash          # Merge after approval
```

### Promoting to Fabric Production

After merging to `main`, promote report changes to the Fabric production workspace:

```bash
git checkout fabric-prod
git merge main
git push
# Fabric workspace auto-syncs from fabric-prod branch
```

Or create a PR from `main` to `fabric-prod` for review before promoting.

---

## Testing Strategy

| Layer | Tests |
|-------|-------|
| Sources | not_null, unique on PKs |
| Staging | not_null, unique, relationships, accepted_values |
| Intermediate | not_null, unique on grain |
| Marts | not_null, unique on grain |

---

## Known Issues & Fixes

1. **order_reviews duplicates**: Handled with ROW_NUMBER in staging
2. **geolocation multiple coords**: Handled with GROUP BY + AVG
3. **customer_id vs customer_unique_id**: Generator uses customer_id for FK integrity
4. **Snowflake private key auth**: Use `private_key_file` (not `private_key_path`) in connection extras

---

## dbt Packages

- `dbt-labs/dbt_utils` - Utility macros and tests
- `dbt-labs/audit_helper` - Data auditing
- `dbt-labs/codegen` - Code generation helpers
