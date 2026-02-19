import os
import pandas as pd
from sqlalchemy import create_engine

# Internal Docker connection string
DB_URL = "postgresql://olist:olist@localhost:5433/olist"

def load_csvs_to_postgres(source_path, target_schema):
    engine = create_engine(DB_URL)

    source_path = "./airflow/datasets"
    
    # Get all CSV files in the directory
    files = [f for f in os.listdir(source_path) if f.endswith('.csv')]
    
    if not files:
        print(f"No CSV files found in {source_path}")
        return

    for file in files:
        table_name = file.replace('.csv', '').replace('_dataset', '')
        file_full_path = os.path.join(source_path, file)
        
        print(f"Reading {file}...")
        df = pd.read_csv(file_full_path)
        
        # Load to PostgreSQL
        print(f"Loading {table_name} into schema {target_schema}...")
        df.to_sql(
            name=table_name,
            con=engine,
            schema=target_schema,
            if_exists='replace',
            index=False
        )
        print(f"Finished loading {table_name}.")

if __name__ == "__main__":
    # This allows you to test the script manually if needed
    load_csvs_to_postgres('/airflow/datasets', 'olist_raw')