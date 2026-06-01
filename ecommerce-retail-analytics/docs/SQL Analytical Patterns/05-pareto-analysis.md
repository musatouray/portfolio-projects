# Pareto Analysis (80/20 Rule) - Interview Study Guide

## What is Pareto Analysis?

Pareto Analysis identifies the "vital few" that drive the majority of results. Named after economist Vilfredo Pareto, who observed that 80% of Italy's land was owned by 20% of the population.

In e-commerce, this translates to:
- Which **20% of products** generate **80% of revenue**?
- Which **20% of customers** drive **80% of sales**?
- Which **20% of sellers** account for **80% of GMV**?

```
All Items → Rank by Value → Calculate Cumulative % → Classify (A/B/C)
```

---

## Key Terms and Definitions

| Term | Definition | SQL Implementation |
|------|------------|-------------------|
| **Cumulative Sum** | Running total up to current row | `SUM() OVER (ORDER BY x DESC)` |
| **Cumulative %** | Running total as % of grand total | `cumulative_sum / grand_total * 100` |
| **ABC Classification** | Segmenting items by contribution | A=80%, B=80-95%, C=95-100% |
| **Pareto Principle** | 80/20 rule | ~20% of items drive ~80% of value |
| **Grand Total** | Sum across all items | `SUM() OVER ()` |
| **Revenue Rank** | Position when sorted by value | `ROW_NUMBER() OVER (ORDER BY revenue DESC)` |

### ABC Classification Thresholds

| Segment | Cumulative Revenue % | Typical Item % | Business Action |
|---------|---------------------|----------------|-----------------|
| **A** | 0-80% | ~20% | High priority, maximize availability |
| **B** | 80-95% | ~30% | Moderate priority, standard treatment |
| **C** | 95-100% | ~50% | Low priority, consider discontinuing |

---

## Why FAANG Cares

### 1. Resource Optimization
- Focus inventory investment on high-impact products
- Prioritize engineering effort on critical systems
- Allocate support resources to top customers

### 2. Strategic Focus
- "What should we double down on?"
- "What can we deprioritize or sunset?"
- Data-driven prioritization over gut feeling

### 3. Tests SQL Skills
- **Window Functions**: `SUM() OVER`, `ROW_NUMBER()`
- **Cumulative Calculations**: Running totals
- **Percentage Calculations**: Avoiding integer division
- **CASE Expressions**: ABC classification

### 4. Common Interview Questions
- "How would you identify which products to focus on?"
- "Design a system to classify inventory by importance"
- "How would you validate the 80/20 rule in our data?"
- "What percentage of customers drive most of our revenue?"

---

## CTE Structure

```
┌─────────────────────┐
│   entity_metrics    │  ← Aggregate metrics per entity (product/customer/seller)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  ranked_entities    │  ← Pre-compute totals, calculate cumulative sums
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ pareto_calculations │  ← Calculate cumulative percentages
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← ABC classification, round output
└─────────────────────┘
```

### SQL Pattern

```sql
with product_revenue as (
    select
        product_id,
        product_category,
        sum(price) as total_revenue,
        count(*) as total_orders
    from order_items
    group by 1, 2
    having sum(price) > 0  -- Exclude zero-revenue items
),

ranked_products as (
    select
        *,
        -- Pre-compute denominators
        sum(total_revenue) over () as grand_total_revenue,
        count(*) over () as total_product_count,

        -- Cumulative sum (use tie-breaker for determinism)
        sum(total_revenue) over (
            order by total_revenue desc, product_id asc
        ) as cumulative_revenue,

        -- Rank for display
        row_number() over (
            order by total_revenue desc, product_id asc
        ) as revenue_rank
    from product_revenue
),

pareto_calculations as (
    select
        *,
        -- Cumulative revenue percentage (multiply first to avoid integer division)
        cumulative_revenue * 100.0 / nullif(grand_total_revenue, 0)
            as cumulative_revenue_pct,

        -- Cumulative product percentage
        revenue_rank * 100.0 / nullif(total_product_count, 0)
            as cumulative_product_pct
    from ranked_products
)

select
    product_id,
    product_category,
    total_revenue,
    revenue_rank,
    round(cumulative_revenue_pct, 2) as cumulative_revenue_pct,
    round(cumulative_product_pct, 2) as cumulative_product_pct,
    case
        when cumulative_revenue_pct <= 80 then 'A'
        when cumulative_revenue_pct <= 95 then 'B'
        else 'C'
    end as pareto_segment
from pareto_calculations
```

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `SUM() OVER (ORDER BY x DESC)` | Running total | Cumulative revenue |
| `SUM() OVER ()` | Grand total | Total revenue for % calculation |
| `ROW_NUMBER() OVER (ORDER BY x DESC)` | Rank items | Revenue rank 1, 2, 3... |
| `COUNT(*) OVER ()` | Total count | Number of products |
| `* 100.0 /` | Avoid integer division | Force decimal result |
| `NULLIF(x, 0)` | Prevent division by zero | Safe percentage calc |

---

## Critical Implementation Details

### 1. Deterministic Ordering

**Problem**: Ties in revenue cause non-deterministic results across runs.

**Solution**: Add a secondary sort key (tie-breaker):
```sql
ORDER BY total_revenue DESC, product_id ASC
```

