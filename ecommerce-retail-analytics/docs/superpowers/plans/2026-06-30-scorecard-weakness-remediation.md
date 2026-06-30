# Scorecard Weakness Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 18 weaknesses identified in the project scorecard review across security, dbt correctness, dbt configuration, Airflow hardening, infrastructure, and CI/CD.

**Architecture:** Fixes are grouped into six independent workstreams that can be executed in parallel except where noted. Security fixes (Task 1) should be done first as they are blockers. All dbt changes follow the existing project conventions in `.claude/references/`.

**Tech Stack:** dbt 1.11.8, Snowflake, Apache Airflow 2.9.3, Docker Compose, GitHub Actions, Power BI TMDL

**Save plan to:** `ecommerce-retail-analytics/docs/superpowers/plans/2026-06-30-scorecard-weakness-remediation.md`

---

## Files Modified

| File | Change |
|------|--------|
| `airflow/docker-compose.yml` | Add Fernet key env var, fix timezone to UTC, add resource limits |
| `airflow/dags/daily_synthetic_orders.py` | Add try-except, add `max_active_runs=1`, fix cleanup trigger_rule |
| `airflow/dags/backfill_synthetic_orders.py` | Fix idempotency: check all 4 files, not just orders |
| `dbt/dbt_project.yml` | Add `customer_valid_statuses` var, add `dim_dates_end_year` var |
| `dbt/models/staging/_sources.yml` | Add freshness blocks to all 6 source tables |
| `dbt/models/marts/core/dim_dates.sql` | Replace hardcoded 2028 end date with dynamic expression |
| `dbt/models/marts/customer/fct_clv_customer.sql` | Fix CLV formula: use `clv_prediction_horizon_days` var, add GREATEST guard |
| `dbt/seeds/rfm_segment_definitions.csv` | Reconcile 8-segment seed with 5-segment model output |
| `dbt/models/marts/customer/_customer_models.yml` | Add CLV test for predicted_clv_12m >= 0 |
| `report/.../relationships.tmdl` | Change FCT_CLV_CUSTOMER→DIM_CUSTOMERS to single direction |
| `.github/workflows/dbt-ci.yml` | Remove `\|\| true` from SQLFluff, add pip cache |
| `.github/workflows/dbt-cd.yml` | Add pip cache, add Slack notification step |
| `snowflake/4-grant-access-config.sql` | Remove TRUNCATE/DELETE from RAW schema grants |
| `snowflake/7-resource-monitor.sql` | New file: create resource monitor with monthly credit cap |

---

## Task 1: Fix Security — Fernet Key and Timezone

**Priority: Do this before anything else.**

The empty Fernet key means Airflow stores all connection secrets (Snowflake credentials, AWS keys) unencrypted in PostgreSQL. The timezone mismatch between containers (`America/New_York`) and DAG schedule comments (`UTC`) creates confusion.

**Files:**
- Modify: `airflow/docker-compose.yml`

- [ ] **Step 1: Generate a Fernet key**

Run this in your terminal (not inside Airflow):
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Copy the output — it looks like `abc123XYZ...=` (43 chars ending in `=`).

- [ ] **Step 2: Add the key and fix the timezone in docker-compose.yml**

In `airflow/docker-compose.yml`, replace lines 10–17 in the `x-airflow-common` environment block:

```yaml
    AIRFLOW__CORE__FERNET_KEY: '${AIRFLOW_FERNET_KEY}'
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__CORE__DEFAULT_TIMEZONE: 'UTC'
    AIRFLOW__WEBSERVER__DEFAULT_UI_TIMEZONE: 'UTC'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: 'true'
    TZ: 'UTC'
```

- [ ] **Step 3: Add AIRFLOW_FERNET_KEY to .env**

Open `.env` and add:
```
AIRFLOW_FERNET_KEY=<paste the key you generated in Step 1>
```

- [ ] **Step 4: Add resource limits to the airflow-scheduler and airflow-webserver services**

In `docker-compose.yml`, add a `deploy` block under both the `airflow-webserver` and `airflow-scheduler` services (after their `ports:` or `healthcheck:` blocks):

```yaml
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 3G
```

