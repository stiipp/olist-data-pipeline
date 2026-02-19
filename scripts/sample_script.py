import psycopg2
import time

for attempt in range(5):
    try:
        print("Attempting to connect to PostgreSQL...")
        conn = psycopg2.connect(
            host="postgres",
            database="airflow",
            user="airflow",
            password="airflow"
        )
        print("✅ Connected to PostgreSQL!")

        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        cur.close()
        conn.close()
        break

    except Exception as e:
        print(f"❌ Attempt {attempt + 1} failed: {e}")
        time.sleep(5)
else:
    print("💥 All attempts to connect to Postgres failed.")
