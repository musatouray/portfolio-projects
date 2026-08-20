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

## Global Constraints

- Slack webhook URL from `SLACK_WEBHOOK_URL` environment variable
- Snowflake connection ID: `snowflake_default`
- All new code follows existing DAG patterns
- No external dependencies beyond `requests` (already available)