Add a smaller limit block under `postgres`:
```yaml
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

- [ ] **Step 5: Verify the containers start cleanly**

```bash
cd airflow
docker compose down && docker compose up -d
docker compose logs airflow-scheduler 2>&1 | head -30
```
Expected: No `InvalidFernetToken` or permission errors in the first 30 log lines.

- [ ] **Step 6: Commit**

```bash
git add airflow/docker-compose.yml .env.example
git commit -m "fix(airflow): set Fernet key, fix timezone to UTC, add resource limits"
```

---

## Task 2: Fix dbt Source Freshness

Without freshness checks, stale RAW data (e.g., Airflow failing silently for 48 hours) is invisible. dbt source tests won't catch it — only `dbt source freshness` will.

**Files:**
- Modify: `dbt/models/staging/_sources.yml`

**Tables that receive freshness checks (loaded daily by Airflow):**
- `orders`
- `order_items`
- `order_payments`
- `order_reviews`

**Tables that do NOT get freshness checks (static reference data, not loaded daily):**
- `customers` — one-time historical load only
- `geolocation` — static reference data
- `sellers`, `products`, `product_category_translation` — static reference data

- [ ] **Step 1: Add a freshness block to each of the 4 daily tables in `_sources.yml`**

Immediately after the `description:` line of each qualifying table, before `columns:`, add:

```yaml
        loaded_at_field: METADATA$START_SCAN_TIME
        freshness:
          warn_after: {count: 25, period: hour}
          error_after: {count: 49, period: hour}
```

`METADATA$START_SCAN_TIME` is a Snowflake pseudocolumn that reflects the COPY INTO load timestamp — the correct field when no explicit `loaded_at` column exists.

- [ ] **Step 2: Test the freshness check locally**

```bash
cd dbt
dbt source freshness
```
Expected output:
```
Found 4 sources with freshness checks...
ok  [25h warn, 49h error] raw.orders .......... [ok, freshness: Xh Xm Xs]
ok  [25h warn, 49h error] raw.order_items ..... [ok, freshness: Xh Xm Xs]
ok  [25h warn, 49h error] raw.order_payments .. [ok, freshness: Xh Xm Xs]
ok  [25h warn, 49h error] raw.order_reviews ... [ok, freshness: Xh Xm Xs]
```

- [ ] **Step 3: Commit**

```bash
git add dbt/models/staging/_sources.yml
git commit -m "feat(dbt): add source freshness checks to daily-loaded RAW tables"
```

---

## Task 3: Fix CLV Formula and Variable Usage

`dbt_project.yml` declares `clv_prediction_horizon_days: 365` and describes an exponential decay model. The actual SQL in `fct_clv_customer.sql` ignores this variable and uses a simple linear daily rate. A same-day customer (first order = today) returns `total_lifetime_revenue` as their 12-month CLV — a massive overestimate.

This task corrects the formula to use the variable and adds a GREATEST guard for the same-day edge case. Full exponential decay requires behavioral data not yet in the model — the honest fix is to make the linear projection explicit and defensible.

**Files:**
- Modify: `dbt/models/marts/customer/fct_clv_customer.sql` (lines 77–84)
- Modify: `dbt/models/marts/customer/_customer_models.yml`

- [ ] **Step 1: Replace the predicted_clv_12m block in fct_clv_customer.sql**

Replace lines 77–84:
```sql
        -- 12-Month Equity Projection Vector
        COALESCE(
            CASE
                WHEN DATEDIFF('DAY', cc.first_order_date, CURRENT_DATE()) = 0 THEN ca.total_lifetime_revenue
                ELSE (ca.total_lifetime_revenue / NULLIF(DATEDIFF('DAY', cc.first_order_date, CURRENT_DATE()), 0)) * 365
            END,
            0
        ) AS predicted_clv_12m,
```

With:
```sql
        -- Linear CLV projection over the configured horizon
        -- Uses daily revenue rate extrapolated to the prediction horizon.
        -- lifespan clamped to GREATEST(1, ...) to avoid division-by-zero and
        -- unrealistic same-day projections (a brand-new customer defaults to AOV).
        COALESCE(
            (ca.total_lifetime_revenue
                / NULLIF(GREATEST(1, DATEDIFF('DAY', cc.first_order_date, CURRENT_DATE())), 0))
            * {{ var('clv_prediction_horizon_days') }},
            0
        ) AS predicted_clv_12m,
