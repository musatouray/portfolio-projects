# Time Intelligence - Interview Study Guide

## What is Time Intelligence?

Time Intelligence analyzes metrics across time periods to identify trends, seasonality, and growth patterns. It answers:
- "How does this month compare to last month?" (MoM)
- "How are we doing vs same period last year?" (YoY)
- "What's the underlying trend after removing daily noise?" (Moving Averages)

```
Daily Metrics → Add Time Comparisons → Calculate Growth Rates → Identify Trends
```

---

## Key Terms and Definitions

| Term | Definition | SQL Implementation |
|------|------------|-------------------|
| **Prior Period** | Value from a previous time point | `LAG()` or self-join |
| **WoW** | Week-over-Week comparison | Compare to 7 days ago |
| **MoM** | Month-over-Month comparison | Compare to same day last month |
| **YoY** | Year-over-Year comparison | Compare to same day last year |
| **Moving Average** | Rolling average over N periods | `AVG() OVER (ROWS BETWEEN...)` |
| **Running Total** | Cumulative sum to date | `SUM() OVER (ORDER BY date)` |
| **YTD** | Year-to-Date cumulative | `SUM() OVER (PARTITION BY year)` |
| **Growth Rate** | Percentage change | `(current - prior) / prior * 100` |

### Common Time Periods

| Abbreviation | Meaning | SQL Pattern |
|--------------|---------|-------------|
| **PW** | Prior Week (same day) | `DATEADD(day, -7, date)` |
| **PM** | Prior Month (same day) | `DATEADD(month, -1, date)` |
| **PY** | Prior Year (same day) | `DATEADD(year, -1, date)` |
| **YTD** | Year-to-Date | `PARTITION BY year` |
| **QTD** | Quarter-to-Date | `PARTITION BY year, quarter` |
| **MTD** | Month-to-Date | `PARTITION BY year, month` |
| **WTD** | Week-to-Date | `PARTITION BY iso_week` |

---

## Why FAANG Cares

### 1. Business Health Monitoring
- "Are we growing or declining?"
- "Is this spike normal or an anomaly?"
- "How does seasonality affect our metrics?"

### 2. Strategic Planning
- Set realistic targets based on historical trends
- Identify seasonal patterns for resource planning
- Detect early warning signs of decline

### 3. Tests SQL Skills
- **Window Functions**: `LAG()`, `SUM() OVER`, `AVG() OVER`
- **Self-Joins**: For handling gaps in data
- **Date Functions**: `DATEADD()`, `DATEDIFF()`
- **Frame Clauses**: `ROWS BETWEEN N PRECEDING AND CURRENT ROW`

### 4. Common Interview Questions
- "How would you calculate month-over-month growth?"
- "Design a system to track YTD performance"
- "How would you smooth out daily fluctuations to see the trend?"
- "What's the difference between LAG and a moving average?"

---

## Two Approaches: LAG vs Self-Join

### When to Use LAG()

Use `LAG()` when your data has **no gaps** (every time period has a row):

```sql
-- Simple and efficient when no gaps
LAG(revenue, 7) OVER (ORDER BY date) as revenue_7_days_ago
```

**Problem**: If there are missing dates, `LAG(revenue, 7)` gives you "7 rows back" not "7 calendar days ago."

### When to Use Self-Join

Use self-join when your data has **gaps** (missing dates):

```sql
-- Handles gaps correctly
SELECT
    curr.date,
    curr.revenue,
    prev.revenue as revenue_7_days_ago
FROM daily_metrics curr
LEFT JOIN daily_metrics prev
    ON prev.date = DATEADD(day, -7, curr.date)
```

**Benefit**: Always compares to the exact calendar date, regardless of gaps.

---

## CTE Structure

```
┌─────────────────────┐
│   daily_base        │  ← Join metrics with dim_dates for calendar attributes
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  prior_periods      │  ← Self-joins for PW, PM, PY
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  moving_averages    │  ← Rolling windows (7d, 28d, 90d, 365d)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  running_totals     │  ← Cumulative, YTD, QTD, MTD, WTD
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  growth_rates       │  ← WoW%, MoM%, YoY%
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← Select, round, add metadata
└─────────────────────┘
```

---

## SQL Patterns

### Prior Period Comparisons (Self-Join)

```sql
SELECT
    curr.*,
    -- Prior week (exactly 7 days ago)
    prev_week.revenue as revenue_prev_week,
    -- Prior month (same day last month)
    prev_month.revenue as revenue_prev_month,
    -- Prior year (same day last year)
    prev_year.revenue as revenue_prev_year
FROM daily_base curr
LEFT JOIN daily_base prev_week
    ON prev_week.date = DATEADD(day, -7, curr.date)
LEFT JOIN daily_base prev_month
    ON prev_month.date = DATEADD(month, -1, curr.date)
LEFT JOIN daily_base prev_year
    ON prev_year.date = DATEADD(year, -1, curr.date)
```

### Moving Averages

```sql
-- 7-day moving average (smooths weekly patterns)
AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
) as revenue_ma_7d

-- 28-day moving average (smooths monthly patterns)
AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 27 PRECEDING AND CURRENT ROW
) as revenue_ma_28d
```

**Note**: Use 28 days (4 weeks) instead of 30 to align with weekly patterns.

### Running Totals

```sql
-- Cumulative (all-time)
SUM(revenue) OVER (ORDER BY date) as cumulative_revenue

-- Year-to-date (resets each year)
SUM(revenue) OVER (
    PARTITION BY year
    ORDER BY date
) as ytd_revenue

-- Quarter-to-date
SUM(revenue) OVER (
    PARTITION BY year, quarter_number
    ORDER BY date
) as qtd_revenue
```

