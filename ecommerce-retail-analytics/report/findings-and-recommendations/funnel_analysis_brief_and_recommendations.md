# Funnel Analysis — Brief & Recommendations

**Prepared:** July 2026  
**Data range:** Full order history through June 2026  
**Total orders analysed:** 994,690  
**Source:** Ecommerce Analytics — Funnel Analysis page, FCT_ORDERS, FCT_ORDER_PAYMENTS

---

## Executive Summary

The post-purchase operational funnel performs well on volume but has a critical quality problem: **only 59.8% of delivered orders arrive on time**, meaning 4 in 10 customers receive their order after the promised date. With 994,690 total orders and a 97.1% delivery completion rate, the issue is not getting orders to customers — it is getting them there *when promised*.

The average order takes **14.7 days** from placement to delivery, with carrier transit accounting for 77% of that time (11.3 days). This is a logistics and carrier-SLA problem, not a warehouse problem.

Payment behaviour signals financial reliance on credit: 73.5% of revenue is collected via credit card at an average of **3.0 installments** per order, indicating customers are routinely financing purchases. Combined with a freight share of 12.7% of revenue, the true cost-to-serve is higher than payment totals suggest.

---

## Funnel Overview — Order Lifecycle

| Stage | Orders | Share of Total |
|---|---|---|
| Orders Placed | 994,690 | 100.0% |
| Orders Delivered | 965,551 | **97.1%** |
| Delivered On Time | 577,445 | **58.0%** |
| ↳ Delivered Late | 388,106 | 40.2% |
| Canceled | 9,352 | 0.9% |
| In Pipeline (Processing/Invoiced/Approved) | 5,095 | 0.5% |
| Unavailable | 4,633 | 0.5% |

> **Note:** This funnel begins at order placement. Cart, browse, and checkout-to-order conversion data is not available in this dataset. What is measured here is the **post-purchase operational funnel** — from order confirmed to customer satisfaction.

---

## Delivery Time Decomposition

| Stage | Avg Days | Share of Total |
|---|---|---|
| Order → Approval (admin wait) | 0.5 days | 3% |
| Approval → Carrier Pickup (warehouse prep) | 3.0 days | 20% |
| Carrier Pickup → Delivery (transit) | **11.3 days** | **77%** |
| **Total: Order → Delivery** | **14.7 days** | 100% |

Transit time dominates at 77% of total delivery time. The warehouse hands off quickly; the bottleneck is in last-mile and inter-city carrier performance.

---

## Finding 1 — The on-time delivery rate is the biggest operational failure

**59.8% on-time delivery rate** means 388,106 customers received their order after the date they were promised. This is not a marginal performance gap — it is a structural reliability problem.

The average late delivery provides no data on *how late* deliveries arrive (this would require delivery-date vs estimated-date delta analysis), but the volume alone — 40.2% of all delivered orders — signals that estimated delivery dates are systematically optimistic relative to actual carrier performance.

**Impact on customer trust:** Over-promising and under-delivering on the single most visible post-purchase experience (when the order arrives) is a leading driver of 1-star reviews and reduced repeat purchase intent, even when the product itself is satisfactory.

---

## Finding 2 — Carrier transit time is the constraint, not the warehouse

The delivery time breakdown reveals:

- **Approval wait (0.5 days):** Negligible — order processing is fast
- **Warehouse prep (3.0 days):** Reasonable for an e-commerce operation
- **Carrier transit (11.3 days):** This is where 77% of the delivery timeline is consumed

A 3-day warehouse prep is not world-class but is operationally acceptable. An 11.3-day average transit is not. For context, same-day or next-day delivery is standard in major markets. Even 5–7 days would be a significant improvement.

**Implication:** Renegotiating carrier SLAs, adding regional distribution centres, or partnering with faster last-mile providers will have a far greater impact on the on-time rate than any internal warehouse optimisation.

---

## Finding 3 — 1-star reviews are disproportionately high