```

- [ ] **Step 2: Add a data test to _customer_models.yml**

Find the `fct_clv_customer` block in `dbt/models/marts/customer/_customer_models.yml` and add under `data_tests:` at the model level (or create one if it doesn't exist):

```yaml
    data_tests:
      - dbt_utils.expression_is_true:
          expression: "predicted_clv_12m >= 0"
          name: fct_clv_customer_predicted_clv_non_negative
```

- [ ] **Step 3: Run and verify**

```bash
cd dbt
dbt run --select fct_clv_customer
dbt test --select fct_clv_customer
```
Expected: Run succeeds. Test `fct_clv_customer_predicted_clv_non_negative` passes.

- [ ] **Step 4: Commit**

```bash
git add dbt/models/marts/customer/fct_clv_customer.sql \
        dbt/models/marts/customer/_customer_models.yml
git commit -m "fix(dbt): use clv_prediction_horizon_days var, guard same-day edge case in fct_clv_customer"
```

---

## Task 4: Reconcile RFM Seed with Model Output

The seed `rfm_segment_definitions.csv` defines 8 segments. The model `fct_rfm_segments.sql` outputs 5. This means 3 seed rows (Cant Lose Them, Loyal, Need Attention) have no corresponding data, and any report joining to the seed for descriptions will show empty rows.

The correct fix is to align the seed with what the model actually produces.

**Files:**
- Modify: `dbt/seeds/rfm_segment_definitions.csv`

- [ ] **Step 1: Rewrite the seed to match the 5 model segments**

Replace the entire contents of `dbt/seeds/rfm_segment_definitions.csv` with:

```csv
rfm_segment,segment_description,recommended_action,priority
Champions,"Best customers — recent, frequent, and high spenders. R≥4 F≥4 M≥4.",Reward with loyalty programs and early product access,1
Loyalists,"Consistent buyers with good recency and frequency. R≥3 F≥3.",Upsell and cross-sell opportunities to increase monetary value,2
New Customers,"Recent first- or second-time buyers. R≥4 with ≤2 total orders.",Welcome series and onboarding to drive the second purchase,3
At Risk / Hibernating,"Low recency — haven't purchased in a long time. R=1.",Re-engagement campaigns or sunset from active lists,4
General Pool,"Mid-range customers who don't fit other segments.",Monitor and test different engagement strategies,5
```

- [ ] **Step 2: Run the seed and verify**

```bash
cd dbt
dbt seed --select rfm_segment_definitions
```
Expected: `OK created seed model dev.marts.rfm_segment_definitions (5 rows)`

- [ ] **Step 3: Verify no orphaned values exist in fct_rfm_segments**

Run this SQL in Snowflake:
```sql
SELECT DISTINCT rfm_segment
FROM ECOMMERCE_RETAIL_DB_DEV.MARTS.FCT_RFM_SEGMENTS
WHERE rfm_segment NOT IN (
    SELECT rfm_segment FROM ECOMMERCE_RETAIL_DB_DEV.MARTS.RFM_SEGMENT_DEFINITIONS
);
```
Expected: 0 rows returned.

- [ ] **Step 4: Commit**

```bash
git add dbt/seeds/rfm_segment_definitions.csv
git commit -m "fix(dbt): reconcile rfm_segment_definitions seed with 5-segment model output"
```

---

## Task 5: Future-Proof dim_dates End Date

`dim_dates.sql` hardcodes `end_date="cast('2028-12-31' as date)"`. In 2029, all date joins for new data will silently fail to match (NULL date keys). This adds a dbt variable that defaults to 10 years from today so it never needs manual updating.

**Files:**
- Modify: `dbt/dbt_project.yml`
- Modify: `dbt/models/marts/core/dim_dates.sql`

- [ ] **Step 1: Add the variable to dbt_project.yml**

In `dbt/dbt_project.yml`, add after the `market_basket_min_pair_count` line:

```yaml
  # dim_dates: number of years ahead of today to generate dates
  # Default 10 years ensures the table never expires without manual edits
  dim_dates_future_years: 10
