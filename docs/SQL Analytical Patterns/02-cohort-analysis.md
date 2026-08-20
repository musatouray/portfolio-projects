# Cohort Analysis - Interview Study Guide

## What is Cohort Analysis?

Cohort analysis groups customers by a shared characteristic (typically their first purchase date) and tracks their behavior over time. It answers the question: "Are customers acquired this month behaving better or worse than those acquired last month?"

Unlike aggregate metrics that blur trends, cohort analysis reveals whether your product is improving or declining by comparing apples to apples — customers at the same stage of their lifecycle.

```
Customers → Group by First Purchase Month → Track Activity Over Time → Retention Curves
```

---

## Key Terms and Definitions

| Term | Definition | SQL Implementation |
|------|------------|-------------------|
| **Cohort** | A group of customers who share a common characteristic, typically first purchase month | `DATE_TRUNC('month', first_order_date)` |
| **Cohort Month** | The month a customer made their first purchase (their "birth" month) | `DATE_TRUNC('month', MIN(order_date))` |
| **Activity Month** | Any month in which a customer placed an order | `DATE_TRUNC('month', order_date)` |
| **Period Number** | Time elapsed since cohort formation (0 = first month, 1 = second month, etc.) | `DATEDIFF('month', cohort_month, activity_month)` |
| **Cohort Size** | Total number of customers in a cohort | `COUNT(DISTINCT customer_id) ... GROUP BY cohort_month` |
| **Active Customers** | Customers from a cohort who placed an order in a given period | `COUNT(DISTINCT customer_id) ... GROUP BY cohort_month, period` |
| **Retention Rate** | Percentage of cohort still active: `(active / cohort_size) * 100` | `active_customers / cohort_size * 100` |
| **Retention Curve** | Visual representation of retention over periods | Line chart: X = period, Y = retention % |

### Cohort Table Example

```
              Period 0    Period 1    Period 2    Period 3
Jan 2024       100%        15%         8%          5%
Feb 2024       100%        18%         10%         6%
Mar 2024       100%        22%         14%         -
Apr 2024       100%        25%         -           -
                            ↑
                     Improving retention!
```

---

## Why FAANG Cares

### 1. Product-Market Fit Indicator
- **Improving cohorts** = product is getting better
- **Declining cohorts** = something is wrong
- Isolates product changes from growth effects

### 2. Tests Advanced SQL Skills
- **Self-Joins**: Joining customers to their own activity
- **Window Functions**: `MIN() OVER`, aggregations
- **Date Functions**: `DATE_TRUNC()`, `DATEDIFF()`
- **Complex Aggregations**: Multi-level GROUP BY

### 3. Business Impact
- Reveals true customer quality trends
- Essential for LTV calculations
- Informs acquisition strategy (which channels produce sticky customers?)
- Identifies when product changes impacted retention

### 4. Common Interview Questions
- "How would you measure if our product is improving?"
- "Design a retention analysis for a subscription product"
- "Our DAU is growing but I'm worried about quality — how would you investigate?"
- "Compare customer quality across acquisition channels"

---

## CTE Structure

```
┌─────────────────────┐
│  customer_cohorts   │  ← Assign each customer to their cohort (first purchase month)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  customer_activity  │  ← Get all months where each customer was active
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   cohort_activity   │  ← Join cohorts + activity, calculate period numbers
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    cohort_sizes     │  ← Count total customers per cohort (denominator)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  retention_metrics  │  ← Calculate retention % per cohort per period
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← Add keys, timestamps, format output
└─────────────────────┘
```

### SQL Pattern

```sql
-- Step 1: Assign customers to cohorts
with customer_cohorts as (
    select
        customer_id,
        date_trunc('month', min(order_date)) as cohort_month
    from orders
    group by customer_id
),

-- Step 2: Get each customer's active months
customer_activity as (
    select distinct
        customer_id,
        date_trunc('month', order_date) as activity_month
    from orders
),

-- Step 3: Join and calculate period numbers
cohort_activity as (
    select
        c.cohort_month,
        a.activity_month,
        datediff('month', c.cohort_month, a.activity_month) as period_number,
        count(distinct a.customer_id) as active_customers
    from customer_cohorts c
    inner join customer_activity a using (customer_id)
    where datediff('month', c.cohort_month, a.activity_month) >= 0
    group by 1, 2, 3
),

-- Step 4: Get cohort sizes (denominator)
cohort_sizes as (
    select
        cohort_month,
        count(distinct customer_id) as cohort_size
    from customer_cohorts
    group by 1
),

-- Step 5: Calculate retention
retention_metrics as (
    select
        ca.cohort_month,
        ca.period_number,
        ca.active_customers,
        cs.cohort_size,
        (ca.active_customers::float / cs.cohort_size) * 100 as retention_rate
    from cohort_activity ca
    join cohort_sizes cs using (cohort_month)
)

select * from retention_metrics
order by cohort_month, period_number
```

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `DATE_TRUNC('month', date)` | Truncate to first of month | `DATE_TRUNC('month', order_date)` |
| `DATEDIFF('month', start, end)` | Calculate months between dates | `DATEDIFF('month', cohort, activity)` |
| `COUNT(DISTINCT)` | Count unique customers | `COUNT(DISTINCT customer_id)` |
| `INNER JOIN` / `LEFT JOIN` | Connect cohorts to activity | `JOIN activity USING (customer_id)` |

