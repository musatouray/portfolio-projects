# E-Commerce Analytics

An advanced SQL analytics project demonstrating production-grade data modeling patterns including RFM segmentation, cohort analysis, customer lifetime value, and funnel optimization — built with dbt, Snowflake, and Power BI.

## Overview

This project builds a complete analytics pipeline for the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle, containing 100k orders from Brazilian marketplaces (2016-2018).

Beyond basic reporting, this project showcases **advanced SQL patterns** used by data teams at top companies to drive real business decisions — customer segmentation, revenue attribution, churn prediction, and operational optimization.

## Key Analytics Questions

### Customer Segmentation (RFM Analysis)
- How can we segment customers into actionable groups (Champions, At-Risk, Lost) based on purchase behavior?
- Which customer segments should marketing prioritize for retention vs. re-activation campaigns?
- What is the revenue contribution of each RFM segment?

### Customer Lifetime Value (CLV)
- What is the predicted lifetime value of customers acquired this quarter?
- How does CLV vary across customer segments and acquisition channels?
- Which customer cohorts have the highest ROI potential?

### Pareto Analysis (80/20 Rule)
- Which 20% of products generate 80% of revenue?
- Which customers drive the majority of sales volume?
- What percentage of sellers account for most marketplace GMV?

### Funnel & Conversion Analysis
- What is the conversion rate from order placement to delivery confirmation?
- Where are the biggest drop-offs in the customer journey?
- How does review submission rate correlate with delivery performance?

### Cohort Analysis
- How does purchasing behavior differ between monthly acquisition cohorts?
- What is the retention curve for customers acquired in each quarter?
- Do newer cohorts show improving or declining engagement trends?

### Churn Prediction Indicators
- Which customers haven't purchased in 90+ days but were previously active?
- What behavioral signals indicate a customer is at risk of churning?
- What is our customer reactivation rate after dormancy?

### Market Basket Analysis
- Which products are frequently purchased together?
- What cross-sell opportunities exist based on co-purchase patterns?
- How can we optimize product bundling recommendations?

### Time Intelligence & Trends
- What is the month-over-month and year-over-year revenue growth?
- How do 7-day and 30-day moving averages reveal sales trends?
- What seasonal patterns exist in purchasing behavior?

### Seller Performance Scoring
- How can we rank sellers using a composite score (delivery time, reviews, volume)?
- Which sellers consistently underperform on delivery estimates?
- What is the correlation between seller ratings and repeat purchases?

### Geographic Performance
- Which regions have the highest average order value?
- How does delivery performance vary by customer location?
- Where are the untapped market opportunities?

## Advanced SQL Patterns

| Pattern | Business Value | Key SQL Features |
|---------|----------------|------------------|
| RFM Analysis | Customer segmentation | `NTILE()`, `CASE WHEN` scoring |
| Pareto Analysis | Focus on high-impact items | `SUM() OVER`, cumulative percentages |
| Customer Lifetime Value | Revenue forecasting | Cohort averages, predictive aggregations |
| Funnel Analysis | Conversion optimization | `COUNT(CASE WHEN...)`, stage ratios |
| Cohort Analysis | Retention tracking | `DATE_TRUNC`, cohort pivots |
| Market Basket | Cross-sell opportunities | Self-joins, co-occurrence matrices |
| Churn Indicators | Proactive retention | `DATEDIFF`, `LAG()`, behavioral flags |
| Time Intelligence | Trend analysis | `LAG()`, moving averages, YoY/MoM |
| Seller Scoring | Vendor management | `PERCENT_RANK()`, weighted composites |
| Geo Performance | Regional strategy | Location-based aggregations |

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    Kaggle    │      │  Snowflake   │      │     dbt      │      │   Power BI   │
│   (Source)   │─────▶│  (Warehouse) │─────▶│ (Transform)  │─────▶│   (Visualize)│
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
     CSV via           2-Database            GitHub Actions       Dashboards &
    Kaggle API         Medallion              CI/CD                Reports