```

- [ ] **Step 2: Update dim_dates.sql to use the variable**

In `dbt/models/marts/core/dim_dates.sql`, replace lines 4–9:

```sql
with generated_dates as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2028-12-31' as date)"
    ) }}
),
```

With:

```sql
with generated_dates as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="dateadd(year, " ~ var('dim_dates_future_years') ~ ", current_date())"
    ) }}
),
```

- [ ] **Step 3: Run and verify**

```bash
cd dbt
dbt run --select dim_dates
```

Then in Snowflake confirm the max date is at least 10 years out:
```sql
SELECT MAX(date) FROM ECOMMERCE_RETAIL_DB_DEV.MARTS.DIM_DATES;
-- Expected: 2036-xx-xx or later
```

- [ ] **Step 4: Commit**

```bash
git add dbt/dbt_project.yml dbt/models/marts/core/dim_dates.sql
git commit -m "fix(dbt): replace hardcoded 2028 end date in dim_dates with dynamic 10-year horizon"
```

---

## Task 6: Harden Airflow DAG — Error Handling, Idempotency, Concurrency

Three bugs in `daily_synthetic_orders.py` and `backfill_synthetic_orders.py`:
1. `generate_daily` and `upload_daily_to_s3` have no try-except — Snowflake connection failures crash silently with no structured log.
2. Cleanup only runs on `all_success`, leaving orphaned CSVs on disk when uploads fail.
3. Backfill idempotency check only looks at the `orders` file — if `order_items` failed on a previous run, the backfill skips the date entirely, leaving orphaned orders.

**Files:**
- Modify: `airflow/dags/daily_synthetic_orders.py`
- Modify: `airflow/dags/backfill_synthetic_orders.py`

- [ ] **Step 1: Add try-except to generate_daily in daily_synthetic_orders.py**

Replace the `generate_daily` function body (lines 48–83) with:

```python
def generate_daily(**context):
    """Generate synthetic data for the previous day."""
    import logging
    log = logging.getLogger(__name__)

    execution_date = context["execution_date"]
    target_date = execution_date.date()
    log.info(f"Generating synthetic data for {target_date}")

    try:
        generator = SyntheticDataGenerator(seed=CONFIG["seed"], config=CONFIG)
        generator.load_reference_data()
    except Exception as e:
        log.error(f"Failed to load reference data from Snowflake: {e}")
        raise

    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for table in ["orders", "order_items", "order_payments", "order_reviews"]:
        (LOCAL_DATA_DIR / table).mkdir(exist_ok=True)

    try:
        target_datetime = datetime.combine(target_date, datetime.min.time())
        data = generator.generate_all_for_date(target_datetime)
    except Exception as e:
        log.error(f"Data generation failed for {target_date}: {e}")
        raise

    date_str = target_date.strftime("%Y-%m-%d")
    files_generated = []

    for table_name, df in data.items():
        filename = f"{table_name}_{date_str}.csv"
        filepath = LOCAL_DATA_DIR / table_name / filename
        try:
            df.to_csv(filepath, index=False)
            files_generated.append(str(filepath))
            log.info(f"Generated {filepath}: {len(df)} rows")
        except OSError as e:
            log.error(f"Failed to write {filepath}: {e}")
            raise

    context["ti"].xcom_push(key="target_date", value=date_str)
    context["ti"].xcom_push(key="order_count", value=len(data["orders"]))
    return files_generated
```

- [ ] **Step 2: Fix the cleanup trigger_rule in daily_synthetic_orders.py**

Find the `cleanup` PythonOperator definition (near the bottom of the DAG definition block). Change `trigger_rule="all_success"` to `trigger_rule="all_done"`:

```python
    cleanup = PythonOperator(
        task_id="cleanup_local_files",
        python_callable=cleanup_daily_files,
        trigger_rule="all_done",  # Run on success OR failure to avoid orphaned CSVs
    )