| Star Rating | Orders | Share of Reviewed |
|---|---|---|
| ⭐⭐⭐⭐⭐ (5 stars) | 552,483 | 57.2% |
| ⭐⭐⭐⭐ (4 stars) | 183,801 | 19.0% |
| ⭐⭐⭐ (3 stars) | 76,982 | 8.0% |
| ⭐⭐ (2 stars) | 37,913 | 3.9% |
| ⭐ (1 star) | 115,336 | **11.9%** |

The review distribution is **bimodal** — the two largest groups are 5-star (57.2%) and 1-star (11.9%). This is a strong indicator that the experience is either excellent or operationally failed, with very little middle ground.

- **High Rating Rate (4–5 stars):** 76.2%
- **Low Rating Rate (1–2 stars):** 15.9%

1-star reviews at 11.9% are structurally elevated — not a long tail. Given the 40.2% late delivery rate, it is reasonable to hypothesise that a significant share of 1-star reviews reflect delivery failure rather than product quality issues.

**Average review score: 4.06 / 5** — the aggregate looks healthy, but it masks the bimodal distribution. The average is pulled up by the majority of satisfied customers and does not surface the 15.9% who had a bad experience.

---

## Finding 4 — Credit card installment dependency is a financial risk signal

| Payment Type | Transactions | Revenue | Avg Installments |
|---|---|---|---|
| Credit Card | 729,652 (73.5%) | $225.9M (74.2%) | **3.0** |
| Boleto | 186,572 (18.8%) | $58.0M (19.1%) | 1.0 |
| Voucher | 49,504 (5.0%) | $14.7M (4.8%) | 1.0 |
| Debit Card | 19,343 (2.0%) | $6.0M (2.0%) | 1.0 |

73.5% of revenue flows through credit card with an average of 3 installments per order. This means:

1. **Cash flow is deferred:** Revenue recognized today may not be collected for 2–3 months
2. **Demand is partially credit-dependent:** If consumer credit tightens, order volume and AOV may fall disproportionately
3. **Average Order Value of $310.85** is high enough that customers routinely need installments to afford it

Boleto (18.8%) is a pay-later method (billet banking), further confirming that a significant share of customers need deferred payment options. Together, credit card installments + boleto = 92.3% of transactions where customers are not paying in full upfront.

---

## Finding 5 — Freight is a meaningful cost at 12.7% of revenue

Total freight charged represents **12.7% of total revenue**. At an AOV of $310.85, the average freight charge per order is approximately $39.

This is a double-edged finding:
- **For the business:** Freight revenue partially offsets logistics costs, but if freight is a barrier to purchase (particularly for lower-value orders), it suppresses conversion
- **For customers:** High freight-to-product-value ratios on smaller orders make the marketplace uncompetitive with alternatives that offer free or low-cost shipping

If freight is passed fully to customers, the effective price for many orders is substantially higher than the product list price. This may contribute to the low repeat-purchase rate identified in the Churn Analysis (see [Churn Analysis Brief](churn_analysis_brief_and_recommendations.md)).

---

## Recommendations

### 1 — Audit and renegotiate carrier SLAs *(Highest priority)*

The 11.3-day average transit time and 40.2% late delivery rate both point to the same cause: carrier performance is not matching the estimated delivery dates being quoted to customers. This requires:

- **Root-cause audit:** Which carriers, routes, or regions are driving late deliveries? (Requires carrier-level data not available in this dataset but should be accessible in the operational system)
- **SLA renegotiation:** Carriers whose performance consistently fails to meet estimated delivery dates should face penalty clauses or be replaced
- **Regional fulfillment:** For the highest-volume geographies, a closer distribution point reduces transit time structurally

- **Target KPI:** Improve on-time delivery rate from 59.8% to 75%+ within 12 months

---

### 2 — Recalibrate estimated delivery dates to be realistic *(Quick win)*

If renegotiating carrier SLAs takes time, a faster fix is to **stop over-promising**. If average transit is 11.3 days and 40.2% of orders arrive late, the estimated delivery dates being shown to customers at checkout are too optimistic.

Displaying an estimated delivery window that is 2–3 days longer than current performance — and then consistently beating it — turns a 40% late delivery rate into a positive surprise. Under-promise and over-deliver is far better for review scores and repeat purchase than the current dynamic.

