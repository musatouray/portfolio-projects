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

## Global Constraints

- Slack webhook URL from `SLACK_WEBHOOK_URL` environment variable
- Snowflake connection ID: `snowflake_default`
- All new code follows existing DAG patterns
- No external dependencies beyond `requests` (already available)
