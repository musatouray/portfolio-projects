# DAX Refactors Applied — Change Log

Companion to `POWERBI_REVIEW.md`. Every change below was made directly to `Ecommerce Analytics.SemanticModel/definition/tables/_Measures.tmdl` (and a couple of TMDL table files). Open `_Measures.tmdl` in Power BI Desktop / Tabular Editor to re-validate.

> All changes are **in-place** at the same `lineageTag` so existing visuals continue to bind without rewiring.

---

## A. Correctness fixes (changed numbers — verify visuals)

| # | Measure | Was | Now | Why |
|---|---|---|---|---|
| A1 | `Avg Retention Rate` | `AVERAGE(RETENTION_RATE)` | `DIVIDE(SUM(ACTIVE_CUSTOMERS), SUM(COHORT_SIZE))` | Average-of-averages bug; now correctly weighted by cohort size |
| A2 | `Cohort Churn Rate` | `AVERAGE(CHURN_RATE)` | `1 - DIVIDE(SUM(ACTIVE_CUSTOMERS), SUM(COHORT_SIZE))` | Same fix; complement of weighted retention |
| A3 | `P1 Retention Rate` | `AVERAGE(RETENTION_RATE)` filtered to P1 | `DIVIDE(SUM(ACTIVE_CUSTOMERS), SUM(COHORT_SIZE))` filtered to P1 | Weighted period-1 retention |
| A4 | `P3 Retention Rate` | same as P1 pattern | same fix | — |
| A5 | `P6 Retention Rate` | same as P1 pattern | same fix | — |
| A6 | `Avg P1-P6 Drop` | `formatString: 0` | `formatString: 0.0%;-0.0%;0.0%` | Was rendering percentage delta as `0` |
| A7 | `TS Revenue MoM %` | `SUM(REVENUE_GROWTH_MOM_PCT)` | Recomputed via `DATEADD -1 MONTH` over `[Daily Revenue]` | Summing percentages is meaningless |
| A8 | `TS Revenue YoY %` | `SUM(REVENUE_GROWTH_YOY_PCT)` | Recomputed via `SAMEPERIODLASTYEAR` over `[Daily Revenue]` | Same |
| A9 | `Cumulative Revenue` | `ALL(DIM_DATES)` | `ALLSELECTED(DIM_DATES[DATE])` | Ignored user's date slicer |
| A10 | `Cumulative Orders` | `ALL(DIM_DATES)` | `ALLSELECTED(DIM_DATES[DATE])` | Same |
| A11 | `WTD Revenue` | Custom WEEKDAY math over `MAX(DATE)` | `SUM(FCT_DAILY_REVENUE_TIME_SERIES[WTD_REVENUE])` | Trust the pre-computed column from dbt; correct under any slice |
| A12 | `Revenue WoW %` | DATEADD -7 days of broken WTD measure | `AVERAGE(REVENUE_GROWTH_WOW_PCT)` | Inherits dbt-side definition |

**Verification you must do:** open Cohort Retention page after refresh; the retention matrix numbers will *change* (correctly). Cross-check `Avg Retention Rate` against a hand calc in Snowflake: `SELECT SUM(ACTIVE_CUSTOMERS)::FLOAT / SUM(COHORT_SIZE) FROM MARTS.FCT_COHORT_RETENTION`.

---

## B. Performance refactors (numbers unchanged)

| # | Measure | Was | Now | Why |
|---|---|---|---|---|
| B1 | `Delivery Rate` | `COUNTROWS(FILTER(...))` | `CALCULATE([Total Orders], FCT_ORDERS[ORDER_STATUS] = "delivered")` | FILTER is row-iterator (formula engine); CALCULATE predicate stays in storage engine |
| B2 | `On-Time Delivery Rate` | `COUNTROWS(FILTER(...))` for num and denom | `CALCULATE([Total Orders], ...)` in both | Same |
| B3 | `Single Purchaser Count` | `SUMMARIZE` with extension columns inside `FILTER` inside `CALCULATE` | `ADDCOLUMNS(SUMMARIZE(keys only), "@Orders", CALCULATE(...))` then FILTER | Modern pattern; smaller intermediate tables |
| B4 | `Repeat Purchaser Count` | Same anti-pattern | Same fix | Same |
| B5 | `Latest Cohort Size` | `FILTER(ALL(...), col = MAX(col))` | `VAR _LatestCohort = CALCULATE(MAX(...), ALLSELECTED(...))` + `KEEPFILTERS` | One scan up-front, then cheap filter |

---

## C. Filter-context corrections (numbers may change in edge cases)

| # | Measure | Was | Now | Why |
|---|---|---|---|---|
| C1 | `RFM Segment Revenue %` | `ALL(RFM_SEGMENT)` denominator | `ALLSELECTED(RFM_SEGMENT)` | Respects any outer segment filters |
| C2 | `Revenue % of Total` (Geo) | `ALL(STATE)` | `ALLSELECTED(STATE)` | Respects outer Year/Quarter slicer |
| C3 | `State Revenue Rank` | `RANKX(ALL(STATE), ...)` | `RANKX(ALLSELECTED(STATE), ...)` | Same |
| C4 | `Category Revenue %` | `ALL(PRODUCT_CATEGORY)` | `ALLSELECTED(PRODUCT_CATEGORY)` | Same |
| C5 | `Churn Status %` | `ALL(CHURN_STATUS)` | `ALLSELECTED(CHURN_STATUS)` | Same |

