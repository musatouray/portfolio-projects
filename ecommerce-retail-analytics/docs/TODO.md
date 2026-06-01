# Functionalities to add to this porfolio project

✅ Generate synthetic data for incremental ETL Pipeline (Using Docker, Faker, Airflow, S3 & COPY INTO RAW)
    ┌─────────────────────┬──────────────────────────────────────┬───────────────────────────────────────────┐
    │ Component           │ Choice                               │ Why                                       │
    ├─────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────┤
    │ Storage             │ AWS S3                               │ Native Snowpipe, LocalStack for local dev │
    ├─────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────┤
    │ Ingestion           │ Snowflake External Stage + COPY INTO │ Synchronous, Airflow-orchestrable         │
    ├─────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────┤
    │ Orchestration       │ Airflow on Docker Compose            │ Industry standard, shows DAG design       │
    ├─────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────┤
    │ Data generation     │ Faker + Pandas                       │ Simple, controllable                      │
    ├─────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────┤
    │ Airflow → Snowflake │ SnowflakeOperator or astro-sdk       │ Official provider                         │
    ├─────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────┤
    │ Airflow → S3        │ S3Hook                               │ Mature, well-documented                   │
    ├─────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────┤
    │ Local S3 mock       │ LocalStack                           │ Test without AWS costs                    │
    └─────────────────────┴──────────────────────────────────────┴───────────────────────────────────────────┘
    ▪ generate_data : Faker generates daily CSV
    ▪ upload_to_S3 : Lands in s3://bucket/YYYY/MM/
    ▪ copy_into_raw : COPY INTO Snowfalke RAW
    ▪ backfill : current data is between 2016 to 2018, backfill up to current_date then generate daily files to test all edge cases like:
✅ Data Quality & Observability (Data Contracts)
✅ Idempotency 
✅ Late-arriving data handling
✅ Backfill
✅ SCD Type 2
✅ Implement Change Data Capture (CDC)
✅ Schema Evolution or Schema Drift
✅ Partitioning, clustering keys
✅ Query optimization 
✅ Data Lineage Visualization (Using dbt)
✅ Power BI Dashboard
    ✅ DESIGN FRAMEWORK (docs/dashboard-design/)
        ▪ 00-design-framework.md : Theme design, measure organization, page structure
        ▪ design-tokens.md : Human-readable color/typography reference
        ▪ ecommerce-analytics-theme.json : Power BI theme (580+ lines)
    ✅ NARRATIVE BRIEFS (10 pages with wireframes + data mapping)
        ▪ 01-executive-summary.md : KPIs, revenue trends, business health
        ▪ 02-rfm-segmentation.md : RFM analysis, customer segments
        ▪ 03-customer-lifetime-value.md : CLV tiers and predictions
        ▪ 04-cohort-retention.md : Retention heatmap by cohort
        ▪ 05-churn-risk.md : Churn risk scoring and alerts
        ▪ 06-funnel-analysis.md : Order status funnel
        ▪ 07-product-performance.md : Pareto analysis (80/20)
        ▪ 08-market-basket.md : Cross-sell opportunities
        ▪ 09-geographic-insights.md : Brazil map, regional metrics
        ▪ 10-time-trends.md : Time intelligence, seasonality
    ⏳ BUILD VISUALS (follow wireframes in narrative briefs)
    ⏳ CREATE DAX MEASURES (as specified in each page brief)
✅ BG/NBD Predictive Model via dbt Python for predictive_ltv
✅ Self-Correcting Agentic SQL Analyst - An Agentic RAG using crewAI / LangGraph / Microsoft Agent Framework SDK
✅ Streamlit App
✅ Cost Monitoring (Snowflake query costs, credit usage alerts)
✅ Unit Tests (dbt unit testing for complex SQL logic)

## Agentic Analytics Engineering

✅ Agentic Analytics Engineering
    ✅ CONTEXT FILES
        ▪ CLAUDE.md : Entry point for Claude Code. Points to AGENTS.md
        ▪ AGENTS.md : The brain - describes role, context, tech stack, directory structure, and a menu of skills
    ✅ SUB-AGENTS (Read-Only Behavioral Modes)
        ▪ code-reviewer : Reviews SQL for quality, performance, conventions. Does not write code.
        ▪ doc-reviewer : Reviews YAML descriptions for clarity and completeness. Does not write YAML.
        ▪ performance-analyst : Analyzes query performance, suggests optimizations and clustering keys.
        ▪ data-quality-auditor : Reviews test coverage, identifies gaps in data contracts.
        ▪ schema-designer : Reviews dimensional modeling decisions, star schema conformance.
    ✅ SKILLS - STEP-BY-STEP PROCEDURES (in .claude/skills/<name>/SKILL.md)
        ▪ /develop : Scaffolds SQL, builds logic and creates YAML following conventions
        ▪ /test : Runs dbt tests, spot-checks via warehouse queries, impact analysis across lineage
        ▪ /deploy : Commits changes to repo, opens a draft PR with ticket context
        ▪ /check-test-failures : Queries production test results and suggests fixes
        ▪ /refactor : Optimizes existing models for performance or readability
    ✅ REFERENCES - LAZY-LOADED CONVENTIONS (in .claude/references/)
        ▪ dbt-conventions.md : General conventions about dbt development
        ▪ sql-conventions.md : Loaded only when writing SQL
        ▪ yaml-conventions.md : How to produce correct YAML files
        ▪ data-warehouse.md : How to query the data warehouse - databases, schemas, etc.
