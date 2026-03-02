"""
Olist E-Commerce Data Pipeline DAG

Orchestrates the complete data pipeline:
1. Data Ingestion: Load CSV files into PostgreSQL
2. dbt Run: Transform data (staging + marts)
3. dbt Test: Validate data quality

Schedule: Daily
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ---------------------------------------------------------------------------
# Default arguments applied to every task in this DAG.
# Individual tasks can override these if needed.
# ---------------------------------------------------------------------------
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,   # Each run is independent; don't block on previous failures
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,               # Retry once before marking the task as failed
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 2, 1),
}

# ---------------------------------------------------------------------------
# DAG definition
# schedule_interval='@daily' runs the pipeline once per day at midnight UTC.
# catchup=False prevents Airflow from backfilling all missed runs since
# start_date when the DAG is first enabled.
# ---------------------------------------------------------------------------
dag = DAG(
    'olist_ecommerce_pipeline_bash',
    default_args=default_args,
    description='End-to-end Olist pipeline: Ingest → Transform → Test',
    schedule_interval='@daily',
    catchup=False,
    tags=['olist', 'dbt', 'ecommerce'],
)

# ---------------------------------------------------------------------------
# Task 1: Ingest raw data
# Runs ingest_olist.py as a Python subprocess via the shell.
# The script reads all CSVs from /opt/airflow/datasets and loads them
# into the olist_raw PostgreSQL schema using a truncate-and-reload strategy.
# ---------------------------------------------------------------------------
ingest_task = BashOperator(
    task_id='ingest_raw_data',
    bash_command='cd /opt/airflow && python scripts/ingest_olist.py',
    dag=dag,
)

# ---------------------------------------------------------------------------
# Task 2: dbt run
# Builds all dbt models (staging views + mart tables) against the prod target.
#   --profiles-dir .        → use profiles.yml in the dbt project directory
#   --target prod           → connects to PostgreSQL using the prod profile
#   --target-path /tmp/...  → write compiled SQL artifacts to /tmp to avoid
#                             permission errors on the mounted volume
#   DBT_LOG_PATH=/tmp       → redirect dbt's rotating log file to /tmp for
#                             the same reason (airflow user lacks write access
#                             to the mounted dbt/logs directory)
# ---------------------------------------------------------------------------
dbt_run_task = BashOperator(
    task_id='dbt_run',
    bash_command='cd /opt/airflow/dbt && DBT_LOG_PATH=/tmp dbt run --profiles-dir . --target prod --target-path /tmp/dbt_target',
    dag=dag,
)

# ---------------------------------------------------------------------------
# Task 3: dbt test
# Runs all schema tests (unique, not_null, accepted_values, relationships,
# expression_is_true) and custom singular tests defined in dbt/tests/.
# Uses the same flags as dbt_run for consistency.
# This task only runs if dbt_run succeeds.
# ---------------------------------------------------------------------------
dbt_test_task = BashOperator(
    task_id='dbt_test',
    bash_command='cd /opt/airflow/dbt && DBT_LOG_PATH=/tmp dbt test --profiles-dir . --target prod --target-path /tmp/dbt_target',
    dag=dag,
)

# ---------------------------------------------------------------------------
# Task dependencies — defines the execution order:
#   ingest_raw_data → dbt_run → dbt_test
# Each step must succeed before the next one starts.
# ---------------------------------------------------------------------------
ingest_task >> dbt_run_task >> dbt_test_task
