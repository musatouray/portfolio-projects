# Customer Lifetime Value — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Customer Lifetime Value (CLV) |
| **Page Number** | 3 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with value-tier accents |

---

## Objective

**What decision does this page help make?**

This page answers: *"Which customers are most valuable, and where should we invest to maximize long-term revenue?"*

CLV analysis helps:
1. Identify highest-value customers for premium treatment
2. Compare historical vs. predicted lifetime value
3. Understand value distribution across cohorts
4. Guide customer acquisition cost (CAC) decisions

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **CFO / Finance** | ROI analysis, forecasting | 5-10 minutes |
| **Marketing Director** | CAC/LTV ratio decisions | 3-5 minutes |
| **Customer Success** | Account prioritization | 2-3 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | What is our total customer lifetime value? | Business valuation |
| 2 | How is CLV distributed across customers? | Concentration risk |
| 3 | What is average CLV by cohort? | Acquisition quality |
| 4 | How does historical CLV compare to predicted? | Forecast accuracy |
| 5 | Which CLV segments drive most value? | Resource allocation |
| 6 | Who are our highest-value customers? | VIP identification |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Customer Lifetime Value Analysis"               [CLV Segment Slicer] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  TOTAL CLV  │  │   AVG CLV   │  │ PREDICTED   │  │  TOP 10%    │            │
│  │   R$ 15.4M  │  │   R$ 165    │  │  R$ 18.2M   │  │  R$ 8.5M    │            │
│  │  historical │  │ per customer│  │   +18%      │  │   55% rev   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │     CLV DISTRIBUTION (HISTOGRAM)        │  │   CLV BY COHORT (LINE)      │  │
│  │                                         │  │                             │  │
│  │     ▓▓                                  │  │      ___                    │  │
│  │    ▓▓▓▓                                 │  │     /   \___                │  │
│  │   ▓▓▓▓▓▓                                │  │    /        \___           │  │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓                          │  │   /             \          │  │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░                  │  │  2016  2017  2018          │  │
│  │  $0   $200  $500  $1000+                │  │                             │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌───────────────────────────┐  ┌───────────────────────────────────────────┐  │
│  │   CLV SEGMENT BREAKDOWN   │  │   HISTORICAL vs PREDICTED (SCATTER)       │  │
│  │      (Donut Chart)        │  │                                           │  │
│  │                           │  │   Y: Predicted LTV                        │  │
│  │  High Value: 15%          │  │   X: Historical CLV                       │  │
│  │  Medium: 35%              │  │   Color: CLV Segment                      │  │
│  │  Low: 40%                 │  │   [45° line = perfect prediction]         │  │
│  │  At Risk: 10%             │  │                                           │  │
│  └───────────────────────────┘  └───────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  TOP CUSTOMERS BY CLV (TABLE)                                            │   │
│  │  Rank | Customer ID | Historical CLV | Predicted LTV | Segment | Orders  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Calculation |
|--------|--------------|--------|-------------|
| Total CLV | `Total Historical CLV` | FCT_CLV_CUSTOMER | `SUM(HISTORICAL_CLV)` |
| Avg CLV | `Avg CLV per Customer` | FCT_CLV_CUSTOMER | `AVERAGE(HISTORICAL_CLV)` |
| Predicted LTV | `Total Predicted LTV` | FCT_CLV_CUSTOMER | `SUM(PREDICTED_LTV)` |
| Top 10% Value | `Top Decile CLV` | FCT_CLV_CUSTOMER | `CALCULATE(SUM(...), CLV_DECILE = 10)` |

### CLV Distribution (Histogram)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Histogram or Grouped Bar |
| **X-Axis** | CLV Buckets (binned HISTORICAL_CLV) |
| **Y-Axis** | Customer Count |
| **Bins** | R$0-50, R$50-100, R$100-200, R$200-500, R$500+ |

### CLV by Cohort (Line Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Line Chart |
| **X-Axis** | DIM_COHORTS[COHORT_MONTH] |
| **Y-Axis** | `AVERAGE(HISTORICAL_CLV)` |
| **Legend** | None (single line) or by year |

### CLV Segment Breakdown (Donut)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Donut Chart |
| **Legend** | FCT_CLV_CUSTOMER[CLV_SEGMENT] |
| **Values** | Customer count per segment |

### Historical vs Predicted (Scatter)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Scatter Chart |
| **X-Axis** | HISTORICAL_CLV |
| **Y-Axis** | PREDICTED_LTV |
| **Color** | CLV_SEGMENT |
| **Reference Line** | 45° diagonal (y = x) |

### Top Customers Table

| Column | Source |
|--------|--------|
| Rank | ROW_NUMBER by HISTORICAL_CLV |
| Customer ID | CUSTOMER_UNIQUE_ID |
| Historical CLV | HISTORICAL_CLV |
| Predicted LTV | PREDICTED_LTV |
| CLV Segment | CLV_SEGMENT |
| Total Orders | TOTAL_ORDERS |
| Avg Order Value | AVERAGE_ORDER_VALUE |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| CLV Segment | Slicer (multi-select) | All | All visuals |
| Cohort | Slicer (optional) | All | CLV by Cohort chart |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click CLV segment | Filter all visuals to that segment |
| Click cohort point | Show cohort detail |
| Click customer in table | Drill-through to customer 360 (if available) |
| Hover on scatter point | Show customer CLV details |

---

## Design Specifications

### CLV Segment Colors

| Segment | Hex | Description |
|---------|-----|-------------|
| High Value | `#1E3A5F` | Top CLV tier |
| Medium Value | `#00897B` | Middle tier |
| Low Value | `#90A4AE` | Lower tier |
| At Risk | `#D84315` | Declining CLV |

---

## DAX Measures Required

```
Folder: _Base
├── Total Historical CLV
├── Total Predicted LTV
├── Avg CLV per Customer
├── Total Customers (CLV)

Folder: _Analytical
├── Top Decile CLV
├── Top Decile % of Total
├── CLV by Cohort
├── Prediction Accuracy %

Folder: _Segments
├── High Value Count
├── Medium Value Count
├── Low Value Count
├── High Value Revenue %

Folder: _Time Intelligence
├── CLV Growth MoM
├── Predicted vs Historical Variance
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Value concentration visible** | Clear that top 10-20% drive majority of value |
| **Cohort trends clear** | Can identify if newer cohorts are more/less valuable |
| **Prediction insight** | Understand relationship between historical and predicted |
| **Actionable segments** | Each CLV segment has investment implication |

---

## Implementation Checklist

- [ ] Create CLV bin buckets for histogram
- [ ] Build scatter plot with 45° reference line
- [ ] Configure cohort line chart with proper date axis
- [ ] Add Top N filter to customer table
- [ ] Create segment-specific measures
- [ ] Test cross-filtering between visuals
