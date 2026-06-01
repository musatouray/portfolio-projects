# Power BI Review — E-Commerce Analytics

**Reviewer perspective:** Senior analytics engineer review of `Ecommerce Analytics.pbip` as a FAANG-grade portfolio asset. Findings are prioritized by *severity × visibility-to-interviewer*. Drive-by nits are skipped.

**Legend**
- `[BUG]` produces incorrect numbers
- `[PERF]` produces correct numbers but burns CPU/memory
- `[MODEL]` Vertipaq / star-schema hygiene
- `[UX]` report design / storytelling
- `[POLISH]` cosmetic; matters for a portfolio piece

A companion file, `POWERBI_REVIEW_REFACTORS.md`, lists every measure that was rewritten in place.

---

## 1. Critical correctness bugs

### 1.1 `Avg Retention Rate` / `Cohort Churn Rate` — averaging averages `[BUG]`

```dax
Avg Retention Rate = AVERAGE(FCT_COHORT_RETENTION[RETENTION_RATE])
Cohort Churn Rate  = AVERAGE(FCT_COHORT_RETENTION[CHURN_RATE])
```

`RETENTION_RATE` is already a *ratio* per (cohort, period). Averaging unweighted ratios gives a different number than the true blended rate. A cohort of 5 with 100% retention and a cohort of 5000 with 10% retention should not produce 55%.

**Fix:** weight by cohort size — this is the standard cohort-analysis pattern.

```dax
Avg Retention Rate =
DIVIDE(
    SUM(FCT_COHORT_RETENTION[ACTIVE_CUSTOMERS]),
    SUM(FCT_COHORT_RETENTION[COHORT_SIZE])
)
```

Applied in TMDL.

### 1.2 `P1 / P3 / P6 Retention Rate` — same problem `[BUG]`

`AVERAGE(...)` filtered to `PERIOD_NUMBER = 1` is wrong for the same reason. When the user slices by year or month, you want the *blended* P1 rate, not the unweighted average of per-cohort rates.

**Fix:**
```dax
P1 Retention Rate =
CALCULATE(
    DIVIDE(SUM(FCT_COHORT_RETENTION[ACTIVE_CUSTOMERS]), SUM(FCT_COHORT_RETENTION[COHORT_SIZE])),
    FCT_COHORT_RETENTION[PERIOD_NUMBER] = 1
)
```

Applied in TMDL (P1, P3, P6).

### 1.3 `TS Revenue MoM %` / `TS Revenue YoY %` — SUM of percentages `[BUG]`

```dax
TS Revenue MoM % = SUM(FCT_DAILY_REVENUE_TIME_SERIES[REVENUE_GROWTH_MOM_PCT])
```

`REVENUE_GROWTH_MOM_PCT` is a daily ratio. `SUM` over a month produces a value with no meaningful interpretation (e.g. 30 days × ~5% each = 150%). This will mislead any stakeholder who reads it.

**Fix:** these percentage columns should be recomputed in DAX from the underlying revenue, not summed. The simplest senior-grade replacement is to drop them and rely on `Revenue MoM %` / `Revenue YoY %` which already do this correctly via DAX time intelligence. Applied: rewrote both measures to recompute from `Daily Revenue` and prior periods.

### 1.4 `Cumulative Revenue` / `Cumulative Orders` — ignores user's date slicer `[BUG]`

```dax
Cumulative Revenue =
CALCULATE(
    [Total Revenue],
    FILTER(ALL(DIM_DATES), DIM_DATES[DATE] <= MAX(DIM_DATES[DATE]))
)
```

`ALL(DIM_DATES)` strips every filter on the date table — including the user's date slicer. If they filter to 2017 you still get cumulative from the dawn of the dataset.

**Fix:** use `ALLSELECTED(DIM_DATES[DATE])` to respect outer filters but not the inner row's date cell.

```dax
Cumulative Revenue =
CALCULATE(
    [Total Revenue],
    FILTER(ALLSELECTED(DIM_DATES[DATE]), DIM_DATES[DATE] <= MAX(DIM_DATES[DATE]))
)
```

Applied to both cumulative measures.

### 1.5 `Avg P1-P6 Drop` — wrong format string `[BUG]`

```
formatString: 0
```

This is the difference between two percentages, but Power BI is told to render it as an integer. Means `-0.15` displays as `0`.

**Fix:** `formatString: 0.0%;-0.0%;0.0%`. Applied.

### 1.6 `WTD Revenue` / `Revenue WoW %` `[BUG, latent]`

