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

## Global Constraints

- Slack webhook URL from `SLACK_WEBHOOK_URL` environment variable
- Snowflake connection ID: `snowflake_default`
- All new code follows existing DAG patterns
- No external dependencies beyond `requests` (already available)
