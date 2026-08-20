# Churn Risk — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Churn Risk Analysis |
| **Page Number** | 5 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Warning orange/red for risk emphasis |

---

## Objective

**What decision does this page help make?**

This page answers: *"Which customers are at risk of leaving, and what can we do to retain them?"*

Churn analysis enables:
1. Proactive identification of at-risk customers
2. Understanding churn risk factors
3. Prioritizing retention outreach
4. Measuring revenue at risk

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **Customer Success** | Daily outreach prioritization | 5-10 minutes |
| **Retention Team** | Campaign targeting | 3-5 minutes |
| **VP of Customer** | Risk assessment, resource allocation | 2-3 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | How many customers are at risk of churning? | Scale of problem |
| 2 | What revenue is at risk? | Financial impact |
| 3 | What are the churn status distributions? | Intervention timing |
| 4 | What signals indicate churn risk? | Early warning system |
| 5 | Which high-value customers are at risk? | Priority outreach |
| 6 | What is the single-purchaser rate? | Repeat purchase challenge |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Churn Risk Analysis"                           [Risk Segment Slicer] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  AT RISK    │  │  REVENUE    │  │  CHURNED    │  │  SINGLE     │            │
│  │  CUSTOMERS  │  │  AT RISK    │  │  CUSTOMERS  │  │  PURCHASERS │            │
│  │    8.2K     │  │   R$ 1.2M   │  │   45.3K     │  │    78%      │            │
│  │   ▲ +5%     │  │   ▼ -3%    │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │    CHURN STATUS DISTRIBUTION (FUNNEL)   │  │   RISK SCORE DISTRIBUTION   │  │
│  │                                         │  │        (HISTOGRAM)          │  │
│  │    Active     ████████████████  35K     │  │                             │  │
│  │    Cooling    ████████        12K       │  │    ▓▓▓▓                     │  │
│  │    At Risk    ██████          8K        │  │   ▓▓▓▓▓▓                    │  │
│  │    Churned    ████████████████████ 45K  │  │  ▓▓▓▓▓▓▓▓▓▓▓▓              │  │
│  │                                         │  │  Low    Med    High         │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   DAYS SINCE LAST ORDER (HISTOGRAM)     │  │   NPS SEGMENT BY STATUS     │  │
│  │                                         │  │      (STACKED BAR)          │  │
│  │       ▓▓▓▓▓▓                            │  │                             │  │
│  │      ▓▓▓▓▓▓▓▓▓▓                         │  │  Active   ████ ██ █         │  │
│  │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                    │  │  Cooling  ███ ███ ██        │  │
│  │    0-30  30-60  60-90  90+              │  │  At Risk  ██ ███ ████       │  │
│  │                                         │  │  [Promoter|Neutral|Detract] │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  HIGH-VALUE AT-RISK CUSTOMERS (PRIORITY LIST)                            │   │
│  │  Customer | Revenue | Days Inactive | Orders | Rating | Risk Score       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Calculation |
|--------|--------------|--------|-------------|
| At Risk Customers | `At Risk Count` | FCT_CHURN_RISK | `CALCULATE(COUNT(...), CHURN_STATUS = "At Risk")` |
| Revenue at Risk | `Revenue at Risk` | FCT_CHURN_RISK | `CALCULATE(SUM(TOTAL_REVENUE), CHURN_STATUS = "At Risk")` |
| Churned Customers | `Churned Count` | FCT_CHURN_RISK | `CALCULATE(COUNT(...), CHURN_STATUS = "Churned")` |
| Single Purchasers | `Single Purchaser %` | FCT_CHURN_RISK | `DIVIDE(COUNT where IS_SINGLE_PURCHASER = TRUE, COUNT ALL)` |

### Churn Status Distribution (Funnel/Bar)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Funnel or Horizontal Bar |
| **Y-Axis** | CHURN_STATUS |
| **X-Axis** | Customer Count |
| **Sort** | Active → Cooling → At Risk → Churned |
| **Colors** | Green (Active) → Orange (Cooling) → Red (At Risk/Churned) |

### Risk Score Distribution (Histogram)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Histogram |
| **X-Axis** | CHURN_RISK_SCORE (binned) |
| **Y-Axis** | Customer Count |
| **Bins** | 0-20 (Low), 20-50 (Medium), 50-80 (High), 80-100 (Critical) |

### Days Since Last Order (Histogram)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Histogram |
| **X-Axis** | DAYS_SINCE_LAST_ORDER (binned) |
| **Y-Axis** | Customer Count |
| **Bins** | 0-30, 30-60, 60-90, 90-180, 180+ |
| **Reference Lines** | At threshold boundaries (30, 60, 90 days) |

### NPS Segment by Status (Stacked Bar)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | 100% Stacked Bar |
| **Y-Axis** | CHURN_STATUS |
| **X-Axis** | Percentage |
| **Legend** | CUSTOMER_NPS_SEGMENT (Promoter, Neutral, Detractor) |

### High-Value At-Risk Table

| Column | Source | Filter |
|--------|--------|--------|
| Customer | CUSTOMER_UNIQUE_ID | CHURN_STATUS = "At Risk" |
| Revenue | TOTAL_REVENUE | Sort descending |
| Days Inactive | DAYS_SINCE_LAST_ORDER | |
| Orders | TOTAL_ORDERS | |
| Rating | AVERAGE_RATING | |
| Risk Score | CHURN_RISK_SCORE | |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| Churn Status | Slicer (multi-select) | All | All visuals |
| Risk Segment | Slicer | All | All visuals |
| Single Purchaser | Toggle | All | Focus on repeaters |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click status in funnel | Filter all visuals to that status |
| Click risk score bin | Show customers in that risk range |
| Click customer in table | Drill-through to customer detail |
| Hover on histogram bar | Show customer count, revenue at stake |

---

## Design Specifications

### Churn Status Colors

| Status | Hex | Description |
|--------|-----|-------------|
| Active | `#2E7D32` | Safe customers |
| Cooling | `#FFA000` | Early warning |
| At Risk | `#FF7043` | Needs attention |
| Churned | `#D84315` | Lost customers |

### Risk Score Colors

| Score Range | Hex | Label |
|-------------|-----|-------|
| 0-20 | `#2E7D32` | Low Risk |
| 20-50 | `#FFC107` | Medium Risk |
| 50-80 | `#FF9800` | High Risk |
| 80-100 | `#D84315` | Critical |

---

## DAX Measures Required

```
Folder: _Base
├── Total Customers (Churn)
├── Total Revenue (Churn)
├── Avg Days Since Last Order

Folder: _Segments
├── Active Count
├── Cooling Count
├── At Risk Count
├── Churned Count
├── Single Purchaser Count
├── Single Purchaser %

Folder: _Analytical
├── Revenue at Risk
├── Revenue at Risk %
├── Avg Risk Score
├── High Risk Count
├── At Risk & High Value Count

Folder: _Data Visualization
├── Status Color
├── Risk Score Color
├── Days Inactive Warning
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Risk visibility** | At-risk customers immediately identifiable |
| **Revenue impact clear** | Financial stakes are quantified |
| **Prioritization enabled** | High-value at-risk list is actionable |
| **Early warning** | Cooling customers visible before they churn |

---

## Implementation Checklist

- [ ] Create churn status funnel/bar chart
- [ ] Build risk score histogram with bins
- [ ] Configure days inactive histogram with thresholds
- [ ] Create NPS by status stacked bar
- [ ] Build priority list with Top N filter
- [ ] Add revenue at risk calculations
- [ ] Configure conditional formatting for risk scores
