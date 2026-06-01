# Customer Lifetime Value (CLV) - Interview Study Guide

## What is Customer Lifetime Value?

Customer Lifetime Value (CLV or LTV) predicts the total revenue a customer will generate throughout their relationship with your business. It answers: "How much is this customer worth to us?"

CLV is critical for:
- **Acquisition decisions**: How much can we spend to acquire a customer? (CAC < CLV)
- **Segmentation**: Which customers deserve VIP treatment?
- **Forecasting**: What's the expected revenue from our customer base?
- **Resource allocation**: Where should we invest in retention?

```
Historical Behavior → Apply Prediction Model → Estimate Future Value → Inform Decisions
```

---

## Key Terms and Definitions

| Term | Definition | SQL Implementation |
|------|------------|-------------------|
| **Historical CLV** | Total revenue a customer has already generated | `SUM(order_value)` per customer |
| **Predicted CLV** | Estimated future revenue based on behavior patterns | Cohort averages, statistical models |
| **Average Order Value (AOV)** | Average revenue per order | `total_revenue / total_orders` |
| **Purchase Frequency** | Orders per time period | `total_orders / tenure_months` |
| **Customer Lifespan** | Expected active duration | Derived from cohort retention curves |
| **Cohort Benchmark** | Average CLV for customers in the same acquisition cohort | `AVG(revenue) GROUP BY cohort_month` |
| **Expected LTV** | What we expect an average customer to be worth | Cohort average CLV |
| **Value vs Cohort** | How customer compares to peers | `historical_clv - cohort_avg` |

### CLV Calculation Approaches

| Approach | Formula | Best For |
|----------|---------|----------|
| **Historical** | `SUM(past_revenue)` | Reporting past value |
| **Simple Formula** | `AOV × Frequency × Lifespan` | Quick estimates |
| **Cohort-Based** | Use mature cohort averages | Comparing acquisition quality |
| **Probabilistic (BG/NBD)** | Statistical modeling | Accurate predictions at scale |

---

## Why FAANG Cares

### 1. Unit Economics
- "Does acquiring this customer make money?"
- `CLV > CAC` = profitable customer
- Determines sustainable growth rate

### 2. Resource Prioritization
- "Which customers deserve premium support?"
- "Where should we focus retention efforts?"
- High-CLV customers get more investment

### 3. Growth Strategy
- "Which acquisition channels bring valuable customers?"
- "Are newer cohorts more or less valuable?"
- Informs marketing spend allocation

### 4. Tests SQL Skills
- **Aggregations**: Customer-level metrics
- **Window Functions**: Percentile-based segments
- **Joins**: Cohort benchmarks
- **CASE/GREATEST**: Prediction logic

### 5. Common Interview Questions
- "How would you calculate customer lifetime value?"
- "Design a system to identify high-value customers"
- "How would you predict which customers will be most valuable?"
- "How do you decide how much to spend acquiring customers?"

---

## CTE Structure

```
┌─────────────────────┐
│   customer_base     │  ← Get customer metrics from dim_customers
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  cohort_benchmarks  │  ← Get avg CLV per cohort (prediction baseline)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  clv_calculations   │  ← Calculate historical, expected, predicted CLV
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   clv_segments      │  ← Assign percentile-based segments (NTILE)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← Add keys, timestamps
└─────────────────────┘
```

### SQL Pattern

```sql
-- Customer Lifetime Value calculation
with customer_base as (
    select
        customer_unique_id,
        cohort_key,
        total_orders,
        total_revenue as historical_clv,
        average_order_value
    from dim_customers
    where total_orders > 0  -- Exclude prospects
),

cohort_benchmarks as (
    select
        cohort_key,
        avg_customer_value as cohort_avg_clv
    from dim_cohorts
),

clv_calculations as (
    select
        cb.customer_unique_id,
        cb.cohort_key,
        cb.historical_clv,
        cbm.cohort_avg_clv as expected_ltv,
        -- Predicted: at minimum, expect them to reach cohort average
        greatest(cb.historical_clv, cbm.cohort_avg_clv) as predicted_ltv,
        -- Value vs expectation
        cb.historical_clv - cbm.cohort_avg_clv as value_vs_cohort
    from customer_base cb
    left join cohort_benchmarks cbm using (cohort_key)
),

clv_segments as (
    select
        *,
        ntile(10) over (order by predicted_ltv asc) as clv_decile,
        case
            when ntile(10) over (order by predicted_ltv asc) = 10 then 'Platinum'
            when ntile(10) over (order by predicted_ltv asc) >= 8 then 'Gold'
            when ntile(10) over (order by predicted_ltv asc) >= 5 then 'Silver'
            else 'Bronze'
        end as clv_segment
    from clv_calculations
)

select * from clv_segments
```

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `GREATEST(a, b)` | Return larger value | `GREATEST(historical, cohort_avg)` |
| `NTILE(10)` | Divide into 10 equal buckets (deciles) | `NTILE(10) OVER (ORDER BY clv)` |
| `AVG() ... GROUP BY` | Cohort benchmarks | `AVG(revenue) GROUP BY cohort_month` |
| Arithmetic | Value comparison | `historical_clv - cohort_avg` |