```dax
WTD Revenue =
VAR CurrentDate = MAX(DIM_DATES[DATE])
VAR WeekStart   = CurrentDate - WEEKDAY(CurrentDate, 2) + 1
RETURN CALCULATE([Total Revenue], DIM_DATES[DATE] >= WeekStart && DIM_DATES[DATE] <= CurrentDate)
```

This *only* gives the right answer when the filter context contains a single day. Inside a matrix that already slices by day or week (which is exactly where this measure is used), the inner `MAX` evaluates per cell and the predicate flexes. There is a perfectly good pre-computed `WTD_REVENUE` column on `FCT_DAILY_REVENUE_TIME_SERIES` that you can `SUM` over the slice; that is the dbt-side-pushdown approach and is what a senior would pick.

**Refactor applied:** `WTD Revenue = SUM(FCT_DAILY_REVENUE_TIME_SERIES[WTD_REVENUE])`. Same for `WoW` — derive from the pre-computed daily columns.

---

## 2. Performance hotspots

### 2.1 `COUNTROWS(FILTER(...))` anti-pattern `[PERF]`

```dax
Delivery Rate =
DIVIDE(
    COUNTROWS(FILTER(FCT_ORDERS, FCT_ORDERS[ORDER_STATUS] = "delivered")),
    [Total Orders]
)
```

`FILTER` is a row context iterator — the formula engine evaluates the predicate row-by-row, blocking the storage engine from doing the cheap scan. Replace with a `CALCULATE` predicate so VertiPaq runs a plain filter.

**Fix (applied):**
```dax
Delivery Rate =
DIVIDE(
    CALCULATE([Total Orders], FCT_ORDERS[ORDER_STATUS] = "delivered"),
    [Total Orders]
)
```

Same pattern applied to `On-Time Delivery Rate`.

Trade-off note: on a ~100k-row table the difference is invisible; on a 50M-row fact this is the difference between sub-second and "user closes the tab". Both interviewers and DAX Studio reviewers always check for this.

### 2.2 `Single Purchaser Count` / `Repeat Purchaser Count` `[PERF]`

```dax
CALCULATE(
    DISTINCTCOUNT(DIM_CUSTOMERS[CUSTOMER_UNIQUE_ID]),
    FILTER(
        SUMMARIZE(FCT_ORDERS, DIM_CUSTOMERS[CUSTOMER_UNIQUE_ID], "Orders", COUNTROWS(FCT_ORDERS)),
        [Orders] = 1
    )
)
```

This materializes a per-customer order count table on every evaluation. On the Olist dataset (~99k customers) it's cheap, but the pattern is wrong. Two problems:
1. `SUMMARIZE` with extension columns is the discouraged form — use `ADDCOLUMNS` + `SUMMARIZE` keys-only, or `GROUPBY`.
2. Better still, materialize this in the dbt mart so DAX only does `SUM`.

**Senior call:** I left these in place but rewrote them with the modern pattern (`CALCULATE` + `KEEPFILTERS` + `FILTER` over a `SUMMARIZECOLUMNS`/`GROUPBY` projection). The cleanest portfolio answer is a new `fct_customer_purchase_behavior` mart with `is_single_purchaser` flag. Captured as a recommendation in §6.

### 2.3 `Latest Cohort Size` — heavy iterator `[PERF]`

```dax
FILTER(ALL(FCT_COHORT_RETENTION[COHORT_KEY]),
       FCT_COHORT_RETENTION[COHORT_KEY] = MAX(FCT_COHORT_RETENTION[COHORT_KEY]))
```

Replace with `CALCULATE(... , LASTNONBLANKVALUE(...))` pattern or compute via TOPN over `ALL`. Applied: simplified using `KEEPFILTERS` + `MAX` reference.

### 2.4 Bidirectional cross-filtering `[PERF, MODEL]`

Six relationships have `crossFilteringBehavior: bothDirections` with `fromCardinality: one`:

- `FCT_CHURN_RISK[CUSTOMER_UNIQUE_ID] → DIM_CUSTOMERS` (inactive, still bidi)
- `FCT_CLV_CUSTOMER[CUSTOMER_UNIQUE_ID] → DIM_CUSTOMERS` (inactive)
- `FCT_RFM_SEGMENTS[CUSTOMER_UNIQUE_ID] → DIM_CUSTOMERS`
- `FCT_DAILY_REVENUE_TIME_SERIES[DATE_KEY] → DIM_DATES`
- `FCT_PARETO_PRODUCTS[PRODUCT_KEY] → DIM_PRODUCTS`

