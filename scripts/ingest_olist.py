import os
import pandas as pd
from sqlalchemy import create_engine

# Database connection - use environment variable or default
# For Docker: postgres:5432, For local: localhost:5433
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5433')
DB_URL = f"postgresql://olist:olist@{DB_HOST}:{DB_PORT}/olist"

def load_csvs_to_postgres(source_path, target_schema):
    from sqlalchemy import text
    
    engine = create_engine(DB_URL)
    
    # Get all CSV files in the directory
    files = [f for f in os.listdir(source_path) if f.endswith('.csv')]
    
    if not files:
        print(f"No CSV files found in {source_path}")
        return
    
    print(f"Found {len(files)} CSV files in {source_path}")
    print(f"Database: {DB_URL}")

    for file in files:
        table_name = file.replace('.csv', '').replace('_dataset', '')
        file_full_path = os.path.join(source_path, file)
        
        print(f"Reading {file}...")
        df = pd.read_csv(file_full_path)
        
        # Load to PostgreSQL
        print(f"Loading {table_name} into schema {target_schema}...")
        
        # First load: create table if it doesn't exist
        # Subsequent loads: truncate and reload
        with engine.connect() as conn:
            # Check if table exists
            check_query = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{target_schema}' 
                    AND table_name = '{table_name}'
                );
            """)
            table_exists = conn.execute(check_query).scalar()
            
            if table_exists:
                # Truncate existing table (keeps structure, removes data)
                print(f"  Truncating existing table {target_schema}.{table_name}...")
                conn.execute(text(f"TRUNCATE TABLE {target_schema}.{table_name};"))
                
                # Append to truncated table
                df.to_sql(
                    name=table_name,
                    con=engine,
                    schema=target_schema,
                    if_exists='append',
                    index=False
                )
            else:
                # Create new table
                df.to_sql(
                    name=table_name,
                    con=engine,
                    schema=target_schema,
                    if_exists='fail',
                    index=False
                )
        
        print(f"Finished loading {table_name}.")
    
    print(f"\nSuccessfully loaded {len(files)} tables into {target_schema}")

if __name__ == "__main__":
    # This allows you to test the script manually if needed
    load_csvs_to_postgres('/opt/airflow/datasets', 'olist_raw')