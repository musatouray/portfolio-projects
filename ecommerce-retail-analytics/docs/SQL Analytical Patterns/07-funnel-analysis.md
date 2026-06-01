# Funnel Analysis - Interview Study Guide

## What is Funnel Analysis?

Funnel Analysis tracks conversion rates through sequential stages of a process. It answers:

- "What percentage of orders get delivered?"
- "Where are customers dropping off?"
- "How long does each stage take?"

```
Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5
  100%  →   95%   →   90%   →   85%   →   40%
```

The "funnel" shape comes from progressive drop-off at each stage.

---

## Key Terms and Definitions

| Term | Definition | SQL Implementation |
|------|------------|-------------------|
| **Stage** | A step in the process | Column with timestamp or status |
| **Conversion Rate** | % that progress to next stage | `next_stage / current_stage * 100` |
| **Drop-off** | Count that didn't progress | `current_stage - next_stage` |
| **Overall Conversion** | % from first to last stage | `final_stage / first_stage * 100` |
| **Cycle Time** | Time between stages | `DATEDIFF(stage2_date, stage1_date)` |
| **Exit Rate** | % that left the process | `exits / total * 100` |

### E-commerce Order Funnel Stages

| Stage | Event | Column |
|-------|-------|--------|
| 1. Placed | Customer submits order | `order_date` |
| 2. Approved | Payment confirmed | `order_approved_at` |
| 3. Shipped | Handed to carrier | `delivered_carrier_date` |
| 4. Delivered | Customer receives | `delivered_customer_date` |
| 5. Reviewed | Customer submits review | `review_count > 0` |

---

## Why FAANG Cares

### 1. Identifies Bottlenecks
- "Where are we losing customers?"
- "Which stage has the worst conversion?"
- Focus improvement efforts on biggest drop-offs

### 2. Measures Process Efficiency
- "How long does delivery take?"
- "Are we meeting SLAs?"
- Cycle time analysis reveals operational issues

### 3. Tests SQL Skills
- **Conditional Aggregation**: `COUNT(CASE WHEN...)` or `COUNT(column)`
- **NULL Handling**: Using COUNT behavior with NULLs
- **Date Functions**: `DATEDIFF()` for cycle times
- **Percentage Calculations**: Stage-to-stage and overall rates

### 4. Common Interview Questions
- "How would you measure conversion through a checkout flow?"
- "Design a system to identify where users drop off"
- "Calculate the average time between order and delivery"
- "What percentage of orders result in a review?"

---

## CTE Structure

```
┌─────────────────────┐
│   orders_base       │  ← Get orders with stage timestamps
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ funnel_calculations │  ← Aggregate counts, calculate cycle times
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← Calculate rates, add metadata
└─────────────────────┘
```

---

## SQL Patterns

### Pattern 1: COUNT(column) for Stage Counts

Snowflake's `COUNT(column)` ignores NULLs automatically:

```sql
-- Elegant: COUNT ignores NULLs
count(*) as orders_placed,
count(order_approved_at) as orders_approved,
count(delivered_carrier_date) as orders_shipped,
count(delivered_customer_date) as orders_delivered

-- Equivalent but verbose:
count(case when order_approved_at is not null then 1 end) as orders_approved
```

### Pattern 2: Stage-to-Stage Conversion Rates

```sql
-- Each stage compared to previous stage
round(orders_approved * 100.0 / nullif(orders_placed, 0), 2) as placed_to_approved_pct,
round(orders_shipped * 100.0 / nullif(orders_approved, 0), 2) as approved_to_shipped_pct,
round(orders_delivered * 100.0 / nullif(orders_shipped, 0), 2) as shipped_to_delivered_pct
```

### Pattern 3: Exit/Cancellation Tracking

```sql
-- Track exits from the funnel
sum(case when order_status = 'canceled' then 1 else 0 end) as orders_canceled,
sum(case when order_status = 'unavailable' then 1 else 0 end) as orders_unavailable,

-- Cancellation rate
round(orders_canceled * 100.0 / nullif(orders_placed, 0), 2) as cancellation_rate
```

### Pattern 4: Cycle Time Calculations