```

- [ ] **Step 3: Add max_active_runs to the DAG definition**

Find the `with DAG(` block (around line 181) and add `max_active_runs=1`:

```python
with DAG(
    dag_id="daily_synthetic_orders",
    default_args=default_args,
    description="Generate and load daily synthetic order data",
    schedule_interval="0 11 * * *",
    start_date=datetime(2026, 6, 20),
    catchup=False,
    max_active_runs=1,   # Prevent concurrent runs writing to same S3 paths
    tags=["synthetic", "daily"],
) as dag:
```

- [ ] **Step 4: Fix backfill idempotency in backfill_synthetic_orders.py**

Find the idempotency check in the backfill function (around line 96–101). Replace:

```python
        # Check if files already exist (use orders as the indicator)
        orders_file = LOCAL_DATA_DIR / "orders" / f"orders_{date_str}.csv"
        if not force_regenerate and orders_file.exists() and orders_file.stat().st_size > 0:
            skipped_dates += 1
            current_date += timedelta(days=1)
            continue
```

With:

```python
        # Check ALL 4 table files exist and are non-empty before skipping
        # Checking only orders misses partial failures (e.g., order_items failed last run)
        all_tables = ["orders", "order_items", "order_payments", "order_reviews"]
        all_files_exist = all(
            (LOCAL_DATA_DIR / table / f"{table}_{date_str}.csv").exists()
            and (LOCAL_DATA_DIR / table / f"{table}_{date_str}.csv").stat().st_size > 0
            for table in all_tables
        )
        if not force_regenerate and all_files_exist:
            skipped_dates += 1
            current_date += timedelta(days=1)
            continue
```

- [ ] **Step 5: Verify the DAG parses without errors**

```bash
cd airflow
docker compose exec airflow-scheduler airflow dags list 2>&1 | grep daily_synthetic_orders
```
Expected: `daily_synthetic_orders  | ...  | True`

If you see an import error, check the Python syntax in the modified file.

- [ ] **Step 6: Commit**

```bash
git add airflow/dags/daily_synthetic_orders.py \
        airflow/dags/backfill_synthetic_orders.py
git commit -m "fix(airflow): add error handling, fix cleanup trigger_rule, add max_active_runs, fix backfill idempotency"
```

---

## Task 7: Snowflake Resource Monitor and Least-Privilege Grants

No credit cap exists on the warehouse. A runaway `dbt build` can consume unlimited credits. Additionally, the RAW schema grants include `TRUNCATE` and `DELETE`, violating the Bronze immutability principle.

**Files:**
- Create: `snowflake/7-resource-monitor.sql`
- Modify: `snowflake/4-grant-access-config.sql`

- [ ] **Step 1: Create the resource monitor script**

Create `snowflake/7-resource-monitor.sql` with the following content. Adjust `CREDIT_QUOTA` to match your actual monthly budget:

```sql
-- Resource monitor to cap monthly Snowflake credit usage
-- Run once as ACCOUNTADMIN after initial setup

USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE RESOURCE MONITOR ecommerce_monthly_budget
    CREDIT_QUOTA = 50                          -- Adjust to your monthly budget
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 75 PERCENT DO NOTIFY             -- Alert at 75% spend
        ON 90 PERCENT DO SUSPEND            -- Suspend new queries at 90%
        ON 100 PERCENT DO SUSPEND_IMMEDIATE; -- Hard stop at 100%

ALTER WAREHOUSE ECOMMERCE_RETAIL_WH
    SET RESOURCE_MONITOR = ecommerce_monthly_budget;

-- Confirm
SHOW RESOURCE MONITORS LIKE 'ecommerce_monthly_budget';
```

- [ ] **Step 2: Remove TRUNCATE and DELETE from RAW grants in 4-grant-access-config.sql**

Find the section granting privileges on RAW tables to `LEAD_DATA_ENGINEER_ROLE`. Replace any line containing `TRUNCATE` or `DELETE` in the RAW context.

The corrected RAW grants should be:
```sql
-- RAW schema: insert + select only (Bronze is immutable — no deletes)
GRANT SELECT, INSERT
    ON ALL TABLES IN SCHEMA ECOMMERCE_RETAIL_DB_DEV.RAW
    TO ROLE LEAD_DATA_ENGINEER_ROLE;

GRANT SELECT, INSERT
    ON FUTURE TABLES IN SCHEMA ECOMMERCE_RETAIL_DB_DEV.RAW
    TO ROLE LEAD_DATA_ENGINEER_ROLE;
```

Keep `SELECT, INSERT, UPDATE, DELETE, TRUNCATE` only for STAGING, INTERMEDIATE, and MARTS schemas where dbt needs to recreate tables.

- [ ] **Step 3: Run the resource monitor script in Snowflake**

Connect as `ACCOUNTADMIN` and execute:
```sql
-- In Snowflake worksheet or SnowSQL:
!source snowflake/7-resource-monitor.sql
```
Or paste the contents directly into a Snowflake worksheet and run.

Expected: `Statement executed successfully.` for each command.

- [ ] **Step 4: Commit**

```bash
git add snowflake/7-resource-monitor.sql snowflake/4-grant-access-config.sql
git commit -m "feat(snowflake): add resource monitor with monthly credit cap, remove TRUNCATE/DELETE from RAW grants"
```

---

## Task 8: Fix Power BI Semantic Model — Bi-Directional Relationship

The `FCT_CLV_CUSTOMER → DIM_CUSTOMERS` relationship is set to `bothDirections`. In a star schema this causes filter propagation back from the dimension into the fact table, which creates unexpected query results and prevents row-level security from working correctly. It should be single-direction.

**Files:**
- Modify: `report/Ecommerce Analytics.SemanticModel/definition/relationships.tmdl`

- [ ] **Step 1: Open the relationships file and find the FCT_CLV_CUSTOMER relationship**

Search for `FCT_CLV_CUSTOMER` in `relationships.tmdl`. The block looks like:

```
relationship AutoDetected_a0fd48e3-ac38-4928-a966-3481e4466d7f
    crossFilteringBehavior: bothDirections
    fromCardinality: one
    fromColumn: FCT_CLV_CUSTOMER.CUSTOMER_KEY
    toColumn: DIM_CUSTOMERS.CUSTOMER_KEY
```

- [ ] **Step 2: Change crossFilteringBehavior to singleDirection**

Replace `crossFilteringBehavior: bothDirections` with:

```
    crossFilteringBehavior: singleDirection
```

The full corrected block:
```
relationship AutoDetected_a0fd48e3-ac38-4928-a966-3481e4466d7f
    crossFilteringBehavior: singleDirection
    fromCardinality: one
    fromColumn: FCT_CLV_CUSTOMER.CUSTOMER_KEY
    toColumn: DIM_CUSTOMERS.CUSTOMER_KEY
```

- [ ] **Step 3: Verify the report still opens in Power BI Desktop**

Open `report/Ecommerce Analytics.Report/definition.pbir` in Power BI Desktop. Navigate to the CLV page. Confirm visuals render without errors. If a visual breaks, the slicer that was relying on the reverse filter direction needs to use `CROSSFILTER()` in DAX or a disconnected slicer pattern instead.

- [ ] **Step 4: Commit**

```bash
git add "report/Ecommerce Analytics.SemanticModel/definition/relationships.tmdl"
git commit -m "fix(report): change FCT_CLV_CUSTOMER→DIM_CUSTOMERS relationship to singleDirection"
```

---

## Task 9: Harden CI — Make SQLFluff Blocking and Add Caching

Two gaps in `.github/workflows/dbt-ci.yml`:
1. SQLFluff runs with `|| true`, making lint a no-op — it can never block a PR.
2. `pip install` runs cold on every CI job (adds ~2-3 minutes per run).

**Files:**
- Modify: `.github/workflows/dbt-ci.yml`
- Modify: `.github/workflows/dbt-cd.yml`

- [ ] **Step 1: Remove `|| true` from SQLFluff in dbt-ci.yml**

Find line 47 in `.github/workflows/dbt-ci.yml`:
```yaml
          sqlfluff lint models/ --dialect snowflake --config .sqlfluff || true
```

Replace with:
```yaml
          sqlfluff lint models/ --dialect snowflake --config .sqlfluff
        # Lint failures now block PRs. Fix violations before merging.
```

- [ ] **Step 2: Add pip caching to the lint job in dbt-ci.yml**

After the `Set up Python` step in the `lint` job, add a cache step:

```yaml
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-lint-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-lint-
```

- [ ] **Step 3: Add pip caching to the dbt-build job in dbt-ci.yml**

After the `Set up Python` step in the `dbt-build` job:

```yaml
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-dbt-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-dbt-
```

- [ ] **Step 4: Add pip caching to dbt-cd.yml**

After the `Set up Python` step in `dbt-cd.yml`'s `deploy` job:

```yaml
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-dbt-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-dbt-
```

- [ ] **Step 5: Add a Slack notification step to dbt-cd.yml**

Replace the `notify` job's single `Deployment Status` step in `dbt-cd.yml` with:

```yaml
      - name: Notify Slack on success
        if: needs.deploy.result == 'success'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          curl -s -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data '{
              "text": "✅ *dbt CD deployed to production*\nCommit: `${{ github.sha }}`\nActor: ${{ github.actor }}\nDatabase: ECOMMERCE_RETAIL_DB_PROD"
            }'

      - name: Notify Slack on failure
        if: needs.deploy.result == 'failure'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          curl -s -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data '{
              "text": "❌ *dbt CD FAILED*\nCommit: `${{ github.sha }}`\nActor: ${{ github.actor }}\nCheck: https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }'
