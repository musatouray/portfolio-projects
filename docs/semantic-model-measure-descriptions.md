# Semantic Model — Measure Business Descriptions

Recommended one-line business descriptions for every measure in the **Ecommerce Analytics** semantic model, derived from each measure's DAX, its dependencies, and model context. Descriptions are written to be dropped straight into TMDL as `///` descriptions.

Grain notes used throughout:
- `FCT_ORDERS` = one row per order; `FCT_ORDER_ITEMS` = one row per order line.
- `FCT_RFM_SEGMENTS` = **cumulative monthly snapshot** per customer (customer × month).
- `FCT_COHORT_RETENTION` = cohort-month × period-number grain.
- Time intelligence uses UDF `TimeIntelligence.PY()` (prior-year / SPLY); colors use UDF `Color.YoYGrowthPct()`; KPI card strings use UDF `Format.YoYAbsoluteAndRelative()`.

---

## 00_Base — Fct_Orders

| Measure | Business description |
|---|---|
| Total Revenue | Total customer payments received (`SUM` of order payment value); the headline revenue metric. |
| Total Orders | Count of orders in context. |
| Unique Customers | Distinct customers who placed orders (distinct customer key on order items). |
| Average Order Value | Revenue divided by orders — average spend per order (AOV). |
| Average Review Score | Mean 1–5 customer review score for orders in context. |
| Total Freight | Total shipping/freight charges billed. |
| Delivery Rate | Share of orders with status "delivered". |
| On-Time Delivery Rate | Of delivered orders, the share that arrived on or before the estimated delivery date. |

## 00_Base — Fct_Order_Items

| Measure | Business description |
|---|---|
| Order Items Total Revenue | Product-line revenue (`SUM` of item total) — revenue at the order-line grain, used by product/category analysis. |
| Order Items Total Orders | Distinct orders represented in the order-items table. |
| Order Items AOV | Average order value computed from order-item revenue ÷ order-item orders. |

## 01_Segments — RFM

| Measure | Business description |
|---|---|
| Avg Recency (Days) | Average days since last purchase across customers, at the latest snapshot month. |
| Avg Frequency | Average number of orders per customer, at the latest snapshot month. |
| Avg Monetary | Average customer revenue, at the latest snapshot month. |
| RFM Latest Snapshot | The selected (or most recent) snapshot month from the disconnected calendar; anchors all RFM point-in-time measures. |
| RFM PY Snapshot | The snapshot month exactly one year before the latest snapshot, for year-over-year RFM comparisons. |
| RFM Unique Customers | Customer count at the latest snapshot month (point-in-time segment population). |
| RFM Total Orders | Total orders at the latest snapshot month. |
| RFM Total Revenue | Total revenue at the latest snapshot month. |
| RFM Revenue Share % | A segment's share of total revenue across all RFM segments at the latest snapshot. |
| All Segments Revenue | Revenue across every RFM segment (segment filters removed) — the denominator for segment share. |
| RFM Remaining % | Complement of RFM Revenue Share % (1 − share); used for gauge/"remainder" visuals. |
| RFM PY Customers | Customer count one year prior to the latest snapshot. |
| RFM PY Orders | Total orders one year prior to the latest snapshot. |
| RFM PY Revenue | Total revenue one year prior to the latest snapshot. |
| RFM Customers YoY % | Year-over-year growth in customer count for the segment. |
| RFM Orders YoY % | Year-over-year growth in orders for the segment. |
| RFM Revenue YoY % | Year-over-year growth in revenue for the segment. |
| RFM Period Revenue | Revenue at the selected snapshot period, for period-scoped RFM views. |
| RFM Segment Label | The RFM segment name in the current row/selection (display helper). |

## 01_Segments — RFM — Transitions

| Measure | Business description |
|---|---|
| Transition Count | Customers who were in the "From" segment at the prior snapshot and the "To" segment at the current snapshot — the size of each segment-to-segment migration. |
| Transition % of Source | Share of the source segment's customers that moved to the target segment between snapshots. |
| Transition Window Label | Dynamic subtitle naming the two snapshot months being compared (e.g. "Segment migration: May 2026 → Jun 2026"). |

