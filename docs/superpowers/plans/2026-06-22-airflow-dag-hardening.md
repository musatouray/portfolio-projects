# Airflow DAG Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Slack failure alerts, post-COPY validation, and explicit error handling to Airflow DAGs.

**Architecture:** Create a shared `slack_alerts.py` utility module with callback functions, then integrate into both DAGs. Add a validation task after COPY operations. Change ON_ERROR strategy per DAG type.

**Tech Stack:** Python 3.12, Airflow 2.9.3, Snowflake, Slack Incoming Webhooks

## Global Constraints

- Slack webhook URL from `SLACK_WEBHOOK_URL` environment variable
- Snowflake connection ID: `snowflake_default`
- All new code follows existing DAG patterns
- No external dependencies beyond `requests` (already available)

---

## File Structure

| File | Responsibility |
|------|----------------|
| `airflow/dags/utils/__init__.py` | Package marker |
| `airflow/dags/utils/slack_alerts.py` | Slack notification functions |
| `airflow/dags/backfill_synthetic_orders.py` | Backfill DAG (modify) |
| `airflow/dags/daily_synthetic_orders.py` | Daily DAG (modify) |
| `airflow/docker-compose.yml` | Add SLACK_WEBHOOK_URL env var |

---

### Task 1: Create Slack Alerts Utility Module

**Files:**
- Create: `airflow/dags/utils/__init__.py`
- Create: `airflow/dags/utils/slack_alerts.py`
- Modify: `airflow/docker-compose.yml:19-30`

**Interfaces:**
- Consumes: `SLACK_WEBHOOK_URL` environment variable
- Produces:
  - `slack_failure_callback(context: dict) -> None` - Airflow on_failure_callback
  - `send_slack_message(message: str) -> bool` - Generic Slack poster
  - `send_success_summary(dag_id: str, table_counts: dict, duration_seconds: float) -> None` - Success notification

- [ ] **Step 1: Create utils package**

Create empty `__init__.py`:

```python
# airflow/dags/utils/__init__.py
```

- [ ] **Step 2: Create slack_alerts.py with send_slack_message**

```python
# airflow/dags/utils/slack_alerts.py
"""Slack notification utilities for Airflow DAGs."""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError


def send_slack_message(message: str) -> bool:
    """
    Send a message to Slack via webhook.

    Args:
        message: The message text to send (supports Slack formatting)

    Returns:
        True if successful, False otherwise
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("SLACK_WEBHOOK_URL not configured, skipping notification")
        return False

    payload = json.dumps({"text": message}).encode("utf-8")

    try:
        request = Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=10) as response:
            return response.status == 200
    except URLError as e:
        print(f"Failed to send Slack message: {e}")
        return False
```

- [ ] **Step 3: Add slack_failure_callback function**

Append to `slack_alerts.py`:

```python
def slack_failure_callback(context: dict) -> None:
    """
    Airflow callback for task failures. Posts alert to Slack.

    Args:
        context: Airflow context dictionary containing task instance info
    """
    ti = context.get("task_instance")
    exception = context.get("exception")

    dag_id = ti.dag_id if ti else "unknown"
    task_id = ti.task_id if ti else "unknown"
    execution_date = ti.execution_date.strftime("%Y-%m-%d %H:%M:%S") if ti else "unknown"
    error_msg = str(exception)[:200] if exception else "No error message"

    message = f"""🚨 *Airflow Task Failed*
*DAG:* {dag_id}
*Task:* {task_id}
*Execution:* {execution_date}
*Error:* {error_msg}"""

    send_slack_message(message)
```

- [ ] **Step 4: Add send_success_summary function**

Append to `slack_alerts.py`:

```python
def send_success_summary(
    dag_id: str,
    table_counts: dict[str, int],
    duration_seconds: float,
) -> None:
    """
    Send success summary to Slack after successful load.

    Args:
        dag_id: The DAG identifier
        table_counts: Dict mapping table names to row counts
        duration_seconds: Total duration of the DAG run
    """
    duration_min = duration_seconds / 60

    rows_section = "\n".join(
        f"• {table}: {count:,} rows"
        for table, count in table_counts.items()
    )

    message = f"""✅ *{dag_id} Load Complete*
{rows_section}
*Duration:* {duration_min:.1f} minutes"""

    send_slack_message(message)
```