---

## CLV Prediction Approaches

### 1. Simple Formula
```sql
clv = avg_order_value * purchase_frequency * expected_lifespan
```
- **Pros**: Easy to understand, quick to implement
- **Cons**: Assumes constant behavior, ignores customer differences

### 2. Cohort-Based (Used in Our Model)
```sql
predicted_ltv = greatest(historical_clv, cohort_avg_clv)
```
- **Pros**: Uses actual cohort behavior, accounts for maturity
- **Cons**: Assumes customer will match cohort average

### 3. Probabilistic (BG/NBD + Gamma-Gamma)
- **Pros**: Statistically rigorous, handles uncertainty
- **Cons**: Complex to implement, requires more data

### When to Use Each
| Approach | Use When |
|----------|----------|
| Simple Formula | Quick estimates, early-stage companies |
| Cohort-Based | Comparing acquisition quality, historical analysis |
| Probabilistic | Production systems, precise predictions needed |

---

## CLV Segmentation

### Percentile-Based Segments

| Segment | Decile | Description |
|---------|--------|-------------|
| **Platinum** | 10 (top 10%) | VIP treatment, exclusive offers |
| **Gold** | 8-9 (next 20%) | Loyalty programs, priority support |
| **Silver** | 5-7 (next 30%) | Nurture campaigns, upsell opportunities |
| **Bronze** | 1-4 (bottom 40%) | Standard service, efficiency focus |

### Why Not Equal Revenue Buckets?
Using percentiles ensures:
- Each segment has manageable customer count
- Clear actionability (top 10% = Platinum)
- Stable segment boundaries

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Predicting "average" for everyone | High spenders get undervalued | Use `GREATEST(historical, expected)` |
| Ignoring cohort maturity | New cohorts look less valuable | Compare at same cohort age |
| Not excluding prospects | Division by zero, skewed averages | Filter: `WHERE total_orders > 0` |
| Wrong NTILE order | Segments inverted | `ORDER BY ASC` for high decile = high value |
| AVG of AVG | Statistically incorrect | Sum totals, then divide |

---

## Business Applications

### 1. Customer Acquisition
```
Max CAC = CLV × Target Margin
If CLV = $200 and target margin = 25%
Max CAC = $200 × 0.25 = $50
```

### 2. Retention Investment
```
High CLV customers → Invest heavily in retention
Low CLV customers → Automate, efficiency focus
```

### 3. Marketing Personalization
```
Platinum → Premium offers, early access
Gold → Loyalty rewards
Silver → Nurture to increase frequency
Bronze → Re-activation or efficiency
```

### 4. Revenue Forecasting
```
Expected Revenue = SUM(predicted_ltv) for customer base
```

---

## Interview Tips

1. **Start with business context**: "CLV helps us understand how much each customer is worth so we can make smart acquisition and retention decisions"

2. **Explain the prediction logic**: "We use cohort averages as a baseline — if similar customers spent $200 on average, we expect new customers to reach that level"

3. **Discuss the GREATEST() logic**: "We don't want to downgrade high spenders to the average, so we take the maximum of their actual value and the expected value"

4. **Connect to business impact**: "This lets us calculate max CAC, prioritize retention, and forecast revenue"

5. **Mention limitations**: "This is a simplified model — production systems might use probabilistic models like BG/NBD"

---

## Practice Questions

1. A customer has historical_clv of $500 and their cohort average is $150. What should their predicted_ltv be and why?

2. Why do we use `GREATEST()` instead of just using the cohort average for predictions?

3. How would you modify this model for a subscription business with monthly recurring revenue?

4. What's the problem with calculating `AVG(average_order_value)` across customers?

5. A PM asks "should we acquire customers from Channel A (avg CLV = $100) or Channel B (avg CLV = $80)?" — what other factors should you consider?

6. How would you validate that your CLV predictions are accurate?

---

## Related Patterns

| Pattern | Relationship to CLV |
|---------|---------------------|
| **RFM Analysis** | RFM segments can predict CLV (Champions = high CLV) |
| **Cohort Analysis** | Cohort retention informs expected lifespan |
| **Churn Prediction** | Churned customers have capped CLV |
| **Pareto Analysis** | Often 20% of customers drive 80% of CLV |