## 01_Segments — CLV

| Measure | Business description |
|---|---|
| Total Historical CLV | Sum of realized lifetime revenue across customers (historical customer value to date). |
| Total Predicted CLV | Sum of modeled 12-month predicted customer lifetime value. |
| High Value Customers | Count of customers in the "High" value segment. |
| Medium Value Customers | Count of customers in the "Medium" value segment. |
| Low Value Customers | Count of customers in the "Low" value segment. |
| High Value CLV Revenue % | Share of total historical CLV contributed by High-value customers. |
| Medium Value CLV Revenue % | Share of total historical CLV contributed by Medium-value customers. |
| Low Value CLV Revenue % | Share of total historical CLV contributed by Low-value customers. |

## 04_Funnel

| Measure | Business description |
|---|---|
| Orders Placed | **Placeholder/stub** (returns 0) reserved for the order-lifecycle funnel; not yet implemented against a live source. |

## 05_Cohort

| Measure | Business description |
|---|---|
| Cohort Size | Number of customers in the qualifying acquisition cohorts (respects the cohort-size threshold and as-of date parameters). |
| Retained Customers | Active customers from the cohort still purchasing in the period. |
| Retention Rate | Retained customers ÷ cohort size — the cohort retention percentage. |
| Cohort Churn Rate | Complement of retention rate (1 − retention). |
| Total Cohorts | Distinct number of cohort-period records in context. |
| Cohort Revenue | Period revenue for qualifying cohorts. |
| Cohort Orders | Period orders for qualifying cohorts. |
| Cohort Avg Order Value | Cohort revenue ÷ cohort orders. |
| Cohort Avg Customer Value | Cohort revenue ÷ cohort size (revenue per acquired customer). |
| Cohort Initial Revenue | Cohort's period-0 (acquisition month) revenue — the baseline for revenue-retention ratios. |
| Cohort Lifetime Orders | Total cohort orders across all periods (period filter removed). |
| P1 Retention Rate | Retention rate at period 1 (first month after acquisition). |
| P3 Retention Rate | Retention rate at period 3. |
| P6 Retention Rate | Retention rate at period 6. |
| Avg P1-P6 Drop | Retention decay from period 1 to period 6 (early-life churn severity). |
| Latest Cohort Size | Size of the most recent cohort at period 0. |
| Cohort Gross Retained Revenue (GRR) | Retained revenue excluding expansion — revenue kept from the original cohort. |
| Cohort Net Retained Revenue (NRR) | Retained revenue including expansion/up-sell from the cohort. |
| Gross Revenue Retention (GRR) % | Gross retained revenue ÷ cohort initial revenue (capped at ≤100%). |
| Net Revenue Retention (NRR) % | Net retained revenue ÷ cohort initial revenue (can exceed 100% when expansion outweighs churn). |
| Formatting Avg Cohort Orders | Average period orders per cohort (helper for formatted display). |

## 06_Market Basket

| Measure | Business description |
|---|---|
| Total Product Pairs | Count of product-pair association rules in context. |
| Avg Support % | Average support — how often a product pair appears together across all orders. |
| Avg Confidence % | Average confidence — likelihood of buying product B given product A. |
| Avg Lift | Average lift — how much more often A and B are bought together than chance (>1 = positive affinity). |
| High Lift Pairs | Count of product pairs with lift above 1.5 (strong affinity). |
| Total Pair Occurrences | Total number of co-purchase occurrences across all pairs. |
| Cross-Sell Opportunities | Count of pairs that are actionable cross-sells (lift > 1 and confidence > 10%). |
| Max Lift | Highest lift value among product pairs in context. |
| Max Support % | Highest support value among product pairs in context. |

## 03_Product (Pareto)