```

### Medallion Architecture (2-Database Pattern)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MEDALLION + ENVIRONMENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ECOMMERCE_RETAIL_DB_DEV                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ BRONZE (RAW)          │ Source data lands here (CSV from Kaggle)       │   │
│   ├───────────────────────┼─────────────────────────────────────────────────┤   │
│   │ SILVER (STAGING)      │ Cleaned views ─────────────────────────────┐   │   │
│   ├───────────────────────┼────────────────────────────────────────────│───┤   │
│   │ GOLD (INT + MARTS)    │ Dev analytics                              │   │   │
│   └───────────────────────┴────────────────────────────────────────────│───┘   │
│                                                                         │       │
│   ECOMMERCE_RETAIL_DB_PROD                                              │       │
│   ┌───────────────────────┬────────────────────────────────────────────│───┐   │
│   │ GOLD (INT + MARTS)    │ Prod analytics  ◄───────────────────────────┘   │   │
│   │                       │ (reads from DEV.STAGING)                        │   │
│   └───────────────────────┴─────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- **Bronze + Silver in DEV only** - No data duplication, cost efficient
- **Gold layer separated** - Dev and Prod environments isolated
- **Cross-database reference** - PROD reads from DEV.STAGING (single source of truth)
- **CI/CD with GitHub Actions** - Automated testing and deployment

### Data Flow

1. **Extract**: Download CSV files from Kaggle using the Kaggle API
2. **Load**: Ingest raw CSV data into Snowflake's Bronze layer (`DEV.RAW`)
3. **Transform**: Use dbt to build layered transformations:
   - **Bronze (RAW)**: Raw source data, immutable
   - **Silver (STAGING)**: Cleaned, typed, validated views
   - **Gold (INT + MARTS)**: Business aggregates, analytics-ready tables
4. **CI/CD**: GitHub Actions validates PRs and deploys to production
5. **Visualize**: Connect Power BI to `PROD.MARTS` for dashboards

## Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Source | Kaggle API | Download e-commerce dataset |
| Warehouse | Snowflake | Cloud data storage and compute |
| Transform | dbt | SQL-based data transformation |
| Orchestration | dbt CLI | Run and test transformations |
| Package Manager | uv | Python dependency management |
| Visualization | Power BI | Business intelligence dashboards |

## Dataset Description

The Olist dataset includes:

| Table | Description | Records |
|-------|-------------|---------|
| orders | Order header information | ~100k |
| order_items | Line items for each order | ~113k |
| order_payments | Payment details per order | ~104k |
| order_reviews | Customer reviews and ratings | ~100k |
| customers | Customer information | ~100k |
| products | Product catalog | ~33k |
| sellers | Seller information | ~3k |
| geolocation | Brazilian zip code coordinates | ~1M |
| product_category_translation | Portuguese to English mapping | 71 |

## Data Model

### Layered Architecture (Medallion Pattern)

```
ECOMMERCE_RETAIL_DB_DEV (Bronze + Silver + Gold-Dev)
┌─────────────────────────────────────────────────────────────────────────┐
│ BRONZE (RAW)           Raw CSV data loaded via Python                   │
├─────────────────────────────────────────────────────────────────────────┤
│ SILVER (STAGING)       Cleaned, typed, validated views                  │
│  stg_ecommerce__orders, stg_ecommerce__customers, ...                   │
├─────────────────────────────────────────────────────────────────────────┤
│ GOLD (INTERMEDIATE)    Joined and enriched models                       │
│  int_orders_enriched, int_order_items_enriched                          │
├─────────────────────────────────────────────────────────────────────────┤
│ GOLD (MARTS)           Fact and dimension tables (Dev)                  │
│  Core | Customer | Finance | Marketing                                  │
└─────────────────────────────────────────────────────────────────────────┘