```sql
-- Average time between stages (using seconds for decimal precision)
avg(datediff(second, order_date, order_approved_at) / 86400.0) as avg_days_to_approval,
avg(datediff(second, order_approved_at, delivered_carrier_date) / 86400.0) as avg_days_to_ship,
avg(datediff(second, delivered_carrier_date, delivered_customer_date) / 86400.0) as avg_days_in_transit
```

**Why seconds / 86400?** Gets decimal days (e.g., 2.5 days) instead of integer days.

### Pattern 5: Drop-off Counts

```sql
-- How many didn't make it to the next stage
orders_placed - orders_approved as dropped_before_approval,
orders_approved - orders_shipped as dropped_before_shipping,
orders_shipped - orders_delivered as dropped_before_delivery
```

---

## Complete SQL Example

```sql
with orders as (
    select * from {{ ref('int_orders_enriched') }}
),

funnel_calculations as (
    select
        date_trunc('month', order_date) as funnel_month,

        -- Stage counts (COUNT ignores NULLs)
        count(*) as orders_placed,
        count(order_approved_at) as orders_approved,
        count(delivered_carrier_date) as orders_shipped,
        count(delivered_customer_date) as orders_delivered,
        count(case when review_count > 0 then 1 end) as orders_reviewed,

        -- Exit counts
        sum(case when order_status = 'canceled' then 1 else 0 end) as orders_canceled,

        -- Cycle times (decimal days)
        avg(datediff(second, order_date, order_approved_at) / 86400.0) as avg_days_to_approval,
        avg(datediff(second, order_approved_at, delivered_carrier_date) / 86400.0) as avg_days_to_ship,
        avg(datediff(second, delivered_carrier_date, delivered_customer_date) / 86400.0) as avg_days_in_transit,
        avg(datediff(second, order_date, delivered_customer_date) / 86400.0) as avg_days_to_delivery
    from orders
    group by 1
),

final as (
    select
        funnel_month,
        orders_placed,
        orders_approved,
        orders_shipped,
        orders_delivered,
        orders_reviewed,
        orders_canceled,

        -- Drop-offs
        orders_placed - orders_approved as dropped_before_approval,
        orders_approved - orders_shipped as dropped_before_shipping,
        orders_shipped - orders_delivered as dropped_before_delivery,

        -- Conversion rates
        round(orders_approved * 100.0 / nullif(orders_placed, 0), 2) as placed_to_approved_pct,
        round(orders_shipped * 100.0 / nullif(orders_approved, 0), 2) as approved_to_shipped_pct,
        round(orders_delivered * 100.0 / nullif(orders_shipped, 0), 2) as shipped_to_delivered_pct,
        round(orders_reviewed * 100.0 / nullif(orders_delivered, 0), 2) as delivered_to_reviewed_pct,

        -- Overall rates
        round(orders_delivered * 100.0 / nullif(orders_placed, 0), 2) as overall_delivery_rate,
        round(orders_canceled * 100.0 / nullif(orders_placed, 0), 2) as cancellation_rate,

        -- Cycle times
        round(avg_days_to_approval, 1) as avg_days_to_approval,
        round(avg_days_to_ship, 1) as avg_days_to_ship,
        round(avg_days_in_transit, 1) as avg_days_in_transit,
        round(avg_days_to_delivery, 1) as avg_days_to_delivery
    from funnel_calculations
)

select * from final
```

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `COUNT(column)` | Count non-NULL values | `COUNT(order_approved_at)` |
| `COUNT(*)` | Count all rows | Stage 1 total |
| `SUM(CASE WHEN...)` | Conditional count | `SUM(CASE WHEN status='canceled' THEN 1 ELSE 0 END)` |
| `DATEDIFF(second, a, b) / 86400.0` | Days with decimals | Precise cycle time |
| `NULLIF(x, 0)` | Prevent division by zero | Safe percentage calc |
| `DATE_TRUNC('month', date)` | Group by month | Monthly funnel |

---

## Interpreting Funnel Results

### Healthy E-commerce Funnel

| Stage | Conversion | Benchmark |
|-------|------------|-----------|
| Placed → Approved | 98-100% | Payment success |
| Approved → Shipped | 95-99% | Fulfillment efficiency |
| Shipped → Delivered | 98-100% | Logistics reliability |
| Delivered → Reviewed | 30-50% | Customer engagement |

### Warning Signs

