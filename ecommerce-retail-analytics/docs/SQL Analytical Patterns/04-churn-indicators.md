# Churn Indicators - Interview Study Guide

## What is Churn Analysis?

Churn analysis identifies customers who have stopped purchasing (churned) or are at risk of churning. It answers: "Which customers are we losing, and who might we lose next?"

For e-commerce (transactional, not subscription), churn isn't a single cancellation event — it's **gradual disengagement**. We look for behavioral signals indicating a customer is slipping away.

```
Active Customer → Warning Signs (Cooling) → At Risk → Churned
```

---

## Key Terms and Definitions

| Term | Definition | SQL Implementation |
|------|------------|-------------------|
| **Churned** | No purchase in X days (e.g., 90+) | `days_since_last_order > 90` |
| **At Risk** | Approaching churn threshold | `days_since_last_order BETWEEN 60 AND 90` |
| **Cooling** | Activity declining | `days_since_last_order BETWEEN 30 AND 60` |
| **Active** | Recent purchase | `days_since_last_order < 30` |
| **Dormancy** | Days since last purchase | `DATEDIFF(day, last_order_date, reference_date)` |
| **Single Purchaser** | Only one order ever | `total_orders = 1` |
| **Win-Back** | Returned after being churned | Ordered after 90+ day gap |
| **Churn Risk Score** | Composite score (0-100) | Additive scoring model |

### Churn Status Thresholds (E-commerce)

| Status | Days Since Last Purchase | Action |
|--------|--------------------------|--------|
| Active | 0-30 | Maintain engagement |
| Cooling | 31-60 | Early intervention |
| At Risk | 61-90 | Aggressive re-engagement |
| Churned | 90+ | Win-back campaign |

---

## Why FAANG Cares

### 1. Retention Economics
- Acquiring new customers costs **5-7x more** than retaining existing ones
- A 5% increase in retention can increase profits by 25-95%
- Churn directly impacts revenue forecasts

### 2. Proactive vs Reactive
- Identify at-risk customers **before** they leave
- Intervene while there's still a chance
- Prioritize by risk score and customer value

### 3. Tests SQL Skills
- **Date Functions**: `DATEDIFF()`, date arithmetic
- **CASE Expressions**: Status assignment, scoring
- **Boolean Logic**: Flag creation
- **Additive Scoring**: Composite metrics

### 4. Common Interview Questions
- "How would you identify customers at risk of churning?"
- "Design a system to prioritize retention efforts"
- "What signals indicate a customer might leave?"
- "How would you measure the effectiveness of a win-back campaign?"

---

## CTE Structure

```
┌─────────────────────┐
│   reference_date    │  ← Anchor date for dormancy calculation
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   customer_base     │  ← Get customer metrics from dim_customers
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   churn_metrics     │  ← Calculate dormancy, flags, status
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  churn_risk_score   │  ← Calculate composite risk score (0-100)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← Add risk segments, keys, timestamps
└─────────────────────┘
```

### SQL Pattern

```sql
-- Churn risk calculation with additive scoring
with reference_date as (
    select max(order_date) as max_date
    from orders
),

customer_base as (
    select
        customer_id,
        last_order_date,
        total_orders,
        total_revenue,
        average_rating
    from dim_customers
    where total_orders > 0
),

churn_metrics as (
    select
        cb.*,
        datediff(day, cb.last_order_date, r.max_date) as days_since_last_order,
        (cb.total_orders = 1) as is_single_purchaser,
        case
            when datediff(day, cb.last_order_date, r.max_date) > 90 then 'Churned'
            when datediff(day, cb.last_order_date, r.max_date) > 60 then 'At Risk'
            when datediff(day, cb.last_order_date, r.max_date) > 30 then 'Cooling'
            else 'Active'
        end as churn_status,
        case
            when cb.average_rating >= 4.5 then 'promoter'
            when cb.average_rating >= 3.0 then 'neutral'
            when cb.average_rating is not null then 'detractor'
            else 'unknown'
        end as nps_segment
    from customer_base cb
    cross join reference_date r
),

churn_risk_score as (
    select
        *,
        -- Additive scoring (0-100)
        (
            -- Dormancy: 0-40 points
            case
                when churn_status = 'Churned' then 40
                when churn_status = 'At Risk' then 30
                when churn_status = 'Cooling' then 15
                else 0
            end
            -- Single purchaser: +25 points
            + case when is_single_purchaser then 25 else 0 end
            -- Detractor: +20 points
            + case when nps_segment = 'detractor' then 20
                   when nps_segment = 'unknown' then 10
                   else 0 end
            -- Low value: +15 points
            + case when total_revenue < 100 then 15 else 0 end
        ) as churn_risk_score
    from churn_metrics
)

select
    *,
    case
        when churn_risk_score >= 75 then 'Critical'
        when churn_risk_score >= 50 then 'High'
        when churn_risk_score >= 25 then 'Medium'
        else 'Low'
    end as churn_risk_segment
from churn_risk_score
```

---

## Churn Risk Scoring Model

### Additive Scoring Approach

Each risk factor contributes points to a 0-100 composite score:

