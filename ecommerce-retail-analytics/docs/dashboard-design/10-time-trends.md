# Time Trends — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Time Trends & Seasonality |
| **Page Number** | 10 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with trend accents |

---

## Objective

**What decision does this page help make?**

This page answers: *"How is the business trending over time, and what seasonal patterns should we plan for?"*

Time intelligence analysis reveals:
1. Revenue and order growth trajectories
2. Seasonal patterns and anomalies
3. Period-over-period comparisons (WoW, MoM, YoY)
4. Leading indicators via moving averages

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **Finance** | Forecasting, budget planning | 5-10 minutes |
| **Executive** | Business trajectory assessment | 2-3 minutes |
| **Operations** | Capacity planning | 3-5 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | What is our revenue growth rate? | Business health |
| 2 | How do we compare to prior periods? | Trend direction |
| 3 | What seasonal patterns exist? | Planning cycles |
| 4 | Are we accelerating or decelerating? | Momentum assessment |
| 5 | What does the moving average show? | Noise vs. signal |
| 6 | How are cumulative metrics progressing? | Goal tracking |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Time Trends & Seasonality"                    [Date Range Slicer]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  YTD        │  │  MOM        │  │  YOY        │  │  28-DAY     │            │
│  │  REVENUE    │  │  GROWTH     │  │  GROWTH     │  │  TREND      │            │
│  │  R$ 12.4M   │  │  +8.3%      │  │  +24.5%     │  │  ▲ +5.2%    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    DAILY REVENUE WITH MOVING AVERAGES                    │   │
│  │                                                                          │   │
│  │  Revenue │                                                               │   │
│  │          │    ∿∿∿∿∿  Daily Revenue (light)                              │   │
│  │          │   ────────  7-Day MA                                         │   │
│  │          │  ══════════  28-Day MA                                       │   │
│  │          │                                                               │   │
│  │          │    ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿                        │   │
│  │          │  ─────────────────────────────────────────                   │   │
│  │          │ ════════════════════════════════════════════                 │   │
│  │          └────────────────────────────────────────────────────────────  │   │
│  │             Jan   Feb   Mar   Apr   May   Jun   Jul   Aug              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   PERIOD COMPARISON (BAR/COLUMN)        │  │   CUMULATIVE REVENUE        │  │
│  │                                         │  │        (AREA CHART)         │  │
│  │        Current Period                   │  │                             │  │
│  │        Prior Period                     │  │        ___________________  │  │
│  │                                         │  │       /                     │  │
│  │  Week   ████████  ██████                │  │      /    YTD: R$ 12.4M    │  │
│  │  Month  ████████████  ██████████        │  │     /                       │  │
│  │  YTD    ████████████████  ████████████  │  │    /                        │  │
│  │                                         │  │   /                         │  │
│  │         [Current | Prior]               │  │  Jan  Mar  May  Jul  Sep    │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   SEASONALITY (HEATMAP BY DAY/MONTH)    │  │   GROWTH RATES TABLE        │  │
│  │                                         │  │                             │  │
│  │       Mon Tue Wed Thu Fri Sat Sun       │  │  Period  │ Orders │ Revenue │  │
│  │  Jan  ░░░ ░░░ ░░░ ░░░ ███ ███ ██        │  │  WoW     │ +3.2%  │ +4.1%   │  │
│  │  Feb  ░░░ ░░░ ░░░ ░░░ ███ ███ ██        │  │  MoM     │ +8.1%  │ +8.3%   │  │
│  │  Mar  ░░░ ░░░ ░░░ ░░░ ███ ███ ██        │  │  QoQ     │ +12.5% │ +15.2%  │  │
│  │  ...                                    │  │  YoY     │ +22.1% │ +24.5%  │  │
│  │                                         │  │                             │  │
│  │  [Dark = high volume days]              │  │  [Green/Red indicators]     │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Column |
|--------|--------------|--------|--------|
| YTD Revenue | `YTD Revenue` | FCT_DAILY_REVENUE_TIME_SERIES | YTD_REVENUE |
| MoM Growth | `Revenue MoM %` | FCT_DAILY_REVENUE_TIME_SERIES | REVENUE_GROWTH_MOM_PCT |
| YoY Growth | `Revenue YoY %` | FCT_DAILY_REVENUE_TIME_SERIES | REVENUE_GROWTH_YOY_PCT |
| 28-Day Trend | `28-Day MA Change` | FCT_DAILY_REVENUE_TIME_SERIES | ROLLING_AVG_REVENUE_28D trend |