| Measure | Business description |
|---|---|
| Running Total Product Revenue | Cumulative product-category revenue in descending order (for Pareto/ABC curves). |
| Running Total Product Revenue % | Cumulative revenue as a running share of the selected total. |
| Product Revenue % of Grand Total | A category's revenue as a share of all selected categories. |
| Pareto Best-selling Revenue | Revenue from the "vital few" categories whose cumulative share is within the Pareto threshold. |
| Pareto Others Revenue | Revenue from the remaining ("trivial many") categories beyond the threshold. |
| Pareto Cutoff Marker | The revenue value marking the Pareto threshold line on the chart. |
| Pareto Category Color Flag | Flags each category as best-selling vs other, for conditional coloring. |
| Selected Pareto Segment | The Pareto segment ("Best-selling"/"Others") selected in the disconnected table. |

## 07_Analytical

| Measure | Business description |
|---|---|
| Single Purchaser Count | Customers who placed exactly one order (one-time buyers). |
| Repeat Purchaser Count | Customers who placed more than one order. |
| Single Purchaser % | Share of customers who bought only once. |
| Repeat Purchaser % | Share of customers who bought more than once (repeat rate). |
| Avg Orders per Customer | Total orders ÷ unique customers. |
| Revenue per Customer | Total revenue ÷ unique customers. |

## 08_Time Intelligence — Prior Year (SPLY)

| Measure | Business description |
|---|---|
| Prior Year Revenue | Same-period-last-year revenue. |
| Prior Year Orders | Same-period-last-year orders. |
| Prior Year Customers | Same-period-last-year unique customers. |
| Prior Year AOV | Same-period-last-year average order value. |
| Prior Year On-Time Delivery | Same-period-last-year on-time delivery rate. |
| Prior Year Avg Review Score | Same-period-last-year average review score. |
| Order Items PY Revenue | Prior-year order-item revenue. |
| Order Items PY Orders | Prior-year order-item order count. |
| Order Items PY AOV | Prior-year order-item AOV. |

## 08_Time Intelligence — Year over Year

| Measure | Business description |
|---|---|
| Revenue YoY % | Year-over-year revenue growth. |
| Orders YoY % | Year-over-year order growth. |
| Unique Customers YoY % | Year-over-year customer growth. |
| AOV YoY % | Year-over-year AOV growth. |
| On Time Delivery YoY % | Year-over-year change in on-time delivery rate. |
| Avg Review Score YoY % | Year-over-year change in average review score. |
| Order Items Revenue YoY % | Year-over-year order-item revenue growth. |
| Order Items Orders YoY % | Year-over-year order-item order growth. |
| Order Items AOV YoY % | Year-over-year order-item AOV growth. |

## 09_Time Series

| Measure | Business description |
|---|---|
| Cumulative Revenue | Running total of revenue over the selected date range. |
| Cumulative Orders | Running total of orders over the selected date range. |
| Time Series PY | Prior-year value of the metric currently selected (Revenue/Orders/AOV) for the trend chart. |
| Time Series MoM Growth % | Month-over-month growth of the selected time-series metric. |
| Time Series Blank Placeholder | Intentional blank measure used as a spacer/placeholder in time-series visuals. |

## 10_Geographic

| Measure | Business description |
|---|---|
| Geo Revenue | Revenue by geography. ⚠️ References `FCT_GEO_PERFORMANCE`, which is not in the current model — needs repointing to `FCT_ORDERS` + `DIM_CUSTOMERS[STATE]` or the table must be added. |
| Geo Orders | Orders by geography. ⚠️ Same `FCT_GEO_PERFORMANCE` dependency issue as Geo Revenue. |

## 11_Custom Period

| Measure | Business description |
|---|---|
| Start and End Dates | Formatted "start – end" label of the active date range (or "No Date Range Selected"). |
| Custom Period Slicer Disable | Controls whether the custom date slicer is enabled based on the selected period. |
| Custom Period Slicer Title | Dynamic title for the custom-period slicer. |
| Custom Period Slicer Disable Color | Color that greys out the custom slicer when a preset period is chosen. |

## 12_Top/Bottom N