- [ ] **Step 5: Add SLACK_WEBHOOK_URL to docker-compose.yml**

Modify `airflow/docker-compose.yml`, add after line 30 (after AWS credentials):

```yaml
    # Slack notifications
    SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL}
```

- [ ] **Step 6: Commit**

```bash
git add airflow/dags/utils/__init__.py airflow/dags/utils/slack_alerts.py airflow/docker-compose.yml
git commit -m "feat(airflow): Add Slack notification utilities

- send_slack_message for generic Slack posts
- slack_failure_callback for Airflow on_failure_callback
- send_success_summary for load completion notifications"
```

---

### Task 2: Update Backfill DAG with Slack Alerts and ON_ERROR

**Files:**
- Modify: `airflow/dags/backfill_synthetic_orders.py`

**Interfaces:**
- Consumes: `slack_failure_callback` from `utils.slack_alerts`
- Produces: Updated DAG with failure callbacks and `ON_ERROR = 'SKIP_FILE'`

- [ ] **Step 1: Add import for slack_failure_callback**

At top of `backfill_synthetic_orders.py`, after other imports (around line 21):

```python
from utils.slack_alerts import slack_failure_callback
```

- [ ] **Step 2: Add on_failure_callback to default_args**

Modify `default_args` dict (around line 38-45):

```python
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "on_failure_callback": slack_failure_callback,
}
```

- [ ] **Step 3: Change ON_ERROR to SKIP_FILE**

Modify `COPY_SQL_TEMPLATE` (around line 171-177):

```python
COPY_SQL_TEMPLATE = """
COPY INTO RAW.{table}
FROM @RAW.raw_ecommerce_s3_stage/{folder}/
FILE_FORMAT = RAW.csv_format
PATTERN = '.*\\.csv'
ON_ERROR = 'SKIP_FILE';
"""
```

- [ ] **Step 4: Commit**

```bash
git add airflow/dags/backfill_synthetic_orders.py
git commit -m "feat(airflow): Add Slack alerts and SKIP_FILE to backfill DAG

- on_failure_callback sends Slack alert on task failure
- ON_ERROR changed from CONTINUE to SKIP_FILE"
```

---

### Task 3: Update Daily DAG with Slack Alerts and ON_ERROR

**Files:**
- Modify: `airflow/dags/daily_synthetic_orders.py`

**Interfaces:**
- Consumes: `slack_failure_callback` from `utils.slack_alerts`
- Produces: Updated DAG with failure callbacks and `ON_ERROR = 'ABORT_STATEMENT'`

- [ ] **Step 1: Add import for slack_failure_callback**

At top of `daily_synthetic_orders.py`, after other imports (around line 17):

```python
from utils.slack_alerts import slack_failure_callback
```

- [ ] **Step 2: Add on_failure_callback to default_args**

Modify `default_args` dict (around line 34-41):

```python
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "on_failure_callback": slack_failure_callback,
}
```

- [ ] **Step 3: Change ON_ERROR to ABORT_STATEMENT**

Modify `COPY_DAILY_SQL` (around line 125-130):

```python
COPY_DAILY_SQL = """
COPY INTO RAW.{table}
FROM @RAW.raw_ecommerce_s3_stage/{folder}/{table}_{date}.csv
FILE_FORMAT = RAW.csv_format
ON_ERROR = 'ABORT_STATEMENT';
"""
```

- [ ] **Step 4: Commit**

```bash
git add airflow/dags/daily_synthetic_orders.py
git commit -m "feat(airflow): Add Slack alerts and ABORT_STATEMENT to daily DAG

- on_failure_callback sends Slack alert on task failure
- ON_ERROR changed from CONTINUE to ABORT_STATEMENT"
```

---

### Task 4: Add Validation Task to Backfill DAG

**Files:**
- Modify: `airflow/dags/backfill_synthetic_orders.py`

**Interfaces:**
- Consumes: `send_success_summary` from `utils.slack_alerts`, SnowflakeHook
- Produces: `validate_copy_results` task between COPY tasks and cleanup

