# Funnel Analysis — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Order Funnel Analysis |
| **Page Number** | 6 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with stage-specific colors |

---

## Objective

**What decision does this page help make?**

This page answers: *"Where are we losing orders in the fulfillment process, and how can we improve conversion?"*

Funnel analysis reveals:
1. Conversion rates at each fulfillment stage
2. Where the biggest drop-offs occur
3. Operational bottlenecks (approval, shipping, delivery)
4. Review submission patterns as satisfaction proxy

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **VP of Operations** | Process optimization | 5-10 minutes |
| **Logistics Manager** | Shipping/delivery performance | 3-5 minutes |
| **Customer Experience** | Review and satisfaction tracking | 2-3 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | What is our overall delivery rate? | End-to-end success |
| 2 | Where do orders drop off most? | Intervention priority |
| 3 | What is our cancellation rate? | Revenue leakage |
| 4 | How long does each stage take? | Operational efficiency |
| 5 | What percentage of customers leave reviews? | Engagement indicator |
| 6 | How do conversion rates trend over time? | Improvement tracking |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Order Funnel Analysis"                           [Month Slicer]      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  DELIVERY   │  │  CANCEL     │  │  REVIEW     │  │  AVG DAYS   │            │
│  │   RATE      │  │   RATE      │  │   RATE      │  │  TO DELIVER │            │
│  │    96.5%    │  │    0.6%     │  │    42%      │  │    12.3     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    ORDER FUNNEL (HORIZONTAL FUNNEL)                      │   │
│  │                                                                          │   │
│  │  Placed    ████████████████████████████████████████████████  96.4K  100% │   │
│  │  Approved  ██████████████████████████████████████████████    95.8K  99.4%│   │
│  │  Shipped   ████████████████████████████████████████████      94.2K  97.7%│   │
│  │  Delivered ██████████████████████████████████████████        93.0K  96.5%│   │
│  │  Reviewed  ██████████████████                                39.1K  40.6%│   │
│  │                                                                          │   │
│  │  [Drop-off indicators between stages]                                    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   STAGE TIMING (BAR CHART)              │  │  CONVERSION TREND (LINE)    │  │
│  │                                         │  │                             │  │
│  │  To Approval  ██  0.5 days              │  │   ___   Delivery Rate       │  │
│  │  To Ship      ████  2.1 days            │  │  /   \___                   │  │
│  │  In Transit   ████████  8.2 days        │  │ /        \___              │  │
│  │  Total        ████████████ 12.3 days    │  │                             │  │
│  │                                         │  │  --- Review Rate            │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌───────────────────────────┐  ┌───────────────────────────────────────────┐  │
│  │   DROP-OFF BREAKDOWN      │  │   MONTHLY FUNNEL DETAIL (TABLE)           │  │
│  │      (WATERFALL)          │  │                                           │  │
│  │                           │  │  Month | Placed | Delivered | Del% | Rev% │  │
│  │  Placed:      96.4K       │  │  Jan   │ 8.2K   │ 7.9K      │ 96%  │ 42%  │  │
│  │  -Canceled:   -0.6K       │  │  Feb   │ 8.5K   │ 8.2K      │ 96%  │ 41%  │  │
│  │  -Unavail:    -0.3K       │  │  Mar   │ 9.1K   │ 8.8K      │ 97%  │ 43%  │  │
│  │  -In Transit: -1.2K       │  │  ...   │        │           │      │      │  │
│  │  =Delivered:  93.0K       │  │                                           │  │
│  └───────────────────────────┘  └───────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Calculation |
|--------|--------------|--------|-------------|
| Delivery Rate | `Overall Delivery Rate` | FCT_ORDERS_FUNNEL | `SUM(OVERALL_DELIVERY_RATE)` (weighted avg) |
| Cancel Rate | `Cancellation Rate` | FCT_ORDERS_FUNNEL | `SUM(CANCELLATION_RATE)` |
| Review Rate | `Overall Review Rate` | FCT_ORDERS_FUNNEL | `SUM(OVERALL_REVIEW_RATE)` |
| Avg Days to Deliver | `Avg Delivery Days` | FCT_ORDERS_FUNNEL | `AVG(AVG_DAYS_TO_DELIVERY)` |