| Measure | Business description |
|---|---|
| Rank: Products by Revenue | Flags whether a category belongs to the Top-N, Bottom-N, or middle-separator rows for the ranking table. |
| Display Category | Category name for ranked rows; shows a "⋮" separator for the collapsed middle. |
| Display Rank Number | The rank position shown for Top/Bottom rows; "⋮" for the middle separator. |
| Display Revenue Value | Revenue shown for ranked rows; "⋮" for the middle separator. |
| Display Orders Total | Order count shown for ranked rows; "⋮" for the middle separator. |
| Display % of Grand Total | Category revenue share of the grand total for ranked rows; "⋮" for the middle. |
| Ranking Sort Order | Sort key that orders Top-N, the two separator rows, then Bottom-N. |

## 14_Viz Helpers — KPI Cards (absolute + relative)

| Measure | Business description |
|---|---|
| Formatted Revenue Absolute and Relative | KPI-card string combining current revenue with its YoY change. |
| Formatted Orders Absolute And Relative | KPI-card string combining current orders with YoY change. |
| Formatted AOV Absolute And Relative | KPI-card string combining current AOV with YoY change. |
| Formatted On-Time Delivery Absolute And Relative | KPI-card string combining on-time delivery rate with YoY change. |
| Formatted Avg Review Score Absolute And Relative | KPI-card string combining review score with YoY change. |
| Formatted Unique Customers Absolute And Relative | KPI-card string combining customers with YoY change. |
| Formatted Order Items Revenue Absolute and Relative | KPI-card string for order-item revenue with YoY change. |
| Formatted Order Items Orders Absolute And Relative | KPI-card string for order-item orders with YoY change. |
| Formatted Order Items AOV Absolute And Relative | KPI-card string for order-item AOV with YoY change. |

## 14_Viz Helpers — Color (conditional formatting)

| Measure | Business description |
|---|---|
| Revenue YoY Font Color / Background Color | Font/fill color encoding revenue YoY direction (green up / red down). |
| Orders YoY Font Color / Background Color | Font/fill color encoding orders YoY direction. |
| AOV YoY Font Color / Background Color | Font/fill color encoding AOV YoY direction. |
| Avg Review Score YoY Font Color / Background Color | Font/fill color encoding review-score YoY direction. |
| On Time Delivery YoY Font Color / Background Color | Font/fill color encoding on-time-delivery YoY direction. |
| Unique Customers YoY Font Color / Background Color | Font/fill color encoding customer YoY direction. |
| RFM Orders/Revenue/Customers YoY Font Color | Font color encoding YoY direction for the RFM KPI cards. |
| Churn Status Color | Color scale for churn rate (green safe → orange/red high churn). |
| Retention Heatmap Color | Blue color scale for cohort retention rate (light → dark by strength). |
| CLV Segment Color | Color per CLV value segment (High/Medium/Low). |
| Lift Color | Color scale for market-basket lift strength. |
| RFM Segment Colors | Color per RFM segment. ⚠️ Uses the **old 5-segment** names (Champions/Loyalists/New Customers/At Risk-Hibernating/General Pool); the model now emits **8** segments, so unmatched segments fall to the default color — update to the 8-segment palette. |
| Pareto Matrix Color | Highlight color for the best-selling Pareto segment. |
| Cohort Size Title Font Color | Transparent font color used to hide a helper title. |
| Positive Color / Negative Color / Neutral Color | Sentiment palette constants (green / red / grey) reused across visuals. |

## 14_Viz Helpers — Titles / Subtitles / Legends

| Measure | Business description |
|---|---|
| Selected Metric Title | Title reflecting the selected metric and period (Orders/Revenue/AOV). |
| Custom Period Title | Title showing the active custom or preset period with its date range. |
| Top/Bottom N Title | "Top and Bottom N Products by Revenue" title reflecting the N selection. |
| RFM Segment Snapshot Title | "Snapshot month is as of …" label for RFM visuals. |
| Choose Cohort Size | Prompt/label reflecting the selected minimum cohort size. |
| Cohort Heatmap Title | Heatmap title naming the selected cohort metric (Retention/Active/Revenue/Orders/GRR/NRR). |
| Cohort Period Subtitle | "Cohort Period: min – max" date-range subtitle. |
| Cohort Barchart Title | Bar-chart title naming the selected cohort metric. |
| Time Series Subtitle | Date-range subtitle for the time-series page. |
| Time Series Products Selected Filters | Lists the selected product categories (or "All Products"). |
| Time Series Selected Years Filters | Lists the selected years (or the full range). |
| Time Series Moving Averages Title | Title like "Revenue vs 6 Months Moving Average". |
| Time Series MoM Title | Title like "Revenue MoM Growth". |
| Time Series Moving Averages Legend | Inline SVG legend for actual vs moving-average series. |
| Time Series Current and PY Title | Title like "Revenue and Revenue (PY)". |
| Time Series Current and PY Subtitle | "Period: 2026 vs 2025" subtitle. |
| Time Series Current and PY Legend | Inline SVG legend for current vs prior-year series. |
| Pareto Title | Sentence summarizing how many top categories make up the threshold share of revenue. |