Bi-di + one-to-many is **always** an anti-pattern (Marco Russo / Alberto Ferrari are emphatic about this). It creates ambiguity, drags query performance, and obscures filter direction in the model. Use single-direction relationships with `CROSSFILTER()` inside specific measures when reverse propagation is genuinely needed. **Not auto-applied** — changing relationship cardinality can silently change visuals. Listed as required pre-publish work in §6.

---

## 3. Semantic model hygiene

### 3.1 `DIM_DATES` not marked as a Date Table `[MODEL — important]`

`DIM_DATES` is the only date table in the model but it is missing the `dataCategory: Time` marker (or the equivalent "Mark as date table" in PBI Desktop). Without this, time-intelligence functions (`DATESYTD`, `SAMEPERIODLASTYEAR`, `DATEADD`) fall back to the engine's auto date table heuristics, which produce subtly wrong results when the date column has gaps or duplicates.

**Action (manual):** in Power BI Desktop, right-click `DIM_DATES` → *Mark as Date Table* → pick `DATE`. This cannot be reliably done from TMDL without risking schema breakage.

### 3.2 Wrong `summarizeBy` `[MODEL]`

| Column | Current | Should be |
|---|---|---|
| `DIM_DATES[YEAR/MONTH/QUARTER_NUMBER/DAY/WEEK/...]` | `sum` | `none` |
| `DIM_DATES[*_OFFSET]` | `sum` | `none` |
| `DIM_CUSTOMERS[AVERAGE_ORDER_VALUE]` | `sum` | `none` (or `average`) |
| `DIM_CUSTOMERS[AVERAGE_RATING]` | `sum` | `none` |
| `DIM_CUSTOMERS[DAYS_SINCE_LAST_ORDER]` | `sum` | `none` |
| `FCT_RFM_SEGMENTS[R_SCORE/F_SCORE/M_SCORE]` | `sum` | `none` |
| `FCT_CLV_CUSTOMER[CLV_SCORE / CLV_DECILE / AVERAGE_ORDER_VALUE]` | `sum` | `none` |
| `FCT_DAILY_REVENUE_TIME_SERIES[YEAR/MONTH/...]` | `sum` | `none` |
| `FCT_DAILY_REVENUE_TIME_SERIES[*_PCT, *_GROWTH_*_PCT]` | `sum` | `none` |
| `FCT_DAILY_REVENUE_TIME_SERIES[ROLLING_AVG_*]` | `sum` | `none` |
| `FCT_ORDERS_FUNNEL[*_PCT, *_RATE, AVG_*]` | `sum` | `none` |

Symptoms: end users drag `YEAR` into a card and get `SUM(YEAR)`. Auto-aggregating ratios with `SUM` is also how 1.3 happens. Applied in TMDL.

### 3.3 Aggregates in dimensions `[MODEL]`

`DIM_CUSTOMERS` has `TOTAL_ORDERS`, `TOTAL_REVENUE`, `AVERAGE_ORDER_VALUE`, `TOTAL_REVIEWS`, `AVERAGE_RATING`, `DAYS_SINCE_LAST_ORDER`, `CUSTOMER_TENURE_DAYS`. These are facts about a customer, not attributes — they violate strict Kimball. They duplicate information already in `FCT_ORDERS`, `FCT_RFM_SEGMENTS`, `FCT_CHURN_RISK`. Two consequences:
1. Vertipaq stores them twice.
2. Two paths to the same number → measures can disagree depending on which table they came from (you already have `At Risk Count` from RFM and `At Risk Customers` from Churn — different counts).

**Recommendation:** hide these columns (`isHidden: true`) so the only access is through `_Measures`. Applied for the worst offenders.

### 3.4 Surrogate-key data types `[MODEL, minor]`