ECOMMERCE_RETAIL_DB_PROD (Gold Only - Dashboards Connect Here)
┌─────────────────────────────────────────────────────────────────────────┐
│ GOLD (INTERMEDIATE)    Reads from DEV.STAGING                           │
├─────────────────────────────────────────────────────────────────────────┤
│ GOLD (MARTS)           Production analytics tables                      │
│  dim_* | fct_* (BI tools connect here)                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dimensional Model

**Core Fact Tables:**
- `fct_orders` - Grain: one row per order with metrics and deterministic FKs
- `fct_order_items` - Grain: one row per order item with deterministic FKs

**Customer Fact Tables:**
- `fct_rfm_segments` - Grain: one row per customer per month (RFM + churn risk snapshots)
- `fct_cohort_retention` - Grain: one row per cohort per period with GRR/NRR metrics
- `fct_clv_customer` - Grain: one row per customer with CLV and behavioral segments

**Finance Fact Tables:**
- `fct_order_payments` - Grain: one row per payment line item with deterministic FKs

**Marketing Fact Tables:**
- `fct_market_basket` - Grain: one row per product pair with co-occurrence counts

**Dimension Tables:**
- `dim_customers` - Pure customer dimension with attributes and cohort assignment
- `dim_dates` - Pre-generated date dimension (2016-2028) with period start dates
- `dim_products` - Pure product dimension with English categories
- `dim_sellers` - Pure seller dimension with location and primary category

## Project Structure

```
ecommerce-retail-analytics/        # Project root (within portfolio-projects repo)
├── README.md                      # Project overview (this file)
├── CLAUDE.md                      # Claude Code project context
├── INSTALLATION.md                # Setup and installation guide
├── INSTRUCTIONS.md                # Detailed execution guide
├── .env.example                   # Environment variables template
├── pyproject.toml                 # Python dependencies (uv)
├── uv.lock                        # Locked dependency versions
│
├── .claude/                       # Claude Code configuration
│   ├── AGENTS.md                  # Agentic workflow guide
│   ├── skills/                    # Custom skills
│   └── references/                # Reference documentation
│
├── docs/
│   └── SQL Analytical Patterns/   # SQL pattern study guides
│       ├── 01-rfm-analysis.md
│       ├── 02-cohort-analysis.md
│       ├── 03-customer-lifetime-value.md
│       └── 04-churn-indicators.md
│
├── snowflake/                     # Snowflake setup scripts
│   ├── 1-roles-and-user-config.sql
│   ├── 2-warehouse-config.sql
│   ├── 3-database-schemas-config.sql  # Medallion 2-database setup
│   ├── 4-grant-access-config.sql
│   └── 5-verify-setup.sql
│
├── scripts/                       # Data extraction and loading
│   ├── download_kaggle_data.py
│   └── load_to_snowflake.py
│
├── data/                          # Downloaded data (gitignored)
│
├── report/                        # Power BI PBIP files
│   ├── Ecommerce Analytics.Report/
│   └── Ecommerce Analytics.SemanticModel/
│
└── dbt/
    ├── dbt_project.yml
    ├── packages.yml
    ├── .sqlfluff                  # SQL linting configuration
    ├── models/
    │   ├── staging/               # Silver layer (always in DEV)
    │   ├── intermediate/          # Gold layer
    │   └── marts/
    │       ├── core/              # Shared dimensions & core facts
    │       ├── customer/          # Customer analytics (RFM, CLV, Churn)
    │       ├── finance/           # Revenue & payment analytics
    │       └── marketing/         # Category & geo analytics
    ├── macros/
    ├── tests/
    └── seeds/
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/musatouray/portfolio-projects.git
cd portfolio-projects/ecommerce-retail-analytics
```

For detailed setup instructions including Snowflake key-pair authentication, see **[INSTALLATION.md](INSTALLATION.md)**.

## License

This project uses the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) released under CC BY-NC-SA 4.0.