## 14_Viz Helpers — SVG / HTML / Narrative

| Measure | Business description |
|---|---|
| Star Rating Review | Animated 5-star SVG rendering of the average review score. |
| Revenue Currency SVG Icon | Decorative animated "$" currency SVG icon for revenue cards. |
| Orders Sparkline SVG | Inline SVG sparkline of monthly orders over time. |
| Executive Summary Page | Auto-generated narrative paragraph summarizing revenue, orders, AOV, delivery, satisfaction, RFM concentration, and top/bottom category. |
| Landing Page Dark | Full HTML landing page (dark theme) with live KPI tiles and YoY indicators, for the HTML-content visual. |
| Landing Page Light | Light-theme variant of the HTML landing page. |
| Revenue Format Large | Compact revenue string ($X.XM / $X.XK) for large-number display. |
| Last Refresh | "Refreshed: …" timestamp label of the last data refresh. |

## 14_Viz Helpers — Selected Metric / Custom Period switching

| Measure | Business description |
|---|---|
| Max Selected Metric | Maximum value of the currently selected metric (axis/scaling helper). |
| Min Selected Metric | Minimum value of the currently selected metric. |
| Max Selected Metric Label | Formatted label for the max of the selected metric. |
| Min Selected Metric Label | Formatted label for the min of the selected metric. |
| As on Cohort Date | The "as of" cohort month from the disconnected calendar (defaults to latest). |

## Parameter tables (what-if)

| Measure | Business description |
|---|---|
| Param: Cohort Size Value | Selected minimum cohort-size threshold (default 1). |
| Param: Pareto Threshold Value | Selected Pareto cumulative-revenue threshold (default 80%). |

## Placeholders / stubs

| Measure | Business description |
|---|---|
| Blank | Returns BLANK() — spacer/placeholder. |
| Label Placeholder | Returns 0 — placeholder for a visual label slot. |
| Orders Placed | Returns 0 — reserved funnel stub (see 04_Funnel). |
| Total Churn Customers | Returns 0 — churn-page stub; churn now lives in `FCT_RFM_SEGMENTS` and should be rebuilt from `CHURN_STATUS`. |
| Time Series Blank Placeholder | Returns BLANK() — time-series spacer. |

---

## Issues surfaced during review

1. **`RFM Segment Colors`** maps the **old 5-segment** scheme, but the model now emits **8** RFM segments. Unmatched segments render in the default color. Update the SWITCH to the 8 current segments (Champions, New Customers, Loyal Customers, Potential Loyalists, At Risk, Hibernating, Need Attention, Lost).
2. **`Geo Revenue` / `Geo Orders`** reference `FCT_GEO_PERFORMANCE`, which is not a table in the current model — repoint to `FCT_ORDERS` + `DIM_CUSTOMERS[STATE]` or add the geo mart.
3. **Stub measures** returning 0/BLANK (`Orders Placed`, `Total Churn Customers`, `Label Placeholder`, `Blank`, `Time Series Blank Placeholder`) are intentional placeholders — fine to keep, but `Total Churn Customers` should be rebuilt from `FCT_RFM_SEGMENTS[CHURN_STATUS]` if the churn page is completed.
4. **`GRR %` / `NRR %`** reference `'fct_cohort_retention'[period]` in lowercase; DAX resolves this case-insensitively, but aligning to `FCT_COHORT_RETENTION[PERIOD]` keeps naming consistent.
