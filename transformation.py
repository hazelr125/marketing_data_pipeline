import sqlite3
from contextlib import closing

DB_NAME = "marketing_warehouse.db"

# The Analytical SQL Transformation
TRANSFORM_SQL = """
-- 1. Ensure idempotency by dropping the final table if it exists
DROP TABLE IF EXISTS campaign_performance;

-- 2. Create the curated table using CTEs
CREATE TABLE campaign_performance AS 

-- CTE A: Deduplicate CRM data to fix the intentional duplicate IDs
WITH deduplicated_crm AS (
    SELECT 
        customer_id,
        MAX(status) as status
    FROM raw_crm_customers
    GROUP BY customer_id
),

-- CTE B: Clean and aggregate email data
clean_email AS (
    SELECT 
        UPPER(e.campaign_name) AS campaign_name,
        COUNT(e.email_send_id) AS total_sends,
        -- Treat NULLs as 0 to avoid breaking SUM calculations
        SUM(CASE WHEN e.opens IS NOT NULL THEN e.opens ELSE 0 END) AS total_opens,
        SUM(CASE WHEN e.clicks IS NOT NULL THEN e.clicks ELSE 0 END) AS total_clicks
    FROM raw_email_export e
    -- INNER JOIN ensures we only count emails tied to valid, deduplicated CRM customers
    INNER JOIN deduplicated_crm c ON e.customer_id = c.customer_id
    GROUP BY UPPER(e.campaign_name)
),

-- CTE C: Clean and aggregate web analytics data
clean_web AS (
    SELECT 
        UPPER(utm_cmpgn_name_v2) AS campaign_name,
        COUNT(session_id) AS total_sessions
    FROM raw_web_analytics
    GROUP BY UPPER(utm_cmpgn_name_v2)
),

-- CTE D: Create a unified list of all campaign names across both sources
-- (Acts as a workaround since older SQLite versions don't support FULL OUTER JOIN)
campaign_master AS (
    SELECT campaign_name FROM clean_email
    UNION
    SELECT campaign_name FROM clean_web
)

-- 3. Final Query: Join aggregates and calculate KPI rates
SELECT 
    m.campaign_name,
    COALESCE(e.total_sends, 0) AS total_sends,
    COALESCE(e.total_opens, 0) AS total_opens,
    COALESCE(e.total_clicks, 0) AS total_clicks,
    COALESCE(w.total_sessions, 0) AS total_sessions,
    
    -- Open Rate: Opens / Sends
    CASE 
        WHEN COALESCE(e.total_sends, 0) > 0 
        THEN ROUND((CAST(e.total_opens AS FLOAT) / e.total_sends), 4) 
        ELSE 0.0 
    END AS open_rate,
    
    -- Click-Through Rate: Clicks / Sends
    CASE 
        WHEN COALESCE(e.total_sends, 0) > 0 
        THEN ROUND((CAST(e.total_clicks AS FLOAT) / e.total_sends), 4) 
        ELSE 0.0 
    END AS click_through_rate

FROM campaign_master m
LEFT JOIN clean_email e ON m.campaign_name = e.campaign_name
LEFT JOIN clean_web w ON m.campaign_name = w.campaign_name;
"""

def main():
    print("Connecting to database and executing transformations...")
    
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            cursor = conn.cursor()
            
            # Execute the massive SQL statement
            cursor.executescript(TRANSFORM_SQL)
            print(" - Transformed raw data and created 'campaign_performance' table.")
            
            # Run a quick validation query to preview the results
            cursor.execute("SELECT * FROM campaign_performance;")
            results = cursor.fetchall()
            
            # Print column headers dynamically
            headers = [description[0] for description in cursor.description]
            print(f"\n| {' | '.join(headers)} |")
            print("-" * 100)
            
            # Print the transformed rows
            for row in results:
                print(f"| {row[0]:<15} | {row[1]:<11} | {row[2]:<11} | {row[3]:<12} | {row[4]:<14} | {row[5]:<9} | {row[6]:<18} |")

if __name__ == "__main__":
    main()