- [ ] **Step 1: Add import for send_success_summary**

Update import at top of `backfill_synthetic_orders.py`:

```python
from utils.slack_alerts import slack_failure_callback, send_success_summary
```

- [ ] **Step 2: Add validate_copy_results function**

Add after `cleanup_local_files` function (around line 168), before `COPY_SQL_TEMPLATE`:

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

- [ ] **Step 3: Add validate task to DAG**

Inside the `with DAG(...) as dag:` block, after the copy tasks (around line 246), add:

```python
    validate = PythonOperator(
        task_id="validate_copy_results",
        python_callable=validate_copy_results,
    )
```

- [ ] **Step 4: Update task dependencies**

Replace the existing dependency lines at the end of the DAG (around line 254-257):

```python
    # Task dependencies
    load_ref_data >> generate >> upload
    upload >> [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews]
    [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews] >> validate
    validate >> cleanup
```

- [ ] **Step 5: Commit**

```bash
git add airflow/dags/backfill_synthetic_orders.py
git commit -m "feat(airflow): Add validation task to backfill DAG

- Queries Snowflake for row counts after COPY
- Sends success summary to Slack with table counts and duration"
```

---

### Task 5: Add Validation Task to Daily DAG

**Files:**
- Modify: `airflow/dags/daily_synthetic_orders.py`

**Interfaces:**
- Consumes: `send_success_summary` from `utils.slack_alerts`, SnowflakeHook
- Produces: `validate_copy_results` task between COPY tasks and cleanup

- [ ] **Step 1: Add import for send_success_summary**

Update import at top of `daily_synthetic_orders.py`:

```python
from utils.slack_alerts import slack_failure_callback, send_success_summary
```

- [ ] **Step 2: Add validate_copy_results function**

Add after `cleanup_daily_files` function (around line 122), before `COPY_DAILY_SQL`:

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

- [ ] **Step 3: Add validate task to DAG**

Inside the `with DAG(...) as dag:` block, after the copy tasks (around line 203), add:

```python
    validate = PythonOperator(
        task_id="validate_copy_results",
        python_callable=validate_copy_results,
    )
```

- [ ] **Step 4: Update task dependencies**

Replace the existing dependency lines at the end of the DAG (around line 211-214):

```python
    # Task dependencies
    generate >> upload
    upload >> [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews]
    [copy_orders, copy_order_items, copy_order_payments, copy_order_reviews] >> validate
    validate >> cleanup
```

- [ ] **Step 5: Commit**

```bash
git add airflow/dags/daily_synthetic_orders.py
git commit -m "feat(airflow): Add validation task to daily DAG

- Queries Snowflake for row counts after COPY
- Sends success summary to Slack with table counts and duration"
```

---

### Task 6: Manual Testing

**Files:**
- None (testing only)

**Interfaces:**
- Consumes: All previous tasks completed
- Produces: Verified working implementation

- [ ] **Step 1: Restart Airflow to pick up changes**

```bash
cd airflow
docker compose down
docker compose up -d
```

Wait for containers to start (about 30 seconds).

- [ ] **Step 2: Test Slack webhook directly**

```bash
docker compose exec airflow-scheduler python -c "
from utils.slack_alerts import send_slack_message
result = send_slack_message('🧪 Test message from Airflow')
print('Success!' if result else 'Failed')
"
```

Expected: Message appears in `#ecommerce-analytics-alerts` Slack channel.

- [ ] **Step 3: Verify DAG parsing**

```bash
docker compose exec airflow-scheduler airflow dags list | grep synthetic
```

Expected output:
```
backfill_synthetic_orders
daily_synthetic_orders
```

- [ ] **Step 4: Test failure callback (optional)**

Temporarily break a task to verify Slack alert fires:

```bash
docker compose exec airflow-scheduler airflow tasks test backfill_synthetic_orders copy_orders_to_snowflake 2024-01-01
```

If Snowflake credentials work, this succeeds. To test failure, temporarily rename connection.

- [ ] **Step 5: Document completion**

No commit needed. Testing complete.
