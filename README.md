# E-Commerce Retail Analytics Platform

> **Turn raw transaction data into actionable customer insights that drive revenue growth, reduce churn, and optimize marketing spend.**

A production-grade analytics platform demonstrating how modern data teams deliver business value—from automated data pipelines to interactive dashboards that answer the questions executives actually ask.

---

## Business Impact

This platform answers the critical questions that drive e-commerce profitability:

| Business Question | Analytics Solution | Impact |
|-------------------|-------------------|--------|
| *"Which customers should we prioritize?"* | **RFM Segmentation** classifies customers into Champions, Loyal, At-Risk, and Lost segments | Focus retention efforts on high-value customers before they churn |
| *"What's a customer worth over time?"* | **Customer Lifetime Value** predicts 12-month revenue per customer | Optimize acquisition spend based on projected ROI |
| *"Are we retaining customers?"* | **Cohort Retention Analysis** tracks monthly cohorts with GRR/NRR metrics | Identify which acquisition channels produce sticky customers |
| *"Who's about to leave?"* | **Churn Risk Scoring** flags at-risk customers based on behavioral signals | Trigger proactive outreach before customers disappear |
| *"What products sell together?"* | **Market Basket Analysis** identifies co-purchase patterns | Power cross-sell recommendations and bundle offers |

---

## What Makes This Production-Grade

This isn't a Jupyter notebook analysis—it's a **complete data platform** built with the same tools and practices used by data teams at top tech companies:

| Capability | Implementation |
|------------|----------------|
| **Automated Pipeline** | Airflow orchestrates daily data generation, loading, and transformation |
| **Cloud Data Warehouse** | Snowflake with medallion architecture (Bronze → Silver → Gold) |
| **Version-Controlled Transforms** | dbt models with 20+ staging, intermediate, and mart tables |
| **CI/CD** | GitHub Actions runs tests on every PR, deploys to production on merge |
| **Environment Isolation** | Separate DEV and PROD databases—changes validated before reaching dashboards |
| **Observability** | Slack alerts on pipeline failures, success summaries with row counts |
| **Interactive Dashboards** | Power BI reports deployed via Fabric Git integration (`fabric-prod` branch) |

---

## Analytics Models

### Customer Intelligence

| Model | What It Does | Key Metrics |
|-------|--------------|-------------|
| **fct_rfm_segments** | Monthly customer segmentation snapshots | Recency, Frequency, Monetary scores; segment classification |
| **fct_clv_customer** | Lifetime value prediction with behavioral inputs | 12-month projected CLV, purchase probability, value tier |
| **fct_cohort_retention** | Cohort-based retention tracking | Retention rate, GRR, NRR by acquisition month |

### Core Analytics

| Model | What It Does | Key Metrics |
|-------|--------------|-------------|
| **fct_orders** | Order-level fact table | Revenue, items, payment method, delivery performance |
| **fct_order_items** | Line-item detail | Product, seller, price, freight, margins |
| **fct_order_payments** | Payment breakdown | Payment type, installments, value |
| **fct_market_basket** | Product co-occurrence | Pair frequency, support, confidence |

### Dimensions

| Model | What It Does |
|-------|--------------|
| **dim_customers** | Customer attributes, location, acquisition cohort |
| **dim_products** | Product catalog with categories |
| **dim_sellers** | Seller attributes, performance tier |
| **dim_dates** | Date spine with fiscal periods, holidays |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA PIPELINE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │ Synthetic│    │   AWS    │    │Snowflake │    │   dbt    │    │ Power BI │ │
│   │   Data   │───▶│    S3    │───▶│   RAW    │───▶│  Models  │───▶│Dashboards│ │
│   │Generator │    │  Stage   │    │ (Bronze) │    │(Silver/  │    │ (Fabric) │ │
│   └──────────┘    └──────────┘    └──────────┘    │  Gold)   │    └──────────┘ │
│        │                                          └──────────┘          │       │
│        │              AIRFLOW ORCHESTRATION                             │       │
│        └────────────────────────────────────────────────────────────────┘       │
│                                    │                                            │
│                            ┌───────▼───────┐                                    │
│                            │     Slack     │                                    │
│                            │    Alerts     │                                    │
│                            └───────────────┘                                    │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              CI/CD (GitHub Actions + Fabric Git)                │
│   PR → Test (DEV) → main → Deploy dbt (PROD) → fabric-prod → Fabric Sync       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Medallion Architecture