### Growth Rates

```sql
-- Week-over-week growth percentage
ROUND(
    (revenue - revenue_prev_week) / NULLIF(revenue_prev_week, 0) * 100,
    2
) as revenue_growth_wow_pct

-- Year-over-year growth percentage
ROUND(
    (revenue - revenue_prev_year) / NULLIF(revenue_prev_year, 0) * 100,
    2
) as revenue_growth_yoy_pct
```

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `DATEADD(unit, n, date)` | Add/subtract time | `DATEADD(month, -1, date)` |
| `LAG(col, n)` | Get value n rows back | `LAG(revenue, 7)` |
| `SUM() OVER (ORDER BY)` | Running total | `SUM(rev) OVER (ORDER BY date)` |
| `SUM() OVER (PARTITION BY)` | Running total with reset | `SUM(rev) OVER (PARTITION BY year)` |
| `AVG() OVER (ROWS BETWEEN)` | Moving average | `AVG(rev) OVER (ROWS BETWEEN 6 PRECEDING...)` |
| `NULLIF(x, 0)` | Prevent division by zero | `rev / NULLIF(prev_rev, 0)` |
| `COALESCE(x, 0)` | Replace NULL with 0 | `COALESCE(orders, 0)` |

---

## Handling Data Gaps

### Problem: Gaps in Daily Data

If some days have no orders, you have two choices:

| Approach | Pros | Cons |
|----------|------|------|
| **Only order dates** | Smaller table, simpler | LAG doesn't work correctly, gaps in charts |
| **All calendar dates** | Complete time series, accurate comparisons | More rows, need COALESCE for NULLs |

### Solution: Fill with Date Spine

```sql
-- Include all calendar dates, fill gaps with 0
SELECT
    d.date_key,
    d.date,
    COALESCE(da.total_orders, 0) as total_orders,
    COALESCE(da.revenue, 0) as revenue
FROM dim_dates d
LEFT JOIN daily_aggregates da ON d.date = da.order_date
```

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Using LAG with gaps | Wrong period comparison | Use self-join with DATEADD |
| Integer division | Growth rates are 0 | Multiply by 100.0 first |
| Division by zero | Error when prior period is 0 | Use `NULLIF(prior, 0)` |
| Wrong window frame | MA includes wrong rows | Use `ROWS BETWEEN`, not default |
| 30-day MA | Doesn't align with weeks | Use 28 days (4 weeks) |
| NULLs in base metrics | Confusing for BI tools | Use `COALESCE(..., 0)` |

---

## Business Applications

### 1. Executive Dashboard
```sql
-- Key metrics with growth indicators
SELECT
    date,
    gross_revenue,
    revenue_growth_yoy_pct,
    CASE
        WHEN revenue_growth_yoy_pct > 0 THEN 'Growing'
        WHEN revenue_growth_yoy_pct < 0 THEN 'Declining'
        ELSE 'Flat'
    END as trend
FROM fct_daily_revenue_time_series
WHERE date = CURRENT_DATE - 1
```

### 2. Trend Analysis
```sql
-- Compare actual vs 7-day MA to detect anomalies
SELECT
    date,
    gross_revenue,
    rolling_avg_revenue_7d,
    gross_revenue / NULLIF(rolling_avg_revenue_7d, 0) as index_vs_trend
FROM fct_daily_revenue_time_series
WHERE index_vs_trend > 1.5  -- 50% above trend = anomaly
```

### 3. Seasonality Detection
```sql
-- Compare same day across years
SELECT
    DAYOFWEEK(date) as day_of_week,
    AVG(gross_revenue) as avg_revenue,
    AVG(revenue_growth_yoy_pct) as avg_yoy_growth
FROM fct_daily_revenue_time_series
GROUP BY 1
ORDER BY 1
```

---

## Interview Tips

1. **Clarify data gaps**: "Does the data have rows for every day, or only days with activity? This affects whether I use LAG or self-join."

2. **Explain window frames**: "ROWS BETWEEN 6 PRECEDING AND CURRENT ROW gives me 7 data points total — the current row plus the 6 before it."

3. **Discuss DATEADD vs LAG**: "DATEADD with self-join is more accurate for calendar comparisons, especially with gaps. LAG is simpler but assumes continuous data."

4. **Mention edge cases**: "Early rows will have NULL for prior periods — we can't calculate YoY growth until we have a full year of data."

5. **Connect to business**: "Time intelligence helps answer 'are we doing better or worse' and 'what's the underlying trend' — critical for any business."

---

## Practice Questions

1. What's the difference between `LAG(revenue, 30)` and `DATEADD(month, -1, date)` for month-over-month comparison?

2. Why do we use `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` instead of `ROWS BETWEEN 7 PRECEDING AND CURRENT ROW` for a 7-day moving average?

3. Your growth rate calculation returns NULL for some rows. What are the possible causes?

4. How would you calculate the percentage of YTD target achieved if the annual target is $10M?

5. A PM asks "why did revenue spike on Tuesday?" — how would time intelligence metrics help investigate?

6. What's the difference between `SUM() OVER (ORDER BY date)` and `SUM() OVER (PARTITION BY year ORDER BY date)`?

---

## Related Patterns

| Pattern | Relationship to Time Intelligence |
|---------|----------------------------------|
| **Cohort Analysis** | Cohort retention is time intelligence at cohort level |
| **Churn Indicators** | Uses days_since_last_order (time-based metric) |
| **Pareto Analysis** | Can be extended with time dimension (rankings over time) |
| **Funnel Analysis** | Conversion rates tracked over time |