- `DATE_KEY` is `double` (it's `YYYYMMDD` so `int64` would compress better)
- `CUSTOMER_KEY` is `string` while `ORDER_DATE_KEY` is `double` — inconsistent

Vertipaq stores ints with run-length encoding far more cheaply than strings. With ~99k customers it doesn't matter; at 50M it does. **Not auto-applied** — column type changes require Power Query refresh and can break partitions.

### 3.5 SCD metadata exposed `[POLISH, but visible to interviewers]`

Every fact and dimension exposes `CREATED_AT` / `UPDATED_AT`. These belong to the ETL framework, not to consumers. Hide with `isHidden: true`. Applied.

### 3.6 Geography columns missing `dataCategory` `[UX]`

`DIM_CUSTOMERS[STATE]`, `DIM_SELLERS[STATE]`, `FCT_GEO_PERFORMANCE[STATE]` need `dataCategory: 'State or Province'`; `CITY` needs `'City'`; `ZIP_CODE` needs `'PostalCode'`. Without these, Power BI's map visuals geocode them as generic strings and you get Brazilian states plotted in random places. **Not auto-applied** — requires Power Query column-level metadata that's safer to set in PBI Desktop.

### 3.7 Inactive relationships are dead weight `[MODEL]`

`FCT_ORDERS[DELIVERY_DATE_KEY] → DIM_DATES[DATE_KEY]` is inactive — fine, role-playing-dimension pattern. But no measure activates it with `USERELATIONSHIP`. Either drop it or add measures like `Revenue by Delivery Date = CALCULATE([Total Revenue], USERELATIONSHIP(FCT_ORDERS[DELIVERY_DATE_KEY], DIM_DATES[DATE_KEY]))`. The latter is a quick FAANG-resume win (shows you understand role-playing dimensions). Added two example measures in the refactor.

Same for `FCT_ORDER_ITEMS[ORDER_ID] → FCT_ORDERS[ORDER_ID]` (inactive) — you have separate date relationships for both so this fact-to-fact relationship isn't really needed.

### 3.8 Auto-detected relationship names `[POLISH]`

All 19 relationships are named `AutoDetected_<guid>`. Rename them to something readable like `FCT_ORDERS_ORDER_DATE` so the diagram view tells a story. **Not auto-applied** — purely cosmetic but takes 2 minutes in Desktop.

---

## 4. Report design (the part interviewers actually click on)

### 4.1 Date slicer uses a string column `[BUG/UX]`

`Executive_Summary/visuals/date_slicer` uses `DIM_DATES[MONTH_YEAR]` (a string). This forces the slicer into "dropdown of categories" mode. The point of a date slicer is the *between-date* slider. Swap to `DIM_DATES[DATE]` and set the slicer style to *Between* — gives the user a draggable calendar range. Captured as recommendation, not auto-applied.

### 4.2 No sync slicers `[UX]`

`Date Range` lives on the Executive Summary; the user has to re-filter on every page. Configure **Sync slicers** so Date and any cross-cutting filter (Customer Segment, State) follow the user. Sync state is in `report.json` — set after rebuilding in Desktop, hard to do safely by hand.

### 4.3 Page-level inconsistency `[POLISH]`

- Executive Summary page name: `9ebae341b465b91b82ff` (auto-GUID)
- Every other page: `rfm_segmentation_page`, `clv_page`, ...

Rename the Executive Summary internal name to `executive_summary_page` for consistency. Not auto-applied because pages are referenced by name from bookmarks/buttons if any exist.

### 4.4 KPI cards have unused filter configs `[POLISH]`

Every KPI card has `filterConfig.filters` containing the same measure as an Advanced filter type. Power BI generates these by default but they have no effect and inflate file size. Clean up when republishing.

### 4.5 No drillthrough, no bookmarks, no tooltip pages `[UX — high portfolio impact]`

Three high-leverage additions for a portfolio piece — none currently present:

1. **Drillthrough pages** — Right-click a state on the map → drill to a State Deep-Dive page filtered to that state. The mechanic is `drillthroughFilter` on a page + a target field. Trivial to add and impressive in a demo.
2. **Tooltip page** — A small page (320×240) with a mini cohort retention curve appearing on hover of the cohort table. The interviewer's eyes light up the moment they hover.
3. **Bookmarks + buttons** — Define 2-3 scenarios ("Last 90 days", "Top 5 states", "Reset"), wire them to a navigation pane. Demonstrates you can build a narrative, not just dashboards.

Sketch of recommended page graph:

```
Executive Summary  ───────►  RFM ───►  Customer Detail (drillthrough)
                     │
                     ├──►  Cohort Retention  ───►  Cohort Detail (drillthrough)
                     ├──►  Churn Risk
                     ├──►  CLV
                     ├──►  Funnel Analysis
                     ├──►  Geographic ───►  State Detail (drillthrough)
                     ├──►  Product Performance ───►  Category Detail
                     ├──►  Market Basket
                     └──►  Time Trends
```

### 4.6 Layout polish `[POLISH]`

Executive Summary positions look mostly clean (KPIs at top, trend below). A few things to consider on republish:
- All visuals have `z: 0` — set explicit z-order where overlaps exist
- Add a hidden page navigator visual or a custom-shape navigation panel so users don't rely on the page tabs
- Add accessibility: alt text, tab order, screen-reader-friendly labels (these are zero-cost portfolio points)

### 4.7 RFM scatter clarity `[UX]`

`RFM_Segmentation/visuals/rfm_scatter` plots `Avg Frequency` (X) vs `Avg Monetary` (Y), bubble = `RFM Total Customers`, color = `RFM_SEGMENT`. With ~10 segments you get 10 bubbles — sparse. A more interview-impressive variant: plot **customer-level R vs F-M score**, color by segment. That requires `FCT_RFM_SEGMENTS[CUSTOMER_UNIQUE_ID]` as the implicit detail level, which the current model supports.

### 4.8 Theme `[POLISH]`

Custom theme `E-Commerce Analytics.json` already present and applied — good. Make sure it sets categorical colors that don't clash (the segment colors in the DAX measures `RFM Segment Color`, `CLV Segment Color` are a separate hard-coded palette — keep them aligned with the theme).

---

## 5. Measures that should be merged or renamed

| Current | Issue | Recommendation |
|---|---|---|
| `At Risk Count` (from `FCT_RFM_SEGMENTS`) vs `At Risk Customers` (from `FCT_CHURN_RISK`) | Same name pattern, different counts | Rename to `At Risk Count (RFM)` and `At Risk Count (Churn)` |
| `Delivery Rate` (from `FCT_ORDERS`) vs `Geo Delivery Rate` vs `Overall Delivery Rate` (funnel) | Three "delivery rate" measures | Rename to `Delivery Rate (Orders)`, `Delivery Rate (Geo)`, `Delivery Rate (Funnel)` |
| `RFM Total Customers` | Just `COUNTROWS(FCT_RFM_SEGMENTS)` | Either rename to `RFM Customers` or drop — `Total Customers` from `DIM_CUSTOMERS` covers it |
| `Cancellation Rate` | From funnel aggregate | Document that it's average-of-monthly-rates, not blended |

Renames are not auto-applied because they will break any visual binding (every `visual.json` references measures by name).

---

## 6. Pre-publish checklist (not auto-applied — needs Desktop)

These changes are too risky to do via raw TMDL edits but should be done before showing this to a recruiter:

1. **Mark `DIM_DATES` as Date Table.**
2. **Strip bidirectional flags** from the 6 relationships listed in §2.4. Re-test visuals that depend on `RFM_SEGMENT` slicing customer-level facts (`CROSSFILTER` inside the affected measures if anything breaks).
3. **Rename auto-detected relationships** in the model diagram.
4. **Add `dataCategory`** to STATE/CITY/ZIP columns for geo visuals.
5. **Configure sync slicers** so Date filter follows the user across pages.
6. **Convert date slicer to Between style** using `DIM_DATES[DATE]`.
7. **Switch surrogate keys to int64** in Power Query for `DATE_KEY`. Optional but classy.
8. **Activate role-playing date dimension** — see `Revenue by Delivery Date` example measure added.
9. **Add drillthrough pages + tooltip page + bookmarks** (see §4.5 layout).
10. **Add a `LastRefresh` measure** so the report stamps its data freshness — interviewer reflex check.

---

## 7. Senior-grade additions to consider (next iteration)

Things that move this from "good portfolio" to "they're going to remember this one":

- **Calculation groups** for time intelligence — instead of `YTD Revenue`, `YTD Orders`, `YTD Customers`, define one Time Intelligence calc group with members `Current`, `YTD`, `MTD`, `Prior Year`, `YoY %`. Reduces 40 measures to 1 group + the base measures. **The single biggest "this person knows DAX" signal.**
- **Field parameters** for the executive page — let the user toggle the trend line between Revenue / Orders / AOV / Customers with one click.
- **Tabular Editor 3 best-practice analyzer** report attached to the repo, proving you've run static analysis on the model.
- **CI on the semantic model** — Tabular Editor's CLI can validate TMDL on every PR; a GitHub Action that runs `TabularEditor.exe Model.bim -A BPA.json -F` is a perfect pairing with your existing dbt CI/CD story.
- **External tools metadata** — wire DAX Studio + Tabular Editor into the project, mention in the README. Free signaling that you live in the senior toolchain.
- **Aggregation tables** if the dataset grows — Olist is small, but pretending it's not by adding a `agg_daily_revenue_by_state` aggregation table over the order-line grain shows you understand large-model patterns.

---

## 8. What `POWERBI_REVIEW_REFACTORS.md` lists

Every DAX measure rewritten in-place, with before/after. That file is your evidence trail when an interviewer asks "walk me through what you changed and why."