The "ALL vs ALLSELECTED" choice is contextual. If the visual is meant to show "share of the entire grand total ignoring any slicer", keep `ALL`. If it's meant to show "share of what the user is currently looking at", use `ALLSELECTED`. The latter is the more common dashboard intent.

---

## D. Format & display-folder polish (no functional change)

| # | Measure | Change |
|---|---|---|
| D1 | `Customers MoM %` | Added `formatString: 0.0%;-0.0%;0.0%`, `displayFolder: _Time Intelligence` |
| D2 | `Prior Month Customers` | Format string `#,##0`, folder `_Time Intelligence` |
| D3 | `Cumulative Revenue` | Format `$#,##0`, folder `_Time Intelligence` |
| D4 | `Cumulative Orders` | Format `#,##0`, folder `_Time Intelligence` |
| D5 | `WTD Revenue` | Format `$#,##0`, folder `_Time Intelligence` |
| D6 | `Revenue WoW %` | Format percentage, folder `_Time Intelligence` |
| D7 | `RFM Segment Revenue %` | Format `0.0%`, folder `_Segments\RFM` |
| D8 | `High/Medium CLV Revenue %` | Format `0.0%`, folder `_Segments\CLV` |
| D9 | `Active Rate / Churn Status % / Revenue at Risk %` | Format `0.0%`, folder `_Segments\Churn` |
| D10 | `Delivered to Reviewed % / Funnel Drop-off Rate` | Format `0.0%`, folder `_Funnel` |
| D11 | `Category Revenue %` | Format `0.0%`, folder `_Product` |
| D12 | `Potential Loyalists / New Customers Count` | Format `#,##0`, folder `_Segments\RFM` |
| D13 | All "Color/Arrow/Format" measures | Added `displayFolder: _Viz Helpers` so they don't pollute the top-level measure list |

---

## E. New measures added

| # | Measure | Purpose |
|---|---|---|
| E1 | `Last Refresh` | Stamps `NOW()` as text — pin to report header for data-freshness signal |
| E2 | `Revenue by Delivery Date` | Activates the inactive `FCT_ORDERS[DELIVERY_DATE_KEY]` relationship via `USERELATIONSHIP`. Demonstrates role-playing date pattern |
| E3 | `Orders by Delivery Date` | Same pattern for order count |

`Revenue by Delivery Date` is the FAANG-interview-friendly demonstration that you understand role-playing dimensions. Pair it with `Total Revenue` on a chart — same x-axis, different relationship — and you've earned the "knows DAX" badge.

---

## F. Model-file edits (TMDL outside _Measures.tmdl)

| # | File | Change |
|---|---|---|
| F1 | `DIM_DATES.tmdl` | Header comment instructing reviewer to mark as Date Table. All categorical-numeric columns (YEAR, MONTH, QUARTER_NUMBER, DAY, WEEK, ISO_DAY_OF_WEEK, DAY_OF_WEEK, *_OFFSET) switched from `summarizeBy: sum` to `summarizeBy: none` to prevent nonsense auto-aggregation |
| F2 | `FCT_DAILY_REVENUE_TIME_SERIES.tmdl` | YEAR, QUARTER_NUMBER, MONTH switched from `summarizeBy: sum` to `none` |

---

## G. NOT auto-applied (require Power BI Desktop)

These are listed in `POWERBI_REVIEW.md §6` but worth repeating here:

- Mark `DIM_DATES` as Date Table
- Remove bidirectional flags on 6 relationships
- Rename `AutoDetected_*` relationships
- Add `dataCategory` to geo columns
- Configure sync slicers
- Add drillthrough pages, tooltip pages, bookmarks
- Switch date slicer to *Between* style with `DIM_DATES[DATE]`

---

## H. Test checklist after refresh

1. Open Power BI Desktop, click **Refresh**. The model should load without errors.
2. Navigate to **Cohort Retention** page — retention numbers will have changed (correctly).
3. Spot-check `Avg Retention Rate` vs Snowflake hand-calc.
4. Apply a date-range filter on **Executive Summary**; navigate to **Time Trends** — cumulative numbers should now respect the filter.
5. Check `WTD Revenue` and `Revenue WoW %` on **Time Trends** — values should match the equivalent `WTD_REVENUE` / `REVENUE_GROWTH_WOW_PCT` columns when you put them on a card directly.
6. Run **Performance Analyzer** on the cohort matrix before/after — `Avg Retention Rate` should be faster (SE-only) than the previous AVERAGE.
7. Run DAX Studio's **View Metrics** — confirm no measures returned errors.

If anything breaks, every change is in the `_Measures.tmdl` file at the same `lineageTag`; revert from git.