### Daily Revenue with Moving Averages (Line Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Line Chart (multi-series) |
| **X-Axis** | DATE |
| **Y-Axis Lines** | TOTAL_REVENUE (daily), ROLLING_AVG_REVENUE_7D, ROLLING_AVG_REVENUE_28D |
| **Line Styles** | Daily (dotted/light), 7D (solid), 28D (thick) |
| **Secondary Axis** | Optional for TOTAL_ORDERS |

### Period Comparison (Grouped Bar)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Grouped Bar/Column |
| **Categories** | Week, Month, Quarter, YTD |
| **Series** | Current Period, Prior Period |
| **Values** | TOTAL_REVENUE (current vs WTD_REVENUE, MTD_REVENUE, etc.) |

### Cumulative Revenue (Area Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Area Chart |
| **X-Axis** | DATE |
| **Y-Axis** | CUMULATIVE_REVENUE or YTD_REVENUE |
| **Fill** | Gradient from primary color |

### Seasonality Heatmap

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Matrix with conditional formatting |
| **Rows** | Month (Jan-Dec) |
| **Columns** | Day of Week (Mon-Sun) |
| **Values** | AVG(TOTAL_ORDERS) or AVG(TOTAL_REVENUE) |
| **Color Scale** | Light (low) → Dark (high) |

### Growth Rates Table

| Metric | Orders Column | Revenue Column |
|--------|---------------|----------------|
| WoW | ORDER_GROWTH_WOW_PCT | REVENUE_GROWTH_WOW_PCT |
| MoM | ORDER_GROWTH_MOM_PCT | REVENUE_GROWTH_MOM_PCT |
| QoQ | Calculated | Calculated |
| YoY | ORDER_GROWTH_YOY_PCT | REVENUE_GROWTH_YOY_PCT |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| Date Range | Date Slicer | Last 12 months | All visuals |
| Year | Slicer | Current year | YoY comparisons |
| Granularity | Toggle | Daily | Switch to weekly/monthly |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Brush select on line chart | Zoom to date range |
| Click heatmap cell | Filter to that day/month combo |
| Click period in comparison | Show period detail |
| Hover on moving average | Show exact value and date |

---

## Design Specifications

### Line Chart Colors

| Series | Hex | Style |
|--------|-----|-------|
| Daily Revenue | `#90CAF9` | Dotted, thin |
| 7-Day MA | `#1E88E5` | Solid, medium |
| 28-Day MA | `#1E3A5F` | Solid, thick |
| 90-Day MA | `#0D2137` | Dashed, thick |

### Growth Indicator Colors

| Growth | Hex | Symbol |
|--------|-----|--------|
| Positive | `#2E7D32` | ▲ |
| Negative | `#D84315` | ▼ |
| Flat (±1%) | `#607D8B` | ─ |

### Heatmap Color Scale

| Intensity | Hex |
|-----------|-----|
| Low | `#E3F2FD` |
| Medium-Low | `#90CAF9` |
| Medium | `#42A5F5` |
| Medium-High | `#1E88E5` |
| High | `#1E3A5F` |

---

## DAX Measures Required

```
Folder: _Base (from table)
├── Total Revenue (Daily)
├── Total Orders (Daily)
├── Avg Order Value (Daily)

Folder: _Time Intelligence (from table)
├── YTD Revenue
├── MTD Revenue
├── WTD Revenue
├── QTD Revenue
├── Revenue MoM %
├── Revenue YoY %
├── Revenue WoW %
├── Orders MoM %
├── Orders YoY %

Folder: _Moving Averages (from table)
├── 7-Day MA Revenue
├── 28-Day MA Revenue
├── 90-Day MA Revenue
├── 365-Day MA Revenue

Folder: _Cumulative (from table)
├── Cumulative Revenue
├── Cumulative Orders

Folder: _Data Visualization
├── Growth Arrow
├── Growth Color
├── Period Label
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Trend direction clear** | User can state if business is growing/declining |
| **Seasonality visible** | Weekly and monthly patterns identifiable |
| **Period comparison easy** | Current vs prior periods side-by-side |
| **Leading indicators** | Moving averages show momentum before actuals |

---

## Implementation Checklist

- [ ] Build multi-line chart with proper styling
- [ ] Create period comparison grouped bar
- [ ] Configure cumulative area chart
- [ ] Build seasonality heatmap (day × month)
- [ ] Create growth rates summary table
- [ ] Add date range slicer with relative options
- [ ] Configure growth indicator formatting
- [ ] Test brush selection and zoom