```
ECOMMERCE_RETAIL_DB_DEV                    ECOMMERCE_RETAIL_DB_PROD
┌─────────────────────────┐                ┌─────────────────────────┐
│ RAW (Bronze)            │                │                         │
│ └─ Source tables        │                │                         │
├─────────────────────────┤                │                         │
│ STAGING (Silver)        │───────────────▶│ INTERMEDIATE (Gold)     │
│ └─ Cleaned views        │  CD deploys    │ └─ Enriched models      │
├─────────────────────────┤                ├─────────────────────────┤
│ INTERMEDIATE (Gold)     │                │ MARTS (Gold)            │
├─────────────────────────┤                │ └─ Fact & Dim tables    │
│ MARTS (Gold)            │                │   (Dashboards connect)  │
└─────────────────────────┘                └─────────────────────────┘
        DEV                                         PROD
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | Airflow (Docker) | Schedule pipelines, manage dependencies |
| **Storage** | AWS S3 | Stage raw files for loading |
| **Warehouse** | Snowflake | Scalable cloud analytics database |
| **Transformation** | dbt (Data Build Tool) | Version-controlled SQL models with testing |
| **CI/CD** | GitHub Actions | Automated testing and deployment |
| **Visualization** | Power BI + Microsoft Fabric | Interactive dashboards with Git-based deployment |
| **Alerting** | Slack | Pipeline monitoring and notifications |
| **Languages** | Python, SQL | Data generation, advanced analytics |

---

## Dashboard Highlights

The Power BI layer delivers interactive analytics across multiple domains:

**Customer Analytics**
- RFM segment distribution and migration flows
- CLV distribution by segment and cohort
- Churn risk heatmaps with drill-through to at-risk customers

**Revenue Intelligence**
- Cohort retention triangles with GRR/NRR trends
- Period-over-period revenue comparisons
- Payment method and installment analysis

**Geographic Insights**
- State-level performance maps
- Regional delivery performance
- Market penetration analysis

**Product & Seller Performance**
- Category revenue trends
- Market basket visualization
- Seller tier rankings

---

## Project Structure

```
ecommerce-retail-analytics/
├── airflow/                    # Pipeline orchestration
│   ├── dags/                   # DAG definitions
│   │   ├── daily_synthetic_orders.py
│   │   └── backfill_synthetic_orders.py
│   ├── docker-compose.yml
│   └── Dockerfile
│
├── dbt/                        # Data transformations
│   ├── models/
│   │   ├── staging/            # Silver layer
│   │   ├── intermediate/       # Enriched models
│   │   └── marts/              # Fact & dimension tables
│   │       ├── core/
│   │       ├── customer/
│   │       ├── finance/
│   │       └── marketing/
│   └── tests/
│
├── scripts/                    # Data generation & loading
│   ├── synthetic_data_generator.py
│   └── load_to_snowflake.py
│
├── report/                     # Power BI project files (syncs to Fabric via fabric-prod branch)
│   ├── Ecommerce Analytics.Report/
│   └── Ecommerce Analytics.SemanticModel/
│
├── snowflake/                  # Database setup scripts
├── docs/                       # Documentation
└── .github/workflows/          # CI/CD pipelines
```

---

## Getting Started

See **[INSTALLATION.md](INSTALLATION.md)** for complete setup instructions including:
- Snowflake key-pair authentication
- Airflow Docker deployment
- AWS S3 integration
- Power BI connection

---

## Skills Demonstrated

| Category | Skills |
|----------|--------|
| **Data Engineering** | Pipeline orchestration, ELT patterns, Airflow DAGs |
| **Analytics Engineering** | dbt modeling, data quality testing, documentation, modular SQL |
| **Data Modeling** | Dimensional modeling (Kimball), fact/dimension design, slowly changing dimensions |
| **Advanced SQL** | Window functions, CTEs, complex aggregations, performance optimization |
| **Business Analytics** | RFM segmentation, cohort analysis, CLV, churn prediction, market basket |
| **Cloud Platforms** | Snowflake, AWS S3, cloud cost optimization |
| **DevOps** | Docker, GitHub Actions CI/CD, environment management, Slack alerting |
| **Visualization** | Power BI, DAX measures, interactive dashboards |

---

## License

MIT License - See [LICENSE](LICENSE) for details.