### 2. Integer Division

**Problem**: `row_number() / count(*)` returns 0 for most rows.

**Solution**: Multiply by 100.0 first:
```sql
-- Wrong: integer division
row_number() / count(*) * 100

-- Correct: decimal division
row_number() * 100.0 / count(*)
```

### 3. Zero-Revenue Items

**Problem**: Products with no sales skew the percentage calculations.

**Solution**: Filter them out:
```sql
WHERE total_revenue > 0
```

### 4. Pre-computing Denominators

**Optimization**: Calculate grand totals once, reference in later CTEs:
```sql
sum(total_revenue) over () as grand_total_revenue,
count(*) over () as total_product_count
```

---

## Interpreting Results

### Validating 80/20

Query to check if your data follows Pareto:
```sql
SELECT
    pareto_segment,
    COUNT(*) as product_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct_of_products,
    ROUND(SUM(total_revenue), 2) as segment_revenue
FROM fct_pareto_products
GROUP BY 1
ORDER BY 1
```

**Expected output** (approximately):
| Segment | % of Products | % of Revenue |
|---------|---------------|--------------|
| A | ~20-30% | 80% |
| B | ~30-40% | 15% |
| C | ~40-50% | 5% |

### When 80/20 Doesn't Hold

- **More concentrated** (90/10): Few products dominate — high risk if they fail
- **More distributed** (70/30): Diverse portfolio — harder to prioritize
- Both insights are valuable for strategy

---

## Business Applications

### 1. Inventory Management
```sql
-- Segment A: Never run out of stock
-- Segment C: Consider discontinuing slow movers
SELECT pareto_segment, COUNT(*), SUM(total_revenue)
FROM fct_pareto_products
GROUP BY 1
```

### 2. Customer Prioritization
```sql
-- Top 20% of customers for VIP program
SELECT * FROM fct_pareto_customers
WHERE pareto_segment = 'A'
```

### 3. Seller Quality Focus
```sql
-- Which sellers should we invest in supporting?
SELECT * FROM fct_pareto_sellers
WHERE pareto_segment = 'A'
ORDER BY total_revenue DESC
```

### 4. Category Analysis
```sql
-- Which categories have the most "A" products?
SELECT
    product_category,
    COUNT(*) FILTER (WHERE pareto_segment = 'A') as a_products,
    COUNT(*) as total_products
FROM fct_pareto_products
GROUP BY 1
ORDER BY a_products DESC
```

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Non-deterministic results | Ties cause different rankings | Add tie-breaker: `ORDER BY revenue DESC, id ASC` |
| Integer division | Percentages always 0 | Use `* 100.0 /` not `/ * 100` |
| Including zero-revenue | Skews percentages | Filter: `WHERE revenue > 0` |
| Wrong window frame | Cumulative sum includes wrong rows | Default frame with ORDER BY is correct |
| Using DENSE_RANK for % | Ties share same rank, % is wrong | Use ROW_NUMBER for percentage calculations |

---

## Interview Tips

1. **Start with business context**: "Pareto helps us focus resources on what matters most — typically 20% of items drive 80% of results"

2. **Explain the window function**: "We use SUM() OVER with ORDER BY to get a running total, then divide by the grand total to get cumulative percentage"

3. **Mention the tie-breaker**: "I add a secondary sort key like product_id to ensure deterministic results across runs"

4. **Discuss integer division**: "I multiply by 100.0 first to force decimal division — a common SQL gotcha"

5. **Connect to decisions**: "This directly informs inventory investment, customer prioritization, and resource allocation"

---

## Practice Questions

1. Why do we use `ORDER BY total_revenue DESC, product_id ASC` instead of just `ORDER BY total_revenue DESC`?

2. What's wrong with this calculation: `row_number() / count(*) * 100`?

3. If Segment A contains 40% of products (not 20%), what does that tell you about the business?

4. How would you modify this analysis to show Pareto by category (each category has its own 80/20)?

5. A PM asks "which products should we discontinue?" — how would you use this model to answer?

6. How would you calculate the "Pareto ratio" — the exact percentage of products that drive 80% of revenue?

---

## Related Patterns

| Pattern | Relationship to Pareto |
|---------|------------------------|
| **RFM Analysis** | M (Monetary) score relates to customer-level Pareto |
| **CLV** | High-CLV customers often in Pareto Segment A |
| **Cohort Analysis** | Which cohorts have the most Segment A customers? |
| **Time Intelligence** | Has Pareto concentration changed over time? |

---

## Extensions

### Time-Based Pareto
Track how rankings change month-over-month:
```sql
SELECT
    year_month,
    product_id,
    revenue_rank,
    LAG(revenue_rank) OVER (PARTITION BY product_id ORDER BY year_month) as prev_rank
FROM monthly_pareto
```

### Multi-Dimensional Pareto
Combine product and customer Pareto:
```sql
-- "A" products bought by "A" customers = critical combinations
SELECT *
FROM orders o
JOIN fct_pareto_products p ON o.product_id = p.product_id
JOIN fct_pareto_customers c ON o.customer_id = c.customer_id
WHERE p.pareto_segment = 'A' AND c.pareto_segment = 'A'
```
