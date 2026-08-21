# Business Analytics Impact Summary

## E-Commerce Retail Analytics Platform

**Dataset:** Brazilian E-Commerce | 100,000+ Orders | 96,000+ Customers

---

## Executive Overview

This analytics platform answers the questions that drive business growth:

| Business Question | Pattern | Key Finding |
|-------------------|---------|-------------|
| Who are our best customers? | RFM Analysis | 12% are Champions worth 2x average |
| Are customers coming back? | Cohort Analysis | 99% don't return after first purchase |
| What's each customer worth? | Lifetime Value | Platinum tier = $637 per customer |
| Who's about to leave? | Churn Risk | 46% at critical risk level |
| Which products matter most? | Pareto (80/20) | 28% of products drive 80% of revenue |
| How are we trending? | Time Intelligence | Revenue up 300% week-over-week |
| Where do orders fail? | Funnel Analysis | 97% delivery success rate |
| What sells together? | Market Basket | Computer accessories: 67% cross-buy rate |

---

# 1. RFM Analysis
### Understanding Customer Value

**Question:** *"Who are our most valuable customers, and how should we treat each segment?"*

RFM scores customers on three dimensions:
- **Recency** - When did they last buy?
- **Frequency** - How often do they buy?
- **Monetary** - How much do they spend?

### Results

| Segment | Customers | Avg Spend | Recommended Action |
|---------|-----------|-----------|-------------------|
| Champions | 11,607 | $308 | VIP treatment, early access |
| Can't Lose Them | 782 | $365 | Urgent win-back campaign |
| Potential Loyalists | 10,211 | $169 | Nurture with rewards program |
| At Risk | 3,127 | $172 | Re-engagement emails |
| Hibernating | 28,263 | $164 | Low-cost reactivation |

### Business Impact
- **Champions** (12% of customers) generate disproportionate value - protect them
- **Can't Lose Them** have the highest spend but are slipping away - act now
- **Hibernating** is the largest segment - small improvements yield big returns

---

# 2. Cohort Analysis
### Customer Retention Over Time

**Question:** *"Do customers acquired in different periods behave differently over time?"*

Cohort analysis groups customers by their first purchase month, then tracks what percentage return in subsequent months.

### Results

| Cohort | Size | Month 1 | Month 2 | Month 3 | Month 4 |
|--------|------|---------|---------|---------|---------|
| Jan 2017 | 754 | 0.4% | 0.3% | 0.1% | 0.4% |
| Feb 2017 | 1,705 | 0.2% | 0.3% | 0.1% | 0.2% |
| Mar 2017 | 2,521 | 0.3% | 0.2% | 0.2% | 0.1% |

### Business Impact
- **Critical Finding:** Less than 1% of customers make a second purchase
- **Opportunity:** Even a 1% retention improvement doubles repeat customers
- **Action:** Implement post-purchase engagement within first 30 days

---

# 3. Customer Lifetime Value
### Predicting Customer Worth

**Question:** *"How much revenue can we expect from each customer over their lifetime?"*

CLV combines historical spending with cohort-based predictions to estimate total customer value.

### Results

| Tier | Customers | Historical Spend | Predicted Value | Growth Potential |
|------|-----------|------------------|-----------------|------------------|
| Platinum | 9,542 | $637 | $637 | Maintain |
| Gold | 19,084 | $202 | $221 | +9% |
| Silver | 28,626 | $93 | $172 | +85% |
| Bronze | 38,168 | $85 | $161 | +89% |

### Business Impact
- **Platinum customers** (10%) are worth 4x more than Bronze - prioritize retention
- **Silver & Bronze** have 85%+ growth potential - invest in nurturing
- **Acquisition Budget:** Spend up to predicted CLV to acquire new customers profitably

---

# 4. Churn Risk Indicators
### Identifying At-Risk Customers

**Question:** *"Which customers are about to stop buying, and can we save them?"*

Churn risk scoring combines multiple warning signals into a single 0-100 score.

### Results

| Risk Level | Customers | % of Total | Avg Days Inactive | Risk Score |
|------------|-----------|------------|-------------------|------------|
| Critical | 43,586 | 46% | 284 days | 83 |
| High | 41,775 | 44% | 243 days | 64 |
| Medium | 9,699 | 10% | 74 days | 36 |
| Low | 360 | <1% | 32 days | 9 |

