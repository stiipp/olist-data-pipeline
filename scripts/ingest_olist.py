"""
ingest_olist.py

Loads all Olist CSV files from a source directory into a PostgreSQL schema.

Behavior:
  - First run: creates each table from scratch.
  - Subsequent runs: truncates the existing table and reloads it.
    This avoids using if_exists='replace', which would DROP and recreate
    the table (losing any constraints or indexes added downstream).

Configuration:
  DB_HOST and DB_PORT are read from environment variables so the same
  script works both locally (localhost:5433) and inside Docker (postgres:5432).
"""

import os
import pandas as pd
from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# Database connection
# Defaults point to the local port-forwarded PostgreSQL instance.
# In Docker, these are overridden via environment variables in docker-compose.
# ---------------------------------------------------------------------------
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5433')
DB_URL = f"postgresql://olist:olist@{DB_HOST}:{DB_PORT}/olist"


def load_csvs_to_postgres(source_path, target_schema):
    """
    Read every CSV in `source_path` and load it into `target_schema` in PostgreSQL.

    Args:
        source_path (str): Directory containing the Olist CSV files.
        target_schema (str): PostgreSQL schema to load data into (e.g., 'olist_raw').
    """
    from sqlalchemy import text

    engine = create_engine(DB_URL)

    # Collect only CSV files from the source directory
    files = [f for f in os.listdir(source_path) if f.endswith('.csv')]

    if not files:
        print(f"No CSV files found in {source_path}")
        return

    print(f"Found {len(files)} CSV files in {source_path}")
    print(f"Target database: {DB_URL}")

    for file in files:
        # Derive the PostgreSQL table name from the filename:
        # e.g., olist_customers_dataset.csv → olist_customers
        table_name = file.replace('.csv', '').replace('_dataset', '')
        file_full_path = os.path.join(source_path, file)

        print(f"\nReading {file}...")
        df = pd.read_csv(file_full_path)
        print(f"  {len(df):,} rows loaded from CSV")

        print(f"  Loading into {target_schema}.{table_name}...")

        with engine.connect() as conn:
            # Check whether the target table already exists in the schema.
            # This controls whether we CREATE fresh or TRUNCATE + APPEND.
            check_query = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = '{target_schema}'
                    AND table_name = '{table_name}'
                );
            """)
            table_exists = conn.execute(check_query).scalar()

            if table_exists:
                # Table already exists — truncate to clear old data while
                # preserving the table structure, then append the fresh data.
                # We avoid DROP + CREATE (if_exists='replace') to prevent
                # losing any schema-level customizations.
                print(f"  Table exists — truncating {target_schema}.{table_name}...")
                conn.execute(text(f"TRUNCATE TABLE {target_schema}.{table_name};"))
                df.to_sql(
                    name=table_name,
                    con=engine,
                    schema=target_schema,
                    if_exists='append',  # Table already emptied by TRUNCATE above
                    index=False
                )
            else:
                # First run — create the table and insert all rows.
                # if_exists='fail' acts as a safety net: raises an error if
                # the table somehow appears between the check and the insert.
                print(f"  Table not found — creating {target_schema}.{table_name}...")
                df.to_sql(
                    name=table_name,
                    con=engine,
                    schema=target_schema,
                    if_exists='fail',
                    index=False
                )

        print(f"  Done: {table_name}")

    print(f"\nSuccessfully loaded {len(files)} tables into schema '{target_schema}'")


if __name__ == "__main__":
    # Entry point for manual runs and for Airflow's BashOperator.
    # Uses the Docker-internal dataset path; override DB_HOST/DB_PORT
    # via environment variables when running locally.
    load_csvs_to_postgres('/opt/airflow/datasets', 'olist_raw')