# Executive Summary — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Executive Summary |
| **Page Number** | 1 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue (trust, authority) |

---

## Objective

**What decision does this page help make?**

This page answers: *"How is the business performing, and where should I focus my attention?"*

It serves as the **command center** — providing executives with a 10-second health check before drilling into specifics. The page should surface:
1. Current performance vs. expectations
2. Trend direction (improving or declining)
3. Red flags requiring immediate attention

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **CEO / Founder** | Morning check-in, board prep | 30 seconds |
| **VP of Operations** | Daily standup, issue triage | 1-2 minutes |
| **Data Analyst** | Starting point before deep dives | 10 seconds |

**Key insight**: These users don't have time to explore. The page must **push insights to them**, not require discovery.

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | What is our total revenue? | Core business health metric |
| 2 | How many orders did we process? | Operational volume indicator |
| 3 | How many unique customers purchased? | Customer base health |
| 4 | What is our average order value (AOV)? | Pricing/basket efficiency |
| 5 | Are we trending up or down? | Direction matters more than absolutes |
| 6 | What % of deliveries are on-time? | Operational quality signal |
| 7 | What is our average review score? | Customer satisfaction proxy |
| 8 | How many customers are at risk of churning? | Proactive retention signal |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "E-Commerce Executive Summary"                    [Date Range Slicer] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   REVENUE   │  │   ORDERS    │  │  CUSTOMERS  │  │     AOV     │            │
│  │   R$ 15.4M  │  │    96.4K    │  │    93.3K    │  │   R$ 160    │            │
│  │   ▲ +12.3%  │  │   ▲ +8.1%   │  │   ▲ +15.2%  │  │   ▼ -2.1%   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │                                         │  │      CUSTOMER HEALTH        │  │
│  │         REVENUE TREND (LINE)            │  │  ┌───────────────────────┐  │  │
│  │         with 30-day moving avg          │  │  │ On-Time Delivery: 92% │  │  │
│  │                                         │  │  │ Avg Review Score: 4.1 │  │  │
│  │   [Shows daily revenue + trend line]    │  │  │ At-Risk Customers: 8K │  │  │
│  │                                         │  │  └───────────────────────┘  │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌───────────────────────────┐  ┌───────────────────────────────────────────┐  │
│  │   RFM SEGMENT BREAKDOWN   │  │           TOP 5 CATEGORIES                │  │
│  │      (Donut Chart)        │  │           (Bar Chart)                     │  │
│  │                           │  │                                           │  │
│  │  Champions: 12%           │  │  Health & Beauty ████████████ R$ 1.2M    │  │
│  │  Loyal: 18%               │  │  Watches        █████████    R$ 980K     │  │
│  │  At Risk: 15%             │  │  Bed & Bath     ████████     R$ 870K     │  │
│  │  Hibernating: 25%         │  │  Sports         ███████      R$ 720K     │  │
│  │  Others: 30%              │  │  Furniture      ██████       R$ 650K     │  │
│  └───────────────────────────┘  └───────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards (Top Row)

| Visual | Measure Name | Source Table | Calculation | Format |
|--------|--------------|--------------|-------------|--------|
| Revenue | `Total Revenue` | FCT_ORDERS | `SUM(TOTAL_PAYMENT_VALUE)` | Currency (R$), 1 decimal |
| Orders | `Total Orders` | FCT_ORDERS | `DISTINCTCOUNT(ORDER_ID)` | Whole number, K suffix |
| Customers | `Total Customers` | DIM_CUSTOMERS | `DISTINCTCOUNT(CUSTOMER_UNIQUE_ID)` | Whole number, K suffix |
| AOV | `Avg Order Value` | FCT_ORDERS | `DIVIDE([Total Revenue], [Total Orders])` | Currency (R$), 0 decimals |

### KPI Variance Indicators

| Measure Name | Calculation | Display |
|--------------|-------------|---------|
| `Revenue MoM %` | `DIVIDE([Revenue This Month] - [Revenue Last Month], [Revenue Last Month])` | ▲/▼ with % |
| `Orders MoM %` | Same pattern | ▲/▼ with % |
| `Customers MoM %` | Same pattern | ▲/▼ with % |
| `AOV MoM %` | Same pattern | ▲/▼ with % |

