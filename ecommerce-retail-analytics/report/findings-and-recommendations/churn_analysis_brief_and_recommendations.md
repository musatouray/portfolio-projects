# Churn Analysis — Brief & Recommendations

**Prepared:** July 2026  
**Snapshot date:** June 2026  
**Customer base:** 35,313  
**Source:** Ecommerce Analytics — Churn Risk page, FCT_RFM_SEGMENTS

---

## Executive Summary

39.4% of the customer base has churned as of June 2026. Only 3 in 10 customers are still actively engaged. The average customer has not purchased in **93 days**, and the average churn risk score across all customers is **30.2 / 100**.

The root cause is not dissatisfaction — average review scores for churned segments are 4.0–4.1 out of 5, nearly identical to active customers. The core structural problem is a **failure to convert first-time buyers into repeat purchasers**: 57.9% of all customers made exactly one purchase and never returned.

---

## Churn Status Overview

| Status | Customers | Share |
|---|---|---|
| Active | 10,694 | 30.3% |
| Cooling | 6,350 | 18.0% |
| At Risk | 4,365 | 12.4% |
| **Churned** | **13,904** | **39.4%** |

---

## Finding 1 — Churn is a one-time buyer problem, not a satisfaction problem

57.9% of customers made exactly one purchase and never returned. Average review scores for churned segments are **4.0–4.1 / 5** — nearly identical to active customers. Customers are leaving happy; they simply have no reason to return.

This rules out product quality or delivery failure as the root cause. The issue is **conversion to repeat purchase**, not customer experience.

---

## Finding 2 — Two RFM segments account for 99% of all churned customers

| Segment | Customers | Status | Avg Recency | Avg Rating |
|---|---|---|---|---|
| High-Value Dormant | 8,567 | 100% Churned | 169 days | 4.0 |
| One-and-Done Lost | 5,212 | 100% Churned | 209 days | 4.0 |

These two segments account for **13,779 of the 13,904 churned customers (99%)**.

- **High-Value Dormant** — made multiple high-spend purchases in the past but have been completely silent for ~169 days. They are winnable: they already demonstrated willingness to spend.
- **One-and-Done Lost** — bought once, rated the experience well (4.0), and disappeared. They are the hardest to reactivate because no repeat-purchase habit was ever formed.

---

## Finding 3 — 3,454 high-value customers are on the edge right now

The **Slipping Whales** segment: 3,361 are currently At Risk (97.3% of the group), with an average recency of 75 days. These are formerly frequent, high-spend customers who are going quiet. Average rating: 4.1.

This is the **highest-ROI retention target**: they spend more, they like the brand, and they have not left yet.

| Segment | Customers | Churned | At Risk | Avg Recency | Avg Rating |
|---|---|---|---|---|---|
| High-Value Dormant | 8,567 | 8,567 | — | 169 days | 4.0 |
| One-and-Done Lost | 5,212 | 5,212 | — | 209 days | 4.0 |
| Slipping Whales | 3,454 | 93 | 3,361 | 75 days | 4.1 |
| Need Attention | 863 | 32 | 831 | 75 days | 4.1 |
| Champions | 14,820 | — | 146 | 24 days | 4.0 |

---

## Finding 4 — Satisfaction does not protect against churn

| NPS Tier | Total | Churned | Churn Rate |
|---|---|---|---|
| Detractor | 2,864 | 1,594 | **55.6%** |
| Promoter | 13,863 | 6,666 | **48.1%** |
| Neutral | 18,470 | 5,556 | **30.1%** |

Detractors churn at the highest rate (55.6%), confirming that poor experience accelerates exit. However, **promoters churn at 48.1%** — almost as high. Delighting customers is necessary but nowhere near sufficient to retain them. The marketplace has a **structural repeat-purchase problem across all satisfaction tiers**.

Neutrals churn at the lowest rate (30.1%), likely reflecting habitual buyers who are neither emotionally invested nor actively dissatisfied.

> **Implication:** Retention budget should go to reactivation and habit-forming programmes, not to service recovery initiatives.

---

## Finding 5 — The Critical and High risk tiers define clear intervention windows