---

## Retention vs. Churn

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Retention Rate** | `active_customers / cohort_size * 100` | % of original cohort still active |
| **Churn Rate (Simple)** | `100 - retention_rate` | % of original cohort NOT active |
| **Period Churn** | `(active_prev - active_curr) / active_prev * 100` | % who left since last period |

> **Note**: Simple churn (100 - retention) tells you "% not here anymore." Period churn tells you "% who left this period." Both are useful for different questions.

---

## Common Cohort Types

| Cohort Type | Grouped By | Use Case |
|-------------|------------|----------|
| **Acquisition Cohort** | First purchase month | Most common; tracks new customer quality |
| **Behavioral Cohort** | First action (signup, trial start) | SaaS, freemium products |
| **Channel Cohort** | Acquisition source | Compare marketing channel quality |
| **Feature Cohort** | First use of feature | Measure feature impact on retention |
| **Subscription Cohort** | Subscription start date | Subscription businesses |

---

## Typical Retention Benchmarks

| Business Model | Month 1 | Month 3 | Month 12 |
|----------------|---------|---------|----------|
| **SaaS (B2B)** | 95% | 90% | 80% |
| **SaaS (B2C)** | 80% | 60% | 40% |
| **E-commerce** | 20% | 10% | 5% |
| **Mobile App** | 25% | 10% | 3% |
| **Marketplace** | 30% | 15% | 8% |

> Low retention in e-commerce is normal — most customers buy once. Focus on moving "one-time" → "repeat" buyers.

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Including current month | Partial data skews retention | Filter: `WHERE activity_month < DATE_TRUNC('month', CURRENT_DATE)` |
| Wrong JOIN type | Missing cohort members or NULLs | Use INNER JOIN for activity; ensure cohort sizes are separate |
| Negative period numbers | Activity before cohort month | Filter: `WHERE period_number >= 0` |
| Using `a.customer_id` in cohort LEFT JOIN | Counting NULLs incorrectly | Count from activity side after proper join |
| Not normalizing to cohort size | Larger cohorts appear "better" | Always divide by cohort_size |

---

## Extending the Analysis

### 1. Revenue Retention (Dollar Retention)
```sql
sum(order_value) / first_period_revenue * 100 as revenue_retention
```

### 2. Weighted Retention
```sql
-- Weight by customer value
sum(case when is_active then customer_ltv else 0 end) / sum(customer_ltv)
```

### 3. Cohort Comparison
```sql
-- Compare to previous cohort
retention_rate - lag(retention_rate) over (
    partition by period_number
    order by cohort_month
) as retention_change
```

### 4. Channel-Specific Cohorts
```sql
-- Add acquisition channel dimension
date_trunc('month', first_order_date) as cohort_month,
acquisition_channel,
```

---

## Interview Tips

1. **Start with the business question**: "Cohort analysis helps us understand if customers acquired this month are better or worse than previous months"

2. **Explain the grain clearly**: "Each row represents one cohort-period combination — for example, 'customers acquired in January, in their 3rd month'"

3. **Discuss the join logic**: "We join customers to their activity, then aggregate to count how many from each cohort were active in each period"

4. **Mention partial period handling**: "We exclude the current month to avoid incomplete data biasing our metrics"

5. **Connect to business impact**: "If retention is improving, we know product changes are working. If it's declining, we need to investigate."

---

## Practice Questions

1. Why do we use `DATE_TRUNC('month', ...)` instead of the raw date?

2. What's the difference between `COUNT(DISTINCT a.customer_id)` and `COUNT(DISTINCT c.customer_id)` in a LEFT JOIN?

3. How would you modify this analysis to track revenue retention instead of customer retention?

4. A cohort shows 100% retention in period 0 but 0.5% in period 1. Is this a data bug or expected?

5. How would you identify which acquisition channel produces the stickiest customers?

6. The PM asks "is our product improving?" — how does cohort analysis help answer this?

---

## Visual: Cohort Retention Matrix

```
                    Months Since First Purchase
Cohort      │   0   │   1   │   2   │   3   │   4   │
────────────┼───────┼───────┼───────┼───────┼───────┤
2024-01     │ 100%  │  15%  │  10%  │   7%  │   5%  │
2024-02     │ 100%  │  18%  │  12%  │   8%  │   -   │
2024-03     │ 100%  │  20%  │  14%  │   -   │   -   │  ← Improving!
2024-04     │ 100%  │  22%  │   -   │   -   │   -   │
2024-05     │ 100%  │   -   │   -   │   -   │   -   │

Reading: "Of customers acquired in Jan 2024, 15% came back in month 2"
Insight: "Month 1 retention is improving (15% → 22%), product is getting stickier"
```
