# Cohort Retention — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Cohort Retention Analysis |
| **Page Number** | 4 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with retention gradient |

---

## Objective

**What decision does this page help make?**

This page answers: *"Are we retaining customers over time, and how do different acquisition cohorts compare?"*

Cohort analysis reveals:
1. Whether customer retention is improving or declining
2. Which acquisition periods produced the best customers
3. At what point customers typically drop off
4. The effectiveness of retention initiatives over time

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **VP of Marketing** | Acquisition quality assessment | 5-10 minutes |
| **Growth Team** | Retention strategy planning | 5-10 minutes |
| **Product Manager** | Feature impact on retention | 3-5 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | What is our overall retention rate? | Business health indicator |
| 2 | How does retention vary by cohort? | Acquisition quality |
| 3 | At which period do we lose most customers? | Intervention timing |
| 4 | Are newer cohorts retaining better? | Trend direction |
| 5 | What is the retention curve shape? | Expected customer lifetime |
| 6 | Which cohorts are largest? | Volume context |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Cohort Retention Analysis"                      [Period Selector]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ TOTAL       │  │  PERIOD 1   │  │  PERIOD 3   │  │  PERIOD 6   │            │
│  │ COHORTS     │  │  RETENTION  │  │  RETENTION  │  │  RETENTION  │            │
│  │    24       │  │    45%      │  │    28%      │  │    18%      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    RETENTION HEATMAP (COHORT MATRIX)                     │   │
│  │                                                                          │   │
│  │  Cohort    │ P0   │ P1   │ P2   │ P3   │ P4   │ P5   │ P6   │ ...       │   │
│  │  ─────────────────────────────────────────────────────────────           │   │
│  │  Jan 2017  │ 100% │ 42%  │ 31%  │ 25%  │ 21%  │ 18%  │ 15%  │           │   │
│  │  Feb 2017  │ 100% │ 45%  │ 33%  │ 27%  │ 22%  │ 19%  │ 16%  │           │   │
│  │  Mar 2017  │ 100% │ 48%  │ 35%  │ 28%  │ 23%  │ 20%  │      │           │   │
│  │  ...       │      │      │      │      │      │      │      │           │   │
│  │                                                                          │   │
│  │  Color: Dark (high retention) → Light (low retention)                    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   RETENTION CURVES (LINE CHART)         │  │   COHORT SIZE (BAR CHART)   │  │
│  │                                         │  │                             │  │
│  │   100%  ─┐                              │  │  Jan 2017 ████████          │  │
│  │          └──┐                           │  │  Feb 2017 ██████████        │  │
│  │     50%     └───┐                       │  │  Mar 2017 ████████████      │  │
│  │                 └────────               │  │  Apr 2017 ██████████████    │  │
│  │      0%                                 │  │  ...                        │  │
│  │         P0  P1  P2  P3  P4  P5  P6      │  │                             │  │
│  │   [Multiple lines for selected cohorts] │  │                             │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  COHORT DETAIL TABLE                                                     │   │
│  │  Cohort | Size | P1 Ret | P3 Ret | P6 Ret | Total Revenue | Avg Revenue  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Calculation |
|--------|--------------|--------|-------------|
| Total Cohorts | `Cohort Count` | DIM_COHORTS | `COUNTROWS(DIM_COHORTS)` |
| Period 1 Retention | `P1 Retention Rate` | FCT_COHORT_RETENTION | `AVG(RETENTION_RATE) where PERIOD_NUMBER = 1` |
| Period 3 Retention | `P3 Retention Rate` | FCT_COHORT_RETENTION | `AVG(RETENTION_RATE) where PERIOD_NUMBER = 3` |
| Period 6 Retention | `P6 Retention Rate` | FCT_COHORT_RETENTION | `AVG(RETENTION_RATE) where PERIOD_NUMBER = 6` |

### Retention Heatmap (Matrix)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Matrix |
| **Rows** | DIM_COHORTS[COHORT_MONTH_NAME] |
| **Columns** | FCT_COHORT_RETENTION[PERIOD_NUMBER] |
| **Values** | RETENTION_RATE (formatted as %) |
| **Conditional Formatting** | Color scale: Green (high) → Red (low) |

### Retention Curves (Line Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Line Chart |
| **X-Axis** | PERIOD_NUMBER |
| **Y-Axis** | RETENTION_RATE |
| **Legend** | COHORT_MONTH (selected cohorts) |
| **Small Multiples** | Optional for comparing cohorts |

### Cohort Size (Bar Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | COHORT_MONTH_NAME |
| **X-Axis** | COHORT_SIZE |
| **Sort** | Chronological |

### Cohort Detail Table

| Column | Source |
|--------|--------|
| Cohort | COHORT_MONTH_NAME |
| Size | COHORT_SIZE |
| P1 Retention | RETENTION_RATE where PERIOD_NUMBER = 1 |
| P3 Retention | RETENTION_RATE where PERIOD_NUMBER = 3 |
| P6 Retention | RETENTION_RATE where PERIOD_NUMBER = 6 |
| Total Revenue | DIM_COHORTS[TOTAL_COHORT_REVENUE] |
| Avg Revenue | DIM_COHORTS[AVG_CUSTOMER_VALUE] |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| Cohort | Slicer (multi-select) | Last 12 months | Retention curves |
| Period Range | Slider | 0-12 | Heatmap columns |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click cohort row in heatmap | Highlight that cohort's retention curve |
| Click period column | Show period-specific breakdown |
| Hover on heatmap cell | Show exact retention %, customer count |
| Click cohort in table | Drill-through to cohort detail |

---

## Design Specifications

### Heatmap Color Scale

| Retention | Color | Hex |
|-----------|-------|-----|
| 80-100% | Dark Green | `#1B5E20` |
| 60-80% | Green | `#4CAF50` |
| 40-60% | Yellow | `#FFC107` |
| 20-40% | Orange | `#FF9800` |
| 0-20% | Red | `#D84315` |

---

## DAX Measures Required

```
Folder: _Base
├── Total Cohorts
├── Total Customers (All Cohorts)
├── Avg Cohort Size

Folder: _Analytical
├── P1 Retention Rate (Avg)
├── P3 Retention Rate (Avg)
├── P6 Retention Rate (Avg)
├── P12 Retention Rate (Avg)
├── Retention Rate by Period
├── Active Customers by Period

Folder: _Time Intelligence
├── Retention Trend (Improving/Declining)
├── Best Performing Cohort
├── Worst Performing Cohort

Folder: _Data Visualization
├── Retention Color (Conditional)
├── Cohort Label
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Retention pattern visible** | Clear decay curve shape |
| **Cohort comparison easy** | Can quickly identify best/worst cohorts |
| **Drop-off point clear** | Obvious where biggest retention loss occurs |
| **Trend direction visible** | Newer vs older cohorts comparison |

---

## Implementation Checklist

- [ ] Create matrix visual with proper pivoting
- [ ] Configure conditional formatting for heatmap
- [ ] Build retention curve line chart with cohort legend
- [ ] Add cohort size context bar chart
- [ ] Create period-specific retention measures
- [ ] Test cohort selection interactions
