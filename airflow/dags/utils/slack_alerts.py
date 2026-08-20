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
