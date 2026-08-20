# Geographic Insights — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Geographic Performance |
| **Page Number** | 9 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with regional accents |

---

## Objective

**What decision does this page help make?**

This page answers: *"Where are our strongest and weakest markets, and where should we focus expansion efforts?"*

Geographic analysis reveals:
1. Regional revenue concentration
2. Delivery performance by location
3. Market penetration opportunities
4. State-level customer satisfaction differences

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **Regional Manager** | Territory performance review | 5-10 minutes |
| **Logistics** | Delivery optimization | 3-5 minutes |
| **Strategy** | Expansion planning | 5-10 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | Which states generate the most revenue? | Market prioritization |
| 2 | How does AOV vary by region? | Pricing/basket strategy |
| 3 | Where is delivery performance best/worst? | Logistics optimization |
| 4 | What is customer satisfaction by state? | Service quality gaps |
| 5 | Where are untapped opportunities? | Expansion decisions |
| 6 | How do regions trend over time? | Growth identification |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Geographic Performance"                          [State Slicer]      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  STATES     │  │  TOP STATE  │  │  AVG AOV    │  │  AVG REVIEW │            │
│  │  COVERED    │  │  REVENUE    │  │  BY STATE   │  │  BY STATE   │            │
│  │    27       │  │ SP: R$ 5.2M │  │   R$ 154    │  │    4.1      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │        BRAZIL MAP (CHOROPLETH)          │  │   STATE REVENUE RANKING     │  │
│  │                                         │  │        (BAR CHART)          │  │
│  │         ┌─────┐                         │  │                             │  │
│  │        /       \                        │  │  SP  ████████████████ 34%   │  │
│  │       /    AM   \                       │  │  RJ  ██████████      13%    │  │
│  │      │           │                      │  │  MG  ████████        10%    │  │
│  │       \   PA    /                       │  │  RS  ██████          7%     │  │
│  │        │       │                        │  │  PR  █████           6%     │  │
│  │         │ MT  │                         │  │  SC  ████            5%     │  │
│  │          │   │ MG  RJ                   │  │  BA  ████            5%     │  │
│  │           │ SP │                        │  │  ...                        │  │
│  │            └──┘                         │  │                             │  │
│  │                                         │  │                             │  │
│  │  [Color: Revenue intensity]             │  │  [% of total revenue]       │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   AOV BY STATE (SORTED BAR)             │  │   REVIEW SCORE BY STATE     │  │
│  │                                         │  │        (SORTED BAR)         │  │
│  │  AC  ████████████████  R$ 210           │  │                             │  │
│  │  AP  ███████████████   R$ 198           │  │  SC  ████████████  4.3      │  │
│  │  RR  ██████████████    R$ 185           │  │  PR  ███████████   4.2      │  │
│  │  AM  █████████████     R$ 172           │  │  RS  ██████████    4.1      │  │
│  │  ...                                    │  │  SP  █████████     4.0      │  │
│  │  SP  ████████          R$ 148           │  │  ...                        │  │
│  │                                         │  │                             │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  STATE DETAIL TABLE                                                      │   │
│  │  State | Orders | Revenue | AOV | Delivered % | Canceled % | Avg Review  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Calculation |
|--------|--------------|--------|-------------|
| States Covered | `State Count` | FCT_GEO_PERFORMANCE | `DISTINCTCOUNT(STATE)` |
| Top State Revenue | `Top State Revenue` | FCT_GEO_PERFORMANCE | `MAX state by SUM(TOTAL_REVENUE)` |
| Avg AOV by State | `Avg State AOV` | FCT_GEO_PERFORMANCE | `AVERAGE(AVERAGE_ORDER_VALUE)` |
| Avg Review by State | `Avg State Review` | FCT_GEO_PERFORMANCE | `AVERAGE(AVERAGE_REVIEW_SCORE)` |

