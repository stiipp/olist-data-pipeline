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
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Default arguments
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 2, 1),
}

# Define the DAG
dag = DAG(
    'olist_ecommerce_pipeline_bash',
    default_args=default_args,
    description='End-to-end Olist pipeline: Ingest → Transform → Test',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['olist', 'dbt', 'ecommerce'],
)

# Task 1: Ingest raw data
ingest_task = BashOperator(
    task_id='ingest_raw_data',
    bash_command='cd /opt/airflow && python scripts/ingest_olist.py',
    dag=dag,
)

# Task 2: Run dbt models 
dbt_run_task = BashOperator(
    task_id='dbt_run',
    bash_command='cd /opt/airflow/dbt && dbt run --profiles-dir . --target prod --target-path /tmp/dbt_target',
    dag=dag,
)

# Task 3: Run dbt tests 
dbt_test_task = BashOperator(
    task_id='dbt_test',
    bash_command='cd /opt/airflow/dbt && DBT_LOG_PATH=/tmp dbt test --profiles-dir . --target prod --target-path /tmp/dbt_target',
    dag=dag,
)

# Define task dependencies
ingest_task >> dbt_run_task >> dbt_test_task