### Order Funnel (Funnel Chart)

| Stage | Source Column | Conversion |
|-------|---------------|------------|
| Placed | ORDERS_PLACED | 100% (baseline) |
| Approved | ORDERS_APPROVED | PLACED_TO_APPROVED_PCT |
| Shipped | ORDERS_SHIPPED | APPROVED_TO_SHIPPED_PCT |
| Delivered | ORDERS_DELIVERED | SHIPPED_TO_DELIVERED_PCT |
| Reviewed | ORDERS_REVIEWED | DELIVERED_TO_REVIEWED_PCT |

### Stage Timing (Bar Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | Stage labels |
| **X-Axis** | AVG_DAYS_TO_APPROVAL, AVG_DAYS_TO_SHIP, AVG_DAYS_IN_TRANSIT, AVG_DAYS_TO_DELIVERY |
| **Color** | Single color, darkening for total |

### Conversion Trend (Line Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Line Chart |
| **X-Axis** | MONTH_DATE |
| **Y-Axis** | OVERALL_DELIVERY_RATE, OVERALL_REVIEW_RATE |
| **Legend** | Metric type |

### Drop-off Breakdown (Waterfall)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Waterfall Chart |
| **Categories** | Placed, -Canceled, -Unavailable, -In Transit, =Delivered |
| **Values** | Order counts |
| **Colors** | Blue (positive), Red (negative) |

### Monthly Funnel Table

| Column | Source |
|--------|--------|
| Month | MONTH_YEAR |
| Placed | ORDERS_PLACED |
| Delivered | ORDERS_DELIVERED |
| Delivery % | OVERALL_DELIVERY_RATE |
| Review % | OVERALL_REVIEW_RATE |
| Avg AOV | AVG_ORDER_VALUE |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| Month | Slicer (range) | Last 12 months | All visuals |
| Year | Slicer | Current year | Time comparisons |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click funnel stage | Show stage detail breakdown |
| Click month in table | Filter to that month |
| Hover on funnel | Show absolute numbers and percentages |
| Click drop-off category | Drill into reasons (if available) |

---

## Design Specifications

### Funnel Stage Colors

| Stage | Hex | Description |
|-------|-----|-------------|
| Placed | `#1E3A5F` | Starting point |
| Approved | `#2E5A8F` | Progression |
| Shipped | `#4A7AB0` | Progression |
| Delivered | `#2E7D32` | Success |
| Reviewed | `#00897B` | Engagement |

### Drop-off Colors

| Type | Hex |
|------|-----|
| Positive flow | `#1E3A5F` |
| Canceled | `#D84315` |
| Unavailable | `#FF7043` |
| In Transit | `#FFA000` |

---

## DAX Measures Required

```
Folder: _Base
├── Total Orders Placed
├── Total Orders Delivered
├── Total Orders Reviewed

Folder: _Analytical
├── Placed to Approved %
├── Approved to Shipped %
├── Shipped to Delivered %
├── Delivered to Reviewed %
├── Overall Delivery Rate
├── Overall Review Rate
├── Cancellation Rate
├── Unavailability Rate

Folder: _Time Intelligence
├── Avg Days to Approval
├── Avg Days to Ship
├── Avg Days in Transit
├── Avg Days to Delivery
├── Delivery Rate MoM Change

Folder: _Data Visualization
├── Stage Label
├── Conversion Arrow
├── Drop-off Indicator
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Bottleneck visible** | Largest drop-off stage is immediately clear |
| **Timing context** | Understand how long each stage takes |
| **Trend direction** | Know if conversion is improving or declining |
| **Actionable insight** | Clear which stage needs attention |

---

## Implementation Checklist

- [ ] Build funnel visual with proper stage ordering
- [ ] Create waterfall for drop-off breakdown
- [ ] Configure timing bar chart with benchmarks
- [ ] Build conversion trend line chart
- [ ] Create monthly summary table
- [ ] Add stage-to-stage conversion calculations
- [ ] Configure conditional formatting for rates
