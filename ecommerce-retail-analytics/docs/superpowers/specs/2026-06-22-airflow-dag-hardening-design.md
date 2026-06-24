# Airflow DAG Production Hardening

**Date:** 2026-06-22
**Status:** Approved
**Scope:** Quick wins for production readiness

## Overview

Harden the existing Airflow DAGs (`backfill_synthetic_orders.py` and `daily_synthetic_orders.py`) with three improvements:

1. Slack failure alerts
2. Post-COPY validation task
3. Explicit error handling in COPY statements

## 1. Slack Failure Alerts

### Implementation

Create a shared callback function that posts to Slack when any task fails.

**Location:** New file `airflow/dags/utils/slack_alerts.py`

**Function signature:**
```python
def slack_failure_callback(context: dict) -> None:
    """Post failure alert to Slack channel."""
```

**Message format:**
```
🚨 Airflow Task Failed
DAG: {dag_id}
Task: {task_id}
Execution: {execution_date}
Error: {exception}
```

**Configuration:**
- Webhook URL: `SLACK_WEBHOOK_URL` environment variable
- Channel: `#ecommerce-analytics-alerts` (configured in webhook)

**Integration:**
- Add to `default_args` in both DAGs:
  ```python
  default_args = {
      ...
      "on_failure_callback": slack_failure_callback,
  }
  ```

## 2. Post-COPY Validation Task

### Implementation

Add a validation task that runs after all COPY tasks complete.

**Task name:** `validate_copy_results`

**Behavior:**
1. Query Snowflake for row counts in each table
2. Retrieve expected counts from XCom (files generated/uploaded)
3. Post summary to Slack
4. Log detailed results

**Validation query:**
```sql
SELECT 'ORDERS' as table_name, COUNT(*) as row_count FROM RAW.ORDERS
UNION ALL SELECT 'ORDER_ITEMS', COUNT(*) FROM RAW.ORDER_ITEMS
UNION ALL SELECT 'ORDER_PAYMENTS', COUNT(*) FROM RAW.ORDER_PAYMENTS
UNION ALL SELECT 'ORDER_REVIEWS', COUNT(*) FROM RAW.ORDER_REVIEWS;
```

**Slack messages:**

Success:
```
✅ {DAG} Load Complete
Orders: {n} rows
Order Items: {n} rows
Order Payments: {n} rows
Order Reviews: {n} rows
Duration: {duration}
```

Warning (if issues detected):
```
⚠️ {DAG} Load Warning
Some rows may have been skipped. Check COPY history.
Orders: {n} rows
...
```

**Task dependencies:**
```
[copy_orders, copy_order_items, copy_order_payments, copy_order_reviews] >> validate >> cleanup
```

## 3. Explicit Error Handling

### Implementation

Replace `ON_ERROR = 'CONTINUE'` with explicit error strategies.

**Differentiated approach:**

| DAG | ON_ERROR | Rationale |
|-----|----------|-----------|
| `backfill_synthetic_orders` | `SKIP_FILE` | Many files; one bad file shouldn't block others |
| `daily_synthetic_orders` | `ABORT_STATEMENT` | Single file per table; fail fast on any issue |

**Backfill COPY template:**
```sql
COPY INTO RAW.{table}
FROM @RAW.raw_ecommerce_s3_stage/{folder}/
FILE_FORMAT = RAW.csv_format
PATTERN = '.*\.csv'
ON_ERROR = 'SKIP_FILE';
```

**Daily COPY template:**
```sql
COPY INTO RAW.{table}
FROM @RAW.raw_ecommerce_s3_stage/{folder}/{table}_{date}.csv
FILE_FORMAT = RAW.csv_format
ON_ERROR = 'ABORT_STATEMENT';
```

## File Changes Summary

| File | Change |
|------|--------|
| `airflow/dags/utils/__init__.py` | Create empty init |
| `airflow/dags/utils/slack_alerts.py` | New: Slack callback + success notification functions |
| `airflow/dags/backfill_synthetic_orders.py` | Add callback, validation task, change ON_ERROR |
| `airflow/dags/daily_synthetic_orders.py` | Add callback, validation task, change ON_ERROR |
| `airflow/docker-compose.yml` | Add SLACK_WEBHOOK_URL to environment |

## Testing

After implementation:
1. Trigger a test failure (e.g., bad Snowflake credentials) → verify Slack alert
2. Run successful backfill → verify success summary in Slack
3. Intentionally corrupt a CSV → verify SKIP_FILE behavior in backfill
4. Check Airflow logs for validation task output

## Out of Scope

- Secrets manager integration (future improvement)
- SLA monitoring
- Horizontal scaling (CeleryExecutor/KubernetesExecutor)
