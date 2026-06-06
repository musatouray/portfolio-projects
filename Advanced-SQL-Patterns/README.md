# Advanced SQL Patterns for Business Analytics

## Overview

This project demonstrates advanced T-SQL patterns for solving real-world business analytics questions. Using Microsoft's `AdventureWorksDW2022` data warehouse, these scripts showcase the progression from basic aggregations to sophisticated, set-based operations used in modern business intelligence and data engineering.

> **Note:** `FORMAT()` functions are used throughout for user-friendly presentation since this is an exploratory data analysis (EDA) project. In production environments, formatting would be handled at the presentation layer to avoid the performance overhead of converting numeric values to strings.

## Business Questions Answered

### Sales Performance & Ranking (`01_sales_performance.sql`)

| # | Question | Key Techniques |
|---|----------|----------------|
| 1 | **Top Products by Revenue per Year** — Identify the top 5 products by revenue for each calendar year with rank and contribution percentage | `DENSE_RANK`, `SUM() OVER`, CTEs |
| 2 | **Sales Rep Performance Ranking** — Rank sales representatives by quarterly revenue, showing rank change vs. previous quarter | `LAG`, `DENSE_RANK`, quarter-over-quarter comparison |
| 3 | **Product Category Revenue Distribution** — Calculate what percentile each product falls into based on total revenue | `PERCENT_RANK`, percentile-based tiering |
| 4 | **Best & Worst Performing Territories** — Rank territories by YoY revenue growth rate, identifying top 3 and bottom 3 | `LAG` for YoY, dual `DENSE_RANK` for top/bottom |

### Time Series & Trend Analysis (`02_time_series.sql`)

| # | Question | Key Techniques |
|---|----------|----------------|
| 5 | **Running Total of Sales by Month** — Calculate running total of internet sales by month, partitioned by product category | `SUM() OVER` with ordered frame |
| 6 | **Month-over-Month Sales Growth** — Calculate MoM percentage change for each territory, handling months with zero sales | Date spine via `CROSS JOIN`, `LAG`, `COALESCE` |
| 7 | **3-Month Moving Average** — Compute a rolling average to smooth seasonal fluctuations | `AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` |
| 8 | **Year-to-Date (YTD) Sales** — Calculate YTD sales for each product, resetting at calendar year boundaries | `SUM() OVER (PARTITION BY year, product ORDER BY month)` |

### Customer Analytics (`03_customer_analytics.sql`)

| # | Question | Key Techniques |
|---|----------|----------------|
| 9 | **Customer Segmentation by Purchase Frequency** — Segment customers into quintiles based on order frequency with average order value | `PERCENT_RANK`, frequency-based segmentation |
| 10 | **Customer Lifetime Value Ranking** — Rank customers by predictive CLV within each geographic region | CLV formula: `APV × APF × Lifespan`, regional churn rates |
| 11 | **First vs. Most Recent Purchase Analysis** — Compare each customer's first purchase amount with their most recent | `FIRST_VALUE`, `LAST_VALUE` with proper frame specification |
| 12 | **Customer Retention Cohort Analysis** — Calculate retention rates by cohort month (retention triangle) | `DATETRUNC`, `FIRST_VALUE`, dynamic `PIVOT` |

## Key Techniques Demonstrated

### Window Functions

- **Ranking:** `DENSE_RANK`, `RANK`, `ROW_NUMBER` for competitive rankings
- **Offset:** `LAG`, `LEAD` for period-over-period comparisons
- **Aggregate:** `SUM() OVER`, `AVG() OVER` for running totals and moving averages
- **Value:** `FIRST_VALUE`, `LAST_VALUE` with explicit frame specification

### Advanced Patterns

- **Date Spines:** `CROSS JOIN` to generate continuous time dimensions, ensuring zero-sales months are represented
- **Cohort Analysis:** Customer birth assignment, aging calculation, and retention triangle via `PIVOT`
- **Predictive CLV:** Formula-based lifetime value using `(Average Profit × Purchase Frequency) × Expected Lifespan`
- **Statistical Distribution:** `PERCENT_RANK` for percentile placement (preferred over `NTILE` for skewed distributions)

### Code Organization

- Step-by-step CTEs with numbered comments
- Defensive coding with `NULLIF()` for division protection
- Configurable thresholds via `DECLARE` statements
- Clear separation of aggregation, calculation, and presentation layers

## Repository Structure

```
Advanced-SQL-Patterns/
├── README.md
├── docs/
│   └── data_dictionary.md      # AdventureWorksDW2022 table reference
└── sql/
    ├── 01_sales_performance.sql    # Questions 1-4
    ├── 02_time_series.sql          # Questions 5-8
    └── 03_customer_analytics.sql   # Questions 9-12
```

## Setup Instructions

**Prerequisites:** Microsoft SQL Server 2022+ (for `DATETRUNC` support)

1. Download [`AdventureWorksDW2022.bak`](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure) from Microsoft
2. Restore to your SQL Server instance
3. Execute scripts in `/sql/` via SSMS, Azure Data Studio, or your preferred client

## Connect

Portfolio: [musatouray.github.io](https://musatouray.github.io/)