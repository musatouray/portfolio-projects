# RFM Analysis - Interview Study Guide

## What is RFM Analysis?

RFM is a customer segmentation technique that scores customers based on three behavioral dimensions derived from transaction history. It's a rules-based approach that doesn't require machine learning, making it fast to implement and easy to explain to stakeholders.

RFM segments customers into actionable groups (Champions, At Risk, Hibernating, etc.) that marketing teams can target with personalized campaigns.

```
Customer Transactions → R, F, M Scores → Segments → Marketing Actions
```

---

## Key Terms and Definitions

| Term | Definition | SQL Implementation |
|------|------------|-------------------|
| **Recency (R)** | How recently did the customer make a purchase? Measured in days since last order. Lower = better. | `DATEDIFF(day, last_order_date, reference_date)` |
| **Frequency (F)** | How often does the customer purchase? Measured as total order count. Higher = better. | `COUNT(DISTINCT order_id)` |
| **Monetary (M)** | How much does the customer spend? Measured as total revenue. Higher = better. | `SUM(order_value)` |
| **NTILE(n)** | Window function that divides rows into n buckets. Used to create scores 1-5. | `NTILE(5) OVER (ORDER BY metric)` |
| **Reference Date** | The anchor date for recency calculation. Use `MAX(order_date)` for historical data, `CURRENT_DATE` for live data. | `SELECT MAX(order_date) FROM orders` |
| **RFM Score** | Combined score (e.g., "555" for best customers). Can be concatenated or summed. | `CONCAT(r_score, f_score, m_score)` |
| **Segment** | Business classification based on score combinations (Champions, At Risk, etc.). | `CASE WHEN r >= 4 AND f >= 4 THEN 'Champions'...` |

### Common Segments

| Segment | R | F | M | Business Action |
|---------|---|---|---|-----------------|
| **Champions** | High | High | High | Reward, early access, referral program |
| **Loyal** | Med-High | High | High | Upsell, cross-sell |
| **Potential Loyalists** | High | Med | Med | Nurture to increase frequency |
| **New Customers** | High | Low | Any | Onboarding, drive second purchase |
| **At Risk** | Med | Med-High | Med-High | Win-back campaigns |
| **Can't Lose Them** | Low | High | High | Urgent personal outreach |
| **Hibernating** | Low | Low | Low | Low-cost reactivation or let go |

---

## Why FAANG Cares

### 1. Scalable Customer Segmentation
- Works on millions of customers without ML infrastructure
- Results are deterministic and reproducible
- Easy to explain to non-technical stakeholders

### 2. Tests Core SQL Skills
- **Window Functions**: `NTILE()`, `DENSE_RANK()`, `ROW_NUMBER()`
- **Aggregations**: `COUNT()`, `SUM()`, `MAX()`
- **CASE Expressions**: Complex conditional logic
- **Date Functions**: `DATEDIFF()`, date arithmetic

### 3. Business Impact
- Directly drives marketing ROI
- Identifies high-value customers to protect
- Reveals at-risk customers before they churn
- Enables personalization at scale

### 4. Common Interview Questions
- "How would you segment customers for a marketing campaign?"
- "Design a system to identify customers likely to churn"
- "How do you prioritize which customers to contact?"

---

## CTE Structure

```
┌─────────────────────┐
│   reference_date    │  ← Anchor date for recency calculation
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  customer_metrics   │  ← Calculate raw R, F, M values per customer
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    rfm_scores       │  ← Apply NTILE(5) to create 1-5 scores
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   rfm_segments      │  ← Map scores to business segments via CASE
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← Add surrogate keys, timestamps
└─────────────────────┘
```

### SQL Pattern

```sql
-- Step 1: Get reference date
with reference_date as (
    select max(order_date) as max_date
    from orders
),

-- Step 2: Calculate raw metrics per customer
customer_metrics as (
    select
        customer_id,
        datediff(day, max(order_date), rd.max_date) as recency,
        count(distinct order_id) as frequency,
        sum(order_value) as monetary
    from orders
    cross join reference_date rd
    group by customer_id, rd.max_date
),

-- Step 3: Score using NTILE
rfm_scores as (
    select
        customer_id,
        recency,
        frequency,
        monetary,
        -- Note: DESC for recency (lower days = higher score)
        ntile(5) over (order by recency desc) as r_score,
        ntile(5) over (order by frequency asc) as f_score,
        ntile(5) over (order by monetary asc) as m_score
    from customer_metrics
),

-- Step 4: Assign segments
rfm_segments as (
    select
        *,
        case
            when r_score >= 4 and f_score >= 4 and m_score >= 4 then 'Champions'
            when r_score <= 2 and f_score >= 4 and m_score >= 4 then 'Cant Lose Them'
            when r_score >= 3 and f_score >= 4 then 'Loyal'
            when r_score >= 4 and f_score in (2, 3) then 'Potential Loyalists'
            when r_score >= 4 and f_score = 1 then 'New Customers'
            when r_score in (2, 3) and f_score >= 3 then 'At Risk'
            when r_score <= 2 and f_score <= 2 then 'Hibernating'
            else 'Need Attention'
        end as rfm_segment
    from rfm_scores
)

select * from rfm_segments
```

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `NTILE(5)` | Divide into 5 equal buckets | `NTILE(5) OVER (ORDER BY revenue)` |
| `DATEDIFF()` | Calculate days between dates | `DATEDIFF(day, order_date, current_date)` |
| `CASE WHEN` | Conditional segment assignment | `CASE WHEN r >= 4 THEN 'Recent'` |
| `CROSS JOIN` | Attach reference date to all rows | `FROM customers CROSS JOIN ref_date` |

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Using `CURRENT_DATE` on historical data | All customers appear churned | Use `MAX(order_date)` as reference |
| Narrow segment definitions | Too many fall into "Other" | Use `>=` instead of exact matches |
| Forgetting "Can't Lose Them" | High-value churning customers missed | Check for low R + high F/M |
| Wrong NTILE order | Scores inverted | Recency: `ORDER BY DESC`, F/M: `ORDER BY ASC` |
| Including prospects | NULL metrics cause errors | Filter: `WHERE total_orders > 0` |

---

## Interview Tips

1. **Start with business context**: "RFM helps us identify which customers to prioritize for different campaigns"

2. **Explain the trade-offs**: "We use NTILE for simplicity, but it forces equal bucket sizes. PERCENTILE_CONT would give more control."

3. **Discuss segment ordering**: "CASE WHEN evaluates top-to-bottom, so we check specific segments (Champions) before catch-alls (Need Attention)"

4. **Mention extensions**: "We could weight F and M differently, or add a 4th dimension like product category affinity"

---

## Practice Questions

1. Why do we use `ORDER BY recency DESC` but `ORDER BY frequency ASC` in NTILE?

2. A customer has R=1, F=5, M=5. What segment should they be in and why is this urgent?

3. How would you modify RFM for a subscription business vs. transactional e-commerce?

4. What happens if two customers have identical metrics? How does NTILE handle ties?

5. How would you validate that your RFM segments are actually predictive of future behavior?