| Issue | Indicates |
|-------|-----------|
| Low Placed → Approved | Payment failures, fraud rejection |
| Low Approved → Shipped | Inventory issues, fulfillment problems |
| Low Shipped → Delivered | Logistics failures, address issues |
| Reviews > Deliveries | Late review submissions, data timing |

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Using `COUNT(*)` for all stages | Counts all rows, not stage completions | Use `COUNT(column)` for NULLable stages |
| Integer division | Rates are 0 or 100 | Multiply by `100.0` first |
| `DATEDIFF(day, ...)` only | Loses precision | Use seconds / 86400.0 for decimal days |
| Ignoring cancellations | Missing part of the picture | Track exits separately |
| Single-grain analysis | Misses trends | Add time dimension (monthly) |

---

## Business Applications

### 1. Operational Dashboard
```sql
-- Current month funnel health
SELECT *
FROM fct_orders_funnel
WHERE month_date = DATE_TRUNC('month', CURRENT_DATE)
```

### 2. Trend Analysis
```sql
-- Is delivery rate improving?
SELECT
    month_year,
    overall_delivery_rate,
    overall_delivery_rate - LAG(overall_delivery_rate) OVER (ORDER BY month_date) as change
FROM fct_orders_funnel
ORDER BY month_date
```

### 3. Bottleneck Identification
```sql
-- Which stage has the biggest drop-off?
SELECT
    month_year,
    dropped_before_approval,
    dropped_before_shipping,
    dropped_before_delivery,
    GREATEST(dropped_before_approval, dropped_before_shipping, dropped_before_delivery) as biggest_dropoff
FROM fct_orders_funnel
```

### 4. SLA Monitoring
```sql
-- Are we meeting delivery SLAs?
SELECT
    month_year,
    avg_days_to_delivery,
    CASE WHEN avg_days_to_delivery <= 14 THEN 'Met' ELSE 'Missed' END as sla_status
FROM fct_orders_funnel
```

---

## Interview Tips

1. **Start with business context**: "Funnel analysis helps identify where we're losing customers in the process, so we can focus improvement efforts"

2. **Explain COUNT behavior**: "I use COUNT(column) because it automatically ignores NULLs — only counting orders that reached that stage"

3. **Discuss granularity**: "I chose monthly grain to see trends over time while reducing noise from daily fluctuations"

4. **Mention exits**: "I track cancellations separately because they explain part of the drop-off between stages"

5. **Connect to action**: "A 5% drop between shipped and delivered tells us to investigate logistics partners or address quality"

---

## Practice Questions

1. Why does `COUNT(order_approved_at)` work better than `COUNT(CASE WHEN order_approved_at IS NOT NULL THEN 1 END)`?

2. Your funnel shows 105% conversion from Delivered to Reviewed. What could cause this?

3. How would you modify this analysis to show funnel by product category?

4. The PM asks "why did our delivery rate drop in December?" — what additional data would you look at?

5. How would you calculate the "drop-off rate" at each stage instead of the "conversion rate"?

6. If cycle time increased but conversion stayed the same, what might that indicate?

---

## Related Patterns

| Pattern | Relationship to Funnel |
|---------|------------------------|
| **Cohort Analysis** | Funnel conversion by acquisition cohort |
| **Time Intelligence** | Funnel trends over time (MoM, YoY) |
| **Churn Indicators** | Post-purchase funnel (repeat purchase rate) |
| **Pareto Analysis** | Which products have best funnel conversion? |

---

## Extensions

### Funnel by Dimension
```sql
-- Funnel by customer state
SELECT
    customer_state,
    count(*) as orders_placed,
    count(delivered_customer_date) as orders_delivered,
    round(count(delivered_customer_date) * 100.0 / count(*), 2) as delivery_rate
FROM orders
JOIN customers USING (customer_id)
GROUP BY 1
ORDER BY delivery_rate DESC
```

### Time-to-Stage Distribution
```sql
-- Distribution of delivery times
SELECT
    CASE
        WHEN days_to_delivery <= 7 THEN '0-7 days'
        WHEN days_to_delivery <= 14 THEN '8-14 days'
        WHEN days_to_delivery <= 21 THEN '15-21 days'
        ELSE '22+ days'
    END as delivery_bucket,
    COUNT(*) as order_count
FROM orders
WHERE delivered_customer_date IS NOT NULL
GROUP BY 1
```