```

- [ ] **Step 6: Verify the CI workflow parses correctly**

```bash
# Install the GitHub Actions linter locally (optional but recommended)
pip install actionlint
actionlint .github/workflows/dbt-ci.yml .github/workflows/dbt-cd.yml
```
Expected: No errors.

Alternatively, push to a test branch and check the Actions tab for syntax errors.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/dbt-ci.yml .github/workflows/dbt-cd.yml
git commit -m "feat(ci): make SQLFluff blocking, add pip caching, add Slack notification to CD"
```

---

## Task 10: Save This Plan to the Project

This task copies the plan document into the project so it lives alongside the other plans in `docs/superpowers/plans/`.

**Files:**
- Create: `ecommerce-retail-analytics/docs/superpowers/plans/2026-06-30-scorecard-weakness-remediation.md`

- [ ] **Step 1: Create the docs directory if it doesn't exist**

```bash
mkdir -p ecommerce-retail-analytics/docs/superpowers/plans
```

- [ ] **Step 2: Copy this plan file into the project**

Copy the contents of this plan into:
`ecommerce-retail-analytics/docs/superpowers/plans/2026-06-30-scorecard-weakness-remediation.md`

- [ ] **Step 3: Commit**

```bash
git add ecommerce-retail-analytics/docs/superpowers/plans/2026-06-30-scorecard-weakness-remediation.md
git commit -m "docs: add scorecard weakness remediation plan"
```