| Factor | Points | Logic |
|--------|--------|-------|
| **Dormancy** | 0-40 | Churned=40, At Risk=30, Cooling=15, Active=0 |
| **Single Purchaser** | 0-25 | One-time buyers are high risk |
| **Detractor NPS** | 0-20 | Unhappy customers churn faster |
| **Low Value** | 0-15 | Less invested in relationship |

**Maximum Score**: 100 (40+25+20+15)

### Risk Segments

| Segment | Score Range | Action |
|---------|-------------|--------|
| **Critical** | 75-100 | Immediate intervention, win-back |
| **High** | 50-74 | Proactive outreach |
| **Medium** | 25-49 | Monitor, nurture |
| **Low** | 0-24 | Maintain engagement |

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `DATEDIFF()` | Calculate days between dates | `DATEDIFF(day, last_order, today)` |
| `CASE WHEN` | Assign status/scores | `CASE WHEN days > 90 THEN 'Churned'` |
| Boolean expression | Create flags | `(total_orders = 1) as is_single_purchaser` |
| Additive CASE | Composite scoring | `CASE ... END + CASE ... END` |

---

## Churn Signals

### Behavioral Signals

| Signal | Why It Matters | How to Measure |
|--------|----------------|----------------|
| **Dormancy** | Primary churn indicator | Days since last purchase |
| **Declining Frequency** | Slowing engagement | Compare recent vs historical purchase rate |
| **Single Purchase** | Never formed habit | `total_orders = 1` |
| **Decreasing AOV** | Less invested | Compare recent vs average order value |
| **Cart Abandonment** | Losing interest | (If tracked) abandoned cart rate |

### Satisfaction Signals

| Signal | Why It Matters | How to Measure |
|--------|----------------|----------------|
| **Low Review Score** | Dissatisfied | Average rating < 3 |
| **Support Tickets** | Having problems | (If tracked) ticket frequency |
| **Returns** | Product issues | Return rate |

### Value-Based Signals

| Signal | Why It Matters | How to Measure |
|--------|----------------|----------------|
| **Low CLV** | Less to lose | Below median revenue |
| **No Repeat Purchase** | Never returned | `total_orders = 1` |

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Using current_date on historical data | Everyone looks churned | Use `MAX(order_date)` as reference |
| Equal weight for all signals | Dormancy should matter most | Weight dormancy higher (40/100) |
| Ignoring customer value | Treating all churners equally | Combine risk score with CLV |
| Hard cutoffs only | Miss nuance | Use composite scoring |
| Not considering NPS | Satisfaction predicts churn | Include review scores |

---

## Business Applications

### 1. Prioritized Outreach
```
SELECT * FROM fct_churn_risk
JOIN fct_clv_customer USING (customer_unique_id)
WHERE churn_risk_segment = 'Critical'
  AND clv_segment IN ('Platinum', 'Gold')
ORDER BY clv_score DESC
```
→ High-value customers at critical risk = top priority

### 2. Win-Back Campaign Targeting
```
SELECT * FROM fct_churn_risk
WHERE churn_status = 'Churned'
  AND days_since_last_order BETWEEN 90 AND 180
  AND total_orders > 1
```
→ Reachable churned customers who were once engaged

### 3. Early Warning Dashboard
```
SELECT churn_risk_segment, COUNT(*), AVG(churn_risk_score)
FROM fct_churn_risk
GROUP BY 1
```
→ Monitor customer health over time

### 4. Intervention Effectiveness
```
-- Track if at-risk customers from last month are still customers
SELECT
    prior_month.churn_risk_segment,
    COUNT(CASE WHEN current.churn_status = 'Active' THEN 1 END) as retained,
    COUNT(*) as total
FROM prior_month_snapshot prior_month
LEFT JOIN fct_churn_risk current USING (customer_unique_id)
GROUP BY 1
```

---

## Interview Tips

1. **Start with business impact**: "Identifying churn early lets us intervene while there's still a chance to save the customer"

2. **Explain the scoring logic**: "We use additive scoring where dormancy is weighted highest because it's the strongest signal"

3. **Discuss prioritization**: "Not all churners are equal — we combine risk score with CLV to prioritize high-value at-risk customers"

4. **Mention the reference date**: "For historical data, we use MAX(order_date) as the reference to avoid everyone looking churned"

5. **Connect to retention economics**: "It's 5-7x cheaper to retain than acquire, so preventing churn directly impacts profitability"

---

## Practice Questions

1. Why do we use `MAX(order_date)` instead of `CURRENT_DATE` for historical data?

2. A customer has 5 orders but hasn't purchased in 100 days. What's their churn status and approximate risk score?

3. How would you modify this model for a subscription business?

4. Why is "single purchaser" weighted at 25 points?

5. How would you measure the ROI of a win-back campaign using this model?

6. A PM asks "which customers should we email this week?" — how would you use this model to answer?

---

## Related Patterns

| Pattern | Relationship to Churn |
|---------|----------------------|
| **RFM Analysis** | Recency dimension directly relates to churn |
| **Cohort Analysis** | Cohort retention reveals systemic churn patterns |
| **CLV** | Combine with churn risk to prioritize interventions |
| **Time Intelligence** | Track churn trends over time |