### Brazil Map (Choropleth)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Filled Map (Brazil) |
| **Location** | STATE (2-letter code) |
| **Color Saturation** | SUM(TOTAL_REVENUE) |
| **Tooltips** | Revenue, Orders, AOV, Review Score |

### State Revenue Ranking (Bar)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | STATE |
| **X-Axis** | SUM(TOTAL_REVENUE) |
| **Data Labels** | Percentage of total |
| **Sort** | Revenue descending |
| **Top N** | 10 states |

### AOV by State (Bar)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | STATE |
| **X-Axis** | AVERAGE_ORDER_VALUE |
| **Sort** | AOV descending |
| **Color** | Gradient based on value |

### Review Score by State (Bar)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | STATE |
| **X-Axis** | AVERAGE_REVIEW_SCORE |
| **Sort** | Score descending |
| **Reference Line** | Overall average |

### State Detail Table

| Column | Source |
|--------|--------|
| State | STATE |
| Orders | SUM(TOTAL_ORDERS) |
| Revenue | SUM(TOTAL_REVENUE) |
| AOV | AVERAGE_ORDER_VALUE |
| Delivered % | DELIVERED_ORDERS / TOTAL_ORDERS |
| Canceled % | CANCELED_ORDERS / TOTAL_ORDERS |
| Avg Review | AVERAGE_REVIEW_SCORE |
| Cities | UNIQUE_CITIES |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| State | Slicer (multi-select) | All | All visuals |
| Month | Slicer | Last 12 months | Time-based filtering |
| Region | Slicer (optional) | All | Group states by region |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click state on map | Filter all visuals to that state |
| Click state in bar chart | Cross-highlight map region |
| Hover on map region | Show state metrics in tooltip |
| Click state in table | Drill-through to state detail (if available) |

---

## Brazilian Regions Reference

| Region | States | Typical Characteristics |
|--------|--------|------------------------|
| Southeast | SP, RJ, MG, ES | Highest volume, most developed |
| South | PR, SC, RS | High AOV, good satisfaction |
| Northeast | BA, PE, CE, etc. | Growing market, logistics challenges |
| North | AM, PA, etc. | Highest AOV (freight), longest delivery |
| Central-West | GO, MT, MS, DF | Medium volume, improving logistics |

---

## Design Specifications

### Map Color Scale

| Revenue Percentile | Hex |
|-------------------|-----|
| 0-20% | `#E3F2FD` |
| 20-40% | `#90CAF9` |
| 40-60% | `#42A5F5` |
| 60-80% | `#1E88E5` |
| 80-100% | `#1E3A5F` |

### Performance Indicator Colors

| Performance | Hex | Usage |
|-------------|-----|-------|
| Above Average | `#2E7D32` | AOV, Review above mean |
| Average | `#FFC107` | Within 1 std dev |
| Below Average | `#D84315` | Below mean |

---

## DAX Measures Required

```
Folder: _Base
├── Total States
├── Total Revenue (Geo)
├── Total Orders (Geo)
├── Total Cities

Folder: _Analytical
├── Revenue by State
├── Revenue % by State
├── AOV by State
├── Avg Review by State
├── Delivery Success Rate by State
├── Cancellation Rate by State

Folder: _Comparative
├── State vs National AOV
├── State vs National Review
├── State Revenue Rank

Folder: _Data Visualization
├── Map Color Value
├── State Abbreviation
├── Performance Indicator
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Geographic distribution visible** | Map shows revenue concentration at a glance |
| **Regional comparison easy** | Can compare states on multiple dimensions |
| **Opportunity identification** | Underperforming vs potential markets clear |
| **Operational insights** | Delivery/satisfaction gaps by region visible |

---

## Implementation Checklist

- [ ] Configure Brazil map with state boundaries
- [ ] Build revenue ranking bar chart
- [ ] Create AOV and review score comparisons
- [ ] Add state detail table with all metrics
- [ ] Configure map-to-chart cross-filtering
- [ ] Add regional grouping (optional)
- [ ] Include reference lines for averages
