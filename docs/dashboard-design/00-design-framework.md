# Dashboard Design Framework

Design specifications for the E-Commerce Analytics dashboard.

---

## Theme Design

See `ecommerce-analytics-theme.json` for the Power BI theme file.

### Color Palette

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Primary | Deep Blue | `#1E3A5F` | Headers, KPIs, primary series |
| Primary Light | Steel Blue | `#4A6FA5` | Secondary elements |
| Positive | Forest Green | `#2E7D32` | Growth, success, upward trends |
| Negative | Burnt Orange | `#D84315` | Decline, alerts, risk |
| Neutral | Slate Gray | `#607D8B` | Supporting text, axes |
| Background | Off-White | `#FAFAFA` | Page canvas |
| Card | White | `#FFFFFF` | Visual containers |

### Data Visualization Colors

Sequential palette for multi-series charts:

| Order | Hex |
|-------|-----|
| 1 | `#1E3A5F` |
| 2 | `#00897B` |
| 3 | `#FFA000` |
| 4 | `#7B1FA2` |
| 5 | `#C2185B` |
| 6 | `#0097A7` |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Page Title | Segoe UI | 24px | Semibold |
| KPI Value | Segoe UI | 32px | Bold |
| KPI Label | Segoe UI | 12px | Regular |
| Chart Title | Segoe UI | 14px | Semibold |
| Axis Labels | Segoe UI | 10px | Regular |

### Spacing

All spacing uses an **8px grid**:

| Token | Value |
|-------|-------|
| Card padding | 16px |
| Card margin | 8px |
| Section gap | 24px |
| Card border radius | 8px |

---

## Measure Organization

Organize DAX measures into folders by the question they answer:

| Folder | Question | Examples |
|--------|----------|----------|
| `_Base` | How much? | `Total Revenue`, `Order Count`, `Customer Count` |
| `_Analytical` | How much, filtered? | `Revenue by Segment`, `Orders by Status` |
| `_Time Intelligence` | Compared to when? | `Revenue MoM %`, `YoY Growth`, `30-Day MA` |
| `_Segments` | Which group? | `RFM Segment`, `CLV Tier`, `Churn Status` |
| `_Data Visualization` | How to display? | `Trend Arrow`, `Conditional Color` |

---

## Page Structure

| # | Page | Focus | Primary Tables |
|---|------|-------|----------------|
| 1 | Executive Summary | KPIs, trends, health | FCT_ORDERS, FCT_DAILY_REVENUE |
| 2 | Customer Segmentation | RFM analysis | FCT_RFM_SEGMENTS |
| 3 | Customer Lifetime Value | CLV tiers | FCT_CLV_CUSTOMER |
| 4 | Cohort Retention | Retention heatmap | FCT_COHORT_RETENTION |
| 5 | Churn Risk | At-risk customers | FCT_CHURN_RISK |
| 6 | Funnel Analysis | Order funnel | FCT_ORDERS_FUNNEL |
| 7 | Product Performance | Pareto analysis | FCT_PARETO_PRODUCTS |
| 8 | Market Basket | Cross-sell patterns | FCT_MARKET_BASKET |
| 9 | Geographic Insights | Regional performance | FCT_GEO_PERFORMANCE |
| 10 | Time Trends | Time intelligence | FCT_DAILY_REVENUE_TIME_SERIES |
