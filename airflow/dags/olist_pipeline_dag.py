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
    'olist_ecommerce_pipeline',
    default_args=default_args,
    description='End-to-end Olist pipeline: Ingest → Transform → Test',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['olist', 'dbt', 'ecommerce'],
)


def run_ingestion():
    """
    Run the ingestion script to load CSV files into PostgreSQL
    """
    import sys
    sys.path.insert(0, '/opt/airflow/scripts')
    
    # Import and run the ingestion function
    from ingest_olist import load_csvs_to_postgres
    
    # Use Docker internal paths and connection
    load_csvs_to_postgres('/opt/airflow/datasets', 'olist_raw')


# Task 1: Ingest raw data
ingest_task = PythonOperator(
    task_id='ingest_raw_data',
    python_callable=run_ingestion,
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