- **Target KPI:** Reduce 1-star review rate from 11.9% to under 8% within 6 months by eliminating expectation mismatches

---

### 3 — Investigate the 1-star / late delivery correlation *(Data validation)*

The hypothesis — that 1-star reviews are primarily caused by late delivery, not product quality — should be validated with a cross-analysis of review score by IS_ON_TIME_DELIVERY flag. If confirmed:

- It further strengthens the case for carrier SLA investment
- It means product teams are receiving unfair feedback from operationally failed deliveries
- It means the 15.9% low-rating rate overstates product dissatisfaction

This analysis is achievable within the existing data model (FCT_ORDERS has both REVIEW_SCORE and IS_ON_TIME_DELIVERY).

---

### 4 — Introduce free shipping thresholds to reduce freight-as-barrier

At 12.7% of revenue, freight charges are visible to customers. For customers on the margin of a repeat purchase, a $39 freight charge on a $200 product may be the deciding factor against buying.

A **free shipping threshold** (e.g., orders above $X qualify for free shipping) has two effects:
- Reduces the perceived barrier for incremental purchases
- Increases AOV as customers add items to reach the threshold

The threshold level should be set above current AOV ($310.85) to avoid margin erosion while still creating a reachable incentive. This recommendation directly supports the post-first-purchase nurture sequence recommended in the Churn Analysis.

---

### 5 — Monitor the installment dependency as a demand health indicator

The 3.0-average credit card installments signals that demand is partially credit-funded. Track this metric monthly:

- **Rising installments** → customers are stretching further to afford purchases; demand may be fragile
- **Shift from credit card to boleto** → customers may be losing access to credit
- **Falling AOV** → customers buying smaller items to reduce the installment burden

This metric is a leading indicator of demand softness before it shows up in order volume.

---

### 6 — Establish a warehouse prep SLA of 2 days

Current average prep time is 3.0 days (approval to carrier handoff). Best-in-class e-commerce operations target same-day or next-day handoff. Reducing prep time from 3.0 to 2.0 days:

- Reduces total delivery time by ~1 day on average
- Marginally improves on-time delivery (less time consumed before carrier picks up)
- Does not address the 11.3-day transit bottleneck, but is an achievable internal improvement

- **Target KPI:** Reduce average prep days from 3.0 to 2.0 within 6 months

---

## Priority Matrix

| Action | Urgency | Potential Impact | Effort |
|---|---|---|---|
| Carrier SLA audit & renegotiation | Immediate | Very High — addresses 40.2% late delivery rate | High |
| Recalibrate estimated delivery dates | This week | High — immediate impact on 1-star reviews | Low |
| Free shipping threshold | This quarter | Medium — supports repeat purchase and AOV | Medium |
| Validate late delivery → 1-star link | This quarter | Medium — validates root cause, guides investment | Low |
| Warehouse prep SLA (2-day target) | This quarter | Low-Medium — marginal delivery time improvement | Medium |
| Monthly installment dependency monitoring | Ongoing | Preventive — early warning on demand health | Low |

---

## Connection to Churn Analysis

The findings here directly reinforce the [Churn Analysis Brief](churn_analysis_brief_and_recommendations.md):

- The **40.2% late delivery rate** affects new customers at their most impressionable moment. A customer whose first order arrives late is more likely to become a "One-and-Done Lost" customer
- The **freight cost barrier** likely suppresses the repeat purchases needed to convert one-time buyers into the habitual purchasers that drive CLV
- The **bimodal review distribution** (57% five-star, 12% one-star) aligns with the churn data showing customers either become loyal or disappear — there is very little middle ground

Improving on-time delivery and reducing freight friction are **complementary levers** to the churn retention programme. Neither works alone; both are needed.

---

*Analysis performed using Power BI MCP against the FCT_ORDERS and FCT_ORDER_PAYMENTS tables. Delivery timing computed from DELIVERY_DAYS, FULFILLMENT_DAYS, and SHIPPING_TRANSIT_DAYS columns. Payment mix from FCT_ORDER_PAYMENTS[PAYMENT_TYPE] and PAYMENT_VALUE.*