| Risk Tier | Customers | Avg Risk Score | Avg Days Since Purchase |
|---|---|---|---|
| Critical | 2,570 | 83.2 / 100 | 213 days |
| High | 4,953 | 62.2 / 100 | 178 days |
| Medium | 12,392 | 36.6 / 100 | 121 days |
| Low | 15,398 | 5.8 / 100 | 23 days |

Critical-tier customers have been silent for over **7 months** and score 83/100 on the composite risk model. High-tier customers average ~6 months of silence. These boundaries define the time windows for reactivation campaigns before recovery probability drops below economic viability.

---

## Recommendations

### 1 — Launch a Slipping Whales rescue campaign immediately *(Highest priority)*

Target the **3,361 At-Risk Slipping Whales** before they cross into the Churned pool. They have the highest CLV, are still reachable (75-day recency), and have not left yet. A personalised "we miss you" message with a category-specific offer should deploy within two weeks.

- **Trigger:** Customers in the Slipping Whales RFM segment with CHURN_STATUS = 'At Risk'
- **Channel:** Email / push — personalised to last purchased category
- **Target KPI:** Reduce segment's At Risk count by 20% within 60 days

---

### 2 — Build a post-first-purchase nurture sequence *(Structural fix)*

57.9% one-time buyers is the underlying structural problem. Every new customer should enter an automated sequence after their first order:

| Day | Action |
|---|---|
| Day 7 | "You might also like…" — cross-sell from Market Basket data |
| Day 30 | Category spotlight based on first purchase |
| Day 45 | Incentive (free shipping or small discount) |
| Day 60 | Final re-engagement nudge before entering Cooling status |

This addresses the One-and-Done problem **before** the pattern forms.

---

### 3 — Run a High-Value Dormant win-back programme *(High value, long tail)*

8,567 customers spent well, rated the experience 4.0, and went silent. A tiered win-back campaign personalised to their last purchase category:

- **Under 150 days silent:** Standard re-engagement email
- **150–200 days silent:** Add a meaningful incentive
- **Over 200 days silent:** High-value offer or write off (below minimum economic threshold)

Focus budget on the under-200-day cohort first. Beyond 200 days of silence, reactivation probability drops significantly (One-and-Done Lost average recency is 209 days).

---

### 4 — Set a universal 75-day recency trigger for automated retention outreach

Slipping Whales and Need Attention segments both average **75 days recency** at the point of entering At Risk status. This should become the operational standard:

> Any customer with 2+ prior orders who has not purchased in 75 days enters an automated reactivation flow.

This prevents the pipeline from feeding the Churned pool.

---

### 5 — Monitor the Cooling segment monthly *(Preventive)*

6,350 customers are Cooling — between Active and At Risk. A lightweight nudge at **45-day recency** (before they hit the 75-day At Risk threshold) can slow the rate of deterioration. Monitor the size of this segment month-over-month as a leading indicator of future churn pressure.

---

### 6 — Do not invest in satisfaction-improvement programmes as a churn fix

Review scores of 4.0–4.1 across churned segments confirm satisfaction is not the driver. Directing retention budget toward NPS improvement, service recovery, or review-boosting programmes will not reduce churn. The problem is behavioural, not experiential.

---

## Priority Matrix

| Action | Urgency | Potential Impact | Effort |
|---|---|---|---|
| Slipping Whales rescue campaign | Immediate | High — 3,361 at-risk high-value customers | Low |
| 75-day recency trigger automation | This quarter | High — prevents future churn structurally | Medium |
| Post-first-purchase nurture sequence | This quarter | Very high — addresses 57.9% one-time buyer rate | Medium |
| High-Value Dormant win-back | Next quarter | Medium — 8,567 customers, lower conversion rate | Medium |
| Cooling segment monthly monitoring | Ongoing | Preventive | Low |

---

*Analysis performed using Power BI MCP against the FCT_RFM_SEGMENTS and FCT_CLV_CUSTOMER tables. Churn status classifications are recency-based: Active < 45 days, Cooling 45–90 days, At Risk 90–180 days, Churned > 180 days.*