### Business Impact
- **46% at Critical Risk** - nearly half the customer base needs intervention
- **Medium Risk** (10%) is the sweet spot for intervention - not too late to save
- **Low Risk** customers are rare gems - study what makes them different

---

# 5. Pareto Analysis (80/20 Rule)
### Finding the Products That Matter

**Question:** *"Which products drive the majority of our revenue?"*

The Pareto principle states that roughly 80% of results come from 20% of causes.

### Results

| Segment | Products | % of Catalog | Revenue | % of Revenue |
|---------|----------|--------------|---------|--------------|
| A (Top) | 9,252 | 28% | $12.7M | 80% |
| B (Middle) | 11,759 | 36% | $2.4M | 15% |
| C (Bottom) | 11,940 | 36% | $0.8M | 5% |

### Business Impact
- **28% of products generate 80% of revenue** - focus inventory management here
- **A-segment products** should never stock out
- **C-segment products** (36% of catalog, 5% of revenue) - consider discontinuing

---

# 6. Time Intelligence
### Tracking Performance Over Time

**Question:** *"How are we performing compared to last week, month, and year?"*

Time intelligence adds context to daily numbers by comparing to prior periods and smoothing noise with moving averages.

### Results (January 2018)

| Date | Orders | Revenue | vs Last Week | 7-Day Trend |
|------|--------|---------|--------------|-------------|
| Jan 1 | 73 | $8,392 | -19% | $14,001 |
| Jan 2 | 203 | $29,411 | +21% | $14,682 |
| Jan 4 | 255 | $39,916 | +75% | $19,537 |
| Jan 8 | 292 | $45,169 | +300% | $30,788 |

### Business Impact
- **7-day moving average** reveals true trend beneath daily volatility
- **Week-over-week comparison** shows Jan 8 had 300% growth vs prior week
- **Anomaly detection:** When daily revenue exceeds 150% of 7-day average, investigate

---

# 7. Funnel Analysis
### Order Fulfillment Performance

**Question:** *"Where are we losing orders in the fulfillment process?"*

Funnel analysis tracks conversion rates through each stage of order processing.

### Results

| Stage | Orders | Conversion | Avg Time |
|-------|--------|------------|----------|
| Placed | 3,969 | 100% | - |
| Approved | 3,930 | 99% | 0.5 days |
| Shipped | 3,890 | 98% | 3.2 days |
| Delivered | 3,872 | 97.6% | 12.2 days total |
| Reviewed | ~1,750 | 45% | varies |

### Business Impact
- **97.6% delivery rate** indicates strong operational performance
- **12.2-day delivery time** sets customer expectations
- **45% review rate** - opportunity to increase customer feedback

---

# 8. Market Basket Analysis
### Products Bought Together

**Question:** *"What products are frequently purchased together?"*

Market basket analysis identifies product pairs that appear in the same order more often than chance would predict.

### Results

| Category A | Category B | Co-Purchases | Confidence | Lift |
|------------|------------|--------------|------------|------|
| Computer Accessories | Computer Accessories | 6 | 67% | 7,309x |
| Bed & Bath | Bed & Bath | 6 | 40% | 3,289x |
| Auto Parts | Auto Parts | 17 | 19% | 337x |
| Garden Tools | Garden Tools | 11 | 15% | 10x |

**Key Metrics:**
- **Confidence 67%** = When customers buy Product A, 67% also buy Product B
- **Lift 7,309x** = This pair is bought together 7,309x more than random chance

### Business Impact
- **Bundle opportunities:** Create packages from high-lift product pairs
- **"Customers also bought"** recommendations drive incremental revenue
- **Same-category items** have highest affinity - upsell within categories

---

# Key Insights Summary

| Insight | Metric | Action |
|---------|--------|--------|
| Champions are 2x more valuable | $308 vs $164 avg | Protect with VIP program |
| 99% don't return | <1% Month 1 retention | Post-purchase engagement |
| Half are at risk | 46% Critical churn | Intervention campaign |
| 28% drives 80% | Pareto distribution | Inventory prioritization |
| 97% orders delivered | Funnel success | Maintain operations |
| Computer accessories bundle | 67% confidence | Cross-sell opportunity |

---

*E-Commerce Retail Analytics Platform*
