# Task 4 Report: Add Validation Task to Backfill DAG

**Status:** DONE

**Date:** 2026-06-22

**Modified Files:**
- `airflow/dags/backfill_synthetic_orders.py`

---

## Summary

Successfully added a validation task to the backfill DAG that:
- Queries Snowflake for row counts after COPY operations complete
- Sends a success summary to Slack with table counts and total duration
- Runs between COPY tasks and cleanup in the DAG workflow

## Changes Made

### 1. Updated Import Statement (Line 23)
**Before:**
```python
from utils.slack_alerts import slack_failure_callback
```

**After:**
```python
from utils.slack_alerts import slack_failure_callback, send_success_summary
```

### 2. Added `validate_copy_results` Function (Lines 173-208)
Added new function after `cleanup_local_files`:

```python
def validate_copy_results(**context):
    """Query Snowflake for row counts and send success summary to Slack."""
    from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

    hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)

    # Query row counts for all tables
    count_sql = """
    SELECT 'ORDERS' as table_name, COUNT(*) as row_count FROM RAW.ORDERS
    UNION ALL SELECT 'ORDER_ITEMS', COUNT(*) FROM RAW.ORDER_ITEMS
    UNION ALL SELECT 'ORDER_PAYMENTS', COUNT(*) FROM RAW.ORDER_PAYMENTS
    UNION ALL SELECT 'ORDER_REVIEWS', COUNT(*) FROM RAW.ORDER_REVIEWS;
    """

    results = hook.get_records(count_sql)
    table_counts = {row[0]: row[1] for row in results}

    # Log results
    for table, count in table_counts.items():
        print(f"{table}: {count:,} rows")

    # Calculate duration from DAG start
    dag_run = context["dag_run"]
    if dag_run.start_date:
        duration = (context["data_interval_end"] - dag_run.start_date).total_seconds()
    else:
        duration = 0

    # Send success summary to Slack
    send_success_summary(
        dag_id=context["dag"].dag_id,
        table_counts=table_counts,
        duration_seconds=duration,
    )

    return table_counts
```

**Key Features:**
- Uses `SnowflakeHook` to query row counts from all 4 RAW tables
- Logs results to Airflow logs with formatted numbers
- Calculates total DAG duration from start
- Calls `send_success_summary` to post Slack notification
- Returns table counts for XCom storage

### 3. Added Validate Task Operator (Lines 289-292)
Added new PythonOperator after the COPY tasks:

```python
validate = PythonOperator(
    task_id="validate_copy_results",
    python_callable=validate_copy_results,
)
```

### 4. Updated Task Dependencies (Lines 300-304)
**Before:**
```python
# Task dependencies
load_ref_data >> generate >> upload
upload >> [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews]
[copy_orders, copy_order_items, copy_order_payments, copy_order_reviews] >> cleanup
```

**After:**
```python
# Task dependencies
load_ref_data >> generate >> upload
upload >> [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews]
[copy_orders, copy_order_items, copy_order_payments, copy_order_reviews] >> validate
validate >> cleanup
```

**Flow:** All 4 COPY tasks → validate → cleanup

---

## Verification

### Integration Points Confirmed
1. **`send_success_summary` function exists** in `airflow/dags/utils/slack_alerts.py` (lines 65-89)
   - Accepts: `dag_id`, `table_counts`, `duration_seconds`
   - Formats Slack message with checkmark emoji, table counts, and duration
   - Uses existing `send_slack_message` helper

2. **`SnowflakeHook`** is available via `airflow.providers.snowflake.hooks.snowflake`
   - Already used by SnowflakeOperator in same DAG
   - Method `get_records()` returns list of tuples

3. **Context variables** used correctly:
   - `context["dag"].dag_id` - DAG identifier
   - `context["dag_run"]` - DagRun object with start_date
   - `context["data_interval_end"]` - For duration calculation

### Code Quality
- Follows existing DAG patterns (PythonOperator usage, context handling)
- Consistent with error handling approach (prints to logs)
- Matches coding style (comments, formatting)
- No external dependencies beyond existing ones

---

## Expected Behavior

When the backfill DAG runs successfully:

1. **After all 4 COPY tasks complete**, the validate task will:
   - Query Snowflake for row counts in all 4 RAW tables
   - Print formatted counts to Airflow logs (e.g., "ORDERS: 123,456 rows")
   - Calculate total DAG runtime
   - Send Slack notification with summary

2. **Slack message format** (example):
   ```
   ✅ backfill_synthetic_orders Load Complete
   • ORDERS: 123,456 rows
   • ORDER_ITEMS: 234,567 rows
   • ORDER_PAYMENTS: 345,678 rows
   • ORDER_REVIEWS: 98,765 rows
   Duration: 45.2 minutes
   ```

3. **Only after validation succeeds**, cleanup task removes local CSV files

---

## Testing Recommendations

1. **Unit Test** (optional): Mock SnowflakeHook and verify SQL query correctness
2. **Integration Test**: Trigger backfill DAG with small date range, verify:
   - Validation task runs after all COPY tasks
   - Slack message received (if webhook configured)
   - Cleanup runs after validation
3. **Failure Test**: If validation fails, cleanup should NOT run (trigger_rule="all_success")

---

## Notes

- **No breaking changes**: Existing DAG behavior unchanged, only added new step
- **Backward compatible**: If `SLACK_WEBHOOK_URL` not set, validation still runs (just skips Slack notification)
- **Idempotent**: Validation queries are read-only (SELECT COUNT)
- **Low overhead**: Single query with UNION ALL is efficient

---

## Commit Information

**Recommended commit message:**
```
feat(airflow): Add validation task to backfill DAG

- Queries Snowflake for row counts after COPY
- Sends success summary to Slack with table counts and duration
```

**Files to stage:**
```bash
git add airflow/dags/backfill_synthetic_orders.py
```