---

## Verification

After all tasks are complete, run this end-to-end checklist:

```bash
# 1. dbt: all models build and all tests pass
cd ecommerce-retail-analytics/dbt
dbt build
# Expected: X of X PASS

# 2. dbt source freshness: all sources are fresh
dbt source freshness
# Expected: all green (no ERROR)

# 3. CLV formula sanity: no negative predictions
dbt test --select fct_clv_customer
# Expected: fct_clv_customer_predicted_clv_non_negative PASS

# 4. Seed alignment: 5 segments, no orphans
dbt seed --select rfm_segment_definitions
# Expected: 5 rows

# 5. Airflow: DAG loads and parses
cd ../airflow
docker compose exec airflow-scheduler airflow dags list | grep daily_synthetic_orders
# Expected: daily_synthetic_orders listed, no import errors

# 6. Snowflake: resource monitor is active
# Run in Snowflake: SHOW RESOURCE MONITORS LIKE 'ecommerce_monthly_budget';
# Expected: 1 row with CREDIT_QUOTA set

# 7. CI: open a test PR with a trivial dbt change and verify
#    - SQLFluff job fails if SQL has a lint violation
#    - SQLFluff job passes if SQL is clean
```

---

## Issue Tracker

| Task | Dimension | Score Impact | Effort |
|------|-----------|-------------|--------|
| Task 1: Fernet key + timezone + Docker limits | Production-readiness | +0.5 | 30 min |
| Task 2: Source freshness | Production-readiness | +0.4 | 45 min |
| Task 3: CLV formula fix | Code quality + Business impact | +0.5 | 30 min |
| Task 4: RFM seed reconciliation | Code quality | +0.3 | 15 min |
| Task 5: dim_dates future-proofing | Scalability | +0.2 | 15 min |
| Task 6: Airflow hardening | Production-readiness | +0.5 | 60 min |
| Task 7: Snowflake resource monitor + grants | Scalability + Production-readiness | +0.4 | 45 min |
| Task 8: Power BI relationship fix | Design patterns | +0.2 | 15 min |
| Task 9: CI hardening | Production-readiness | +0.3 | 30 min |
| Task 10: Save plan | — | — | 5 min |
| **Total** | | **~+3.3 → ~7.0 → 8.0+** | **~5 hours** |
