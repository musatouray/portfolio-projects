# Data Engineering Portfolio

A collection of production-grade data engineering and analytics projects showcasing modern data stack implementations, advanced SQL patterns, and end-to-end pipeline automation.

---

## Projects

| Project | Description | Tech Stack |
|---------|-------------|------------|
| [E-Commerce Retail Analytics](./ecommerce-retail-analytics/) | Production-grade analytics platform with automated pipelines, dimensional modeling, and interactive dashboards. Features RFM segmentation, cohort retention, CLV prediction, and churn risk scoring. | Snowflake, dbt, Airflow, AWS S3, Power BI, GitHub Actions |
| [Advanced SQL Patterns](./Advanced-SQL-Patterns/) | Advanced T-SQL patterns for business analytics featuring window functions, time series analysis, customer segmentation, and cohort retention. Includes interactive Jupyter notebooks with visualizations. | SQL Server, Python, Jupyter |

---

## Repository Structure

```
portfolios/
├── .github/workflows/              # CI/CD pipelines
├── ecommerce-retail-analytics/     # E-Commerce Analytics Platform
│   ├── airflow/                    # Pipeline orchestration (Docker)
│   ├── dbt/                        # Data transformations
│   ├── report/                     # Power BI reports (PBIP)
│   └── snowflake/                  # Database setup scripts
├── Advanced-SQL-Patterns/          # SQL Patterns & Techniques
│   ├── sql/                        # Raw SQL scripts
│   ├── notebooks/                  # Jupyter notebooks
│   └── docs/                       # Data dictionary
└── [future-projects]/
```

---

## Skills Demonstrated

| Category | Techniques |
|----------|------------|
| **Data Engineering** | Pipeline orchestration (Airflow), ELT patterns, medallion architecture, cloud data warehousing |
| **Analytics Engineering** | dbt modeling, data quality testing, documentation, modular SQL |
| **Advanced SQL** | Window functions, CTEs, cohort analysis, time series, running totals, percentile ranking |
| **Data Modeling** | Dimensional modeling (Kimball), fact/dimension design, slowly changing dimensions |
| **Business Analytics** | RFM segmentation, customer lifetime value, churn prediction, market basket analysis |
| **DevOps** | Docker, GitHub Actions CI/CD, environment isolation, Slack alerting |
| **Visualization** | Power BI dashboards, DAX measures, Jupyter notebooks with Matplotlib/Seaborn |

---

## Getting Started

Each project contains its own `README.md` with detailed setup instructions. Navigate to the project folder to begin.

---

## Author

**Musa Touray** — Data Engineer

Portfolio: [musatouray.github.io](https://musatouray.github.io/)
