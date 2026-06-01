# RFM Segmentation — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Customer Segmentation (RFM) |
| **Page Number** | 2 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with segment-specific accents |

---

## Objective

**What decision does this page help make?**

This page answers: *"Who are our customers, and how should we treat each group differently?"*

RFM (Recency, Frequency, Monetary) analysis segments customers into actionable groups. This page enables:
1. Identifying high-value customers to protect (Champions, Loyal)
2. Spotting at-risk customers before they churn
3. Prioritizing marketing spend by segment ROI potential

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **Marketing Manager** | Campaign planning, budget allocation | 5-10 minutes |
| **CRM Team** | Customer outreach prioritization | 3-5 minutes |
| **Executive** | Customer base health overview | 1-2 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | How are customers distributed across segments? | Resource allocation |
| 2 | What is the revenue contribution of each segment? | ROI prioritization |
| 3 | Which segments should we prioritize for retention? | Prevent revenue loss |
| 4 | Which segments have re-activation potential? | Growth opportunity |
| 5 | What are the RFM score distributions? | Understand scoring thresholds |
| 6 | Who are the individual Champions? | VIP treatment candidates |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Customer Segmentation (RFM Analysis)"            [Segment Slicer]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  CUSTOMERS  │  │  CHAMPIONS  │  │   AT RISK   │  │ HIBERNATING │            │
│  │    93.3K    │  │    11.2K    │  │    14.0K    │  │    23.3K    │            │
│  │   total     │  │    12%      │  │    15%      │  │    25%      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │     SEGMENT DISTRIBUTION (TREEMAP)      │  │   REVENUE BY SEGMENT (BAR)  │  │
│  │                                         │  │                             │  │
│  │  ┌───────────────┬─────────────┐       │  │  Champions    ████████ 35%  │  │
│  │  │               │             │       │  │  Loyal        ██████   22%  │  │
│  │  │   Champions   │   Loyal     │       │  │  Potential    ████     15%  │  │
│  │  │     12%       │    18%      │       │  │  At Risk      ███      12%  │  │
│  │  ├───────────────┼─────────────┤       │  │  Others       ██       16%  │  │
│  │  │  At Risk 15%  │ Hibernating │       │  │                             │  │
│  │  │               │    25%      │       │  │                             │  │
│  │  └───────────────┴─────────────┘       │  │                             │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    RFM SCORE SCATTER PLOT                                │   │
│  │    Y-Axis: Monetary | X-Axis: Frequency | Color: Recency Score          │   │
│  │    [Interactive: hover for customer details]                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  SEGMENT DETAIL TABLE                                                    │   │
│  │  Segment | Customers | Avg Recency | Avg Frequency | Avg Monetary | Rev  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source Table | Calculation |
|--------|--------------|--------------|-------------|
| Total Customers | `Total RFM Customers` | FCT_RFM_SEGMENTS | `COUNTROWS(FCT_RFM_SEGMENTS)` |
| Champions | `Champion Count` | FCT_RFM_SEGMENTS | `CALCULATE(COUNTROWS(...), RFM_SEGMENT = "Champions")` |
| At Risk | `At Risk Count` | FCT_RFM_SEGMENTS | `CALCULATE(COUNTROWS(...), RFM_SEGMENT = "At Risk")` |
| Hibernating | `Hibernating Count` | FCT_RFM_SEGMENTS | `CALCULATE(COUNTROWS(...), RFM_SEGMENT = "Hibernating")` |

### Segment Distribution (Treemap)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Treemap |
| **Group** | FCT_RFM_SEGMENTS[RFM_SEGMENT] |
| **Values** | `Customer Count` per segment |
| **Color** | Segment-specific colors (see design tokens) |

### Revenue by Segment (Bar Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | FCT_RFM_SEGMENTS[RFM_SEGMENT] |
| **X-Axis** | `SUM(MONETARY)` |
| **Data Labels** | Percentage of total |

### RFM Scatter Plot

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Scatter Chart |
| **X-Axis** | FCT_RFM_SEGMENTS[FREQUENCY] |
| **Y-Axis** | FCT_RFM_SEGMENTS[MONETARY] |
| **Legend/Color** | FCT_RFM_SEGMENTS[R_SCORE] |
| **Size** | Fixed or by MONETARY |
| **Details** | CUSTOMER_UNIQUE_ID (for tooltip) |

### Segment Detail Table

| Column | Source |
|--------|--------|
| Segment | RFM_SEGMENT |
| Customers | COUNT(CUSTOMER_UNIQUE_ID) |
| Avg Recency | AVERAGE(RECENCY) |
| Avg Frequency | AVERAGE(FREQUENCY) |
| Avg Monetary | AVERAGE(MONETARY) |
| Total Revenue | SUM(MONETARY) |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| RFM Segment | Slicer (multi-select) | All | All visuals |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click segment in treemap | Cross-filter other visuals to that segment |
| Click customer in scatter | Drill-through to customer detail (if available) |
| Hover on segment | Tooltip with segment definition and recommendations |

---

## Segment Definitions (Tooltip Content)

| Segment | Definition | Recommended Action |
|---------|------------|-------------------|
| Champions | Recent, frequent, high spenders | VIP treatment, early access |
| Loyal | Consistent purchasers | Loyalty rewards, upsell |
| Potential Loyalists | Recent with growth potential | Nurture, onboarding |
| New Customers | Just made first purchase | Welcome series, education |
| At Risk | Were engaged, declining | Win-back campaign |
| Can't Lose Them | High value but slipping | Personal outreach, incentives |
| Hibernating | Low engagement across metrics | Re-activation or sunset |
| Need Attention | Mixed signals | Targeted engagement |

---

## Design Specifications

### Segment Color Palette

| Segment | Hex | Rationale |
|---------|-----|-----------|
| Champions | `#1E3A5F` | Primary — best customers |
| Loyal | `#00897B` | Teal — reliable |
| Potential Loyalists | `#4CAF50` | Green — growth |
| New Customers | `#FFA000` | Amber — attention needed |
| At Risk | `#FF7043` | Coral — warning |
| Can't Lose Them | `#D84315` | Orange — urgent |
| Hibernating | `#90A4AE` | Gray — dormant |
| Need Attention | `#7B1FA2` | Purple — action required |

---

## DAX Measures Required

```
Folder: _Base
├── Total RFM Customers
├── Total Monetary Value

Folder: _Segments
├── Champion Count
├── Champion %
├── Loyal Count
├── At Risk Count
├── Hibernating Count
├── [One per segment]

Folder: _Analytical
├── Avg Recency by Segment
├── Avg Frequency by Segment
├── Avg Monetary by Segment
├── Revenue % by Segment
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Segment clarity** | User can explain each segment in plain language |
| **Actionable insights** | Each segment has clear recommended action |
| **Visual hierarchy** | Champions and At Risk are most prominent |
| **Drill capability** | Can explore individual customers within segments |

---

## Implementation Checklist

- [ ] Create DAX measures for each segment
- [ ] Build treemap with segment colors
- [ ] Configure scatter plot with proper axes
- [ ] Add segment definition tooltips
- [ ] Set up cross-filtering interactions
- [ ] Test drill-through functionality
