import sqlite3
import csv
import os
from contextlib import closing

# Database configuration
DB_NAME = "marketing_warehouse.db"

# Schema definitions for the raw/staging layer
# Everything is stored relatively loosely (TEXT/INTEGER) to allow messy data in staging
SCHEMAS = {
    "raw_crm_customers": """
        CREATE TABLE IF NOT EXISTS raw_crm_customers (
            customer_id TEXT,
            first_name TEXT,
            email_address TEXT,
            signup_date TEXT,
            status TEXT
        )
    """,
    "raw_email_export": """
        CREATE TABLE IF NOT EXISTS raw_email_export (
            email_send_id TEXT,
            customer_id TEXT,
            campaign_name TEXT,
            send_date TEXT,
            opens INTEGER,
            clicks INTEGER
        )
    """,
    "raw_web_analytics": """
        CREATE TABLE IF NOT EXISTS raw_web_analytics (
            session_id TEXT,
            session_date TEXT,
            utm_source TEXT,
            utm_medium TEXT,
            utm_cmpgn_name_v2 TEXT,
            pageviews INTEGER,
            bounce TEXT
        )
    """
}

def clean_row(row):
    """
    Cleans raw CSV strings for SQL ingestion.
    Converts empty strings to Python None (which translates to SQL NULL).
    """
    return [None if val.strip() == "" else val.strip() for val in row]

def ingest_csv_to_table(cursor, file_path, table_name, num_columns):
    """
    Reads a CSV file and inserts its contents into the specified table using executemany.
    """
    if not os.path.exists(file_path):
        print(f"Warning: File not found: {file_path}. Skipping.")
        return 0

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip the header row
        
        # Prepare the row generator, applying the cleaning function
        rows = (clean_row(row) for row in reader)
        
        # Generate the dynamic parameterized insert query (e.g., ?, ?, ?)
        placeholders = ",".join(["?"] * num_columns)
        insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"
        
        # Execute the bulk insert
        cursor.executemany(insert_query, rows)
        
        # Return the number of inserted rows
        return cursor.rowcount

def main():
    print(f"Connecting to database: {DB_NAME}...")
    
    # Use contextlib.closing to ensure the connection is safely closed
    # The 'with conn' block manages the database transaction (auto-commit/rollback)
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            cursor = conn.cursor()
            
            # 1. Initialize raw layer tables (Drop if exists to ensure idempotent runs)
            print("Initializing raw layer schemas...")
            for table_name, ddl in SCHEMAS.items():
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                cursor.execute(ddl)
                print(f" - Created table: {table_name}")
            
            print("\nStarting data ingestion...")
            
            # 2. Ingest CRM Data (5 columns)
            crm_count = ingest_csv_to_table(
                cursor=cursor,
                file_path="crm_customers.csv",
                table_name="raw_crm_customers",
                num_columns=5
            )
            print(f" - Loaded {crm_count} rows into raw_crm_customers")
            
            # 3. Ingest Email Data (6 columns)
            email_count = ingest_csv_to_table(
                cursor=cursor,
                file_path="email_export.csv",
                table_name="raw_email_export",
                num_columns=6
            )
            print(f" - Loaded {email_count} rows into raw_email_export")
            
            # 4. Ingest Web Analytics Data (7 columns)
            web_count = ingest_csv_to_table(
                cursor=cursor,
                file_path="web_analytics.csv",
                table_name="raw_web_analytics",
                num_columns=7
            )
            print(f" - Loaded {web_count} rows into raw_web_analytics")
            
    print("\nIngestion complete. Database connection safely closed.")

if __name__ == "__main__":
    main()