### Revenue Trend (Line Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Line Chart |
| **X-Axis** | DIM_DATES[DATE] |
| **Y-Axis** | `Total Revenue` |
| **Secondary Line** | `Revenue 30-Day MA` from FCT_DAILY_REVENUE_TIME_SERIES |
| **Interaction** | Brush to filter other visuals |

### Customer Health Cards

| Metric | Source | Calculation |
|--------|--------|-------------|
| On-Time Delivery % | FCT_ORDERS | `DIVIDE(COUNTROWS(FILTER(FCT_ORDERS, [IS_ON_TIME_DELIVERY] = TRUE)), [Total Orders])` |
| Avg Review Score | FCT_ORDERS | `AVERAGE(REVIEW_SCORE)` |
| At-Risk Customers | FCT_CHURN_RISK | `COUNTROWS(FILTER(FCT_CHURN_RISK, [CHURN_STATUS] = "At Risk"))` |

### RFM Segment Breakdown (Donut)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Donut Chart |
| **Legend** | FCT_RFM_SEGMENTS[RFM_SEGMENT] |
| **Values** | `Customer Count` per segment |
| **Sort** | By count descending |

### Top Categories (Bar Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | FCT_CATEGORY_PERFORMANCE[PRODUCT_CATEGORY] |
| **X-Axis** | `SUM(TOTAL_REVENUE)` |
| **Top N** | 5 |
| **Sort** | Revenue descending |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| Date Range | Slicer (relative) | Last 12 months | All visuals |
| Order Status | Hidden filter | Exclude "canceled" | All visuals |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click RFM segment | Drill-through to RFM Analysis page |
| Click category bar | Drill-through to Product Performance page |
| Hover on trend line | Tooltip shows daily breakdown |
| Click "At-Risk" card | Drill-through to Churn Risk page |

---

## Design Specifications

### Color Palette

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary | Deep Blue | `#1E3A5F` | Headers, primary KPIs |
| Positive | Forest Green | `#2E7D32` | Upward trends, good metrics |
| Negative | Burnt Orange | `#D84315` | Downward trends, alerts |
| Neutral | Slate Gray | `#607D8B` | Supporting text, axes |
| Background | Off-White | `#FAFAFA` | Page background |
| Card Background | White | `#FFFFFF` | Visual containers |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Page Title | Segoe UI | 24px | Semibold |
| KPI Value | Segoe UI | 32px | Bold |
| KPI Label | Segoe UI | 12px | Regular |
| Variance | Segoe UI | 14px | Semibold |
| Chart Title | Segoe UI | 14px | Semibold |
| Axis Labels | Segoe UI | 10px | Regular |

### Visual Hierarchy

1. **Primary Focus**: KPI cards (top row) — largest, most prominent
2. **Secondary Focus**: Revenue trend — shows direction
3. **Supporting Context**: RFM breakdown + Categories — explains the "why"
4. **Health Indicators**: Customer health cards — proactive alerts

---

## DAX Measures Required

```
Folder: _Base
├── Total Revenue
├── Total Orders
├── Total Customers
├── Avg Order Value

Folder: _Time Intelligence
├── Revenue This Month
├── Revenue Last Month
├── Revenue MoM %
├── Revenue 30-Day MA
├── Orders MoM %
├── Customers MoM %
├── AOV MoM %

Folder: _Analytical
├── On-Time Delivery %
├── Avg Review Score
├── At-Risk Customer Count

Folder: _Data Visualization
├── Revenue Trend Arrow (▲/▼)
├── Variance Color (Green/Red)
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **10-second insight** | User can state business health in one sentence |
| **No dead ends** | Every visual leads somewhere (drill-through) |
| **No questions unanswered** | Top 8 questions all addressed |
| **Visual balance** | White space ≥ 30% of canvas |

---

## Implementation Checklist

- [ ] Create DAX measures in semantic model
- [ ] Build page layout in Power BI
- [ ] Apply color theme
- [ ] Configure interactions and drill-through
- [ ] Test with stakeholders
