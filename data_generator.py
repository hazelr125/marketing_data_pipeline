import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configuration for consistent synthetic data generation
NUM_CUSTOMERS = 100
BASE_CAMPAIGNS = ["Summer_Sale", "Black_Friday", "Spring_Promo", "Welcome_Series"]

def generate_crm_data() -> pd.DataFrame:
    """Generates CRM customer data and plants duplicate IDs."""
    data = []
    base_date = datetime(2026, 1, 1)
    
    for i in range(1, NUM_CUSTOMERS + 1):
        data.append({
            "customer_id": f"CUST_{i:04d}",
            "first_name": f"User_{i}",
            "email_address": f"user_{i}@example.com",
            "signup_date": (base_date + timedelta(days=random.randint(0, 100))).strftime("%Y-%m-%d"),
            "status": random.choice(["Active", "Inactive", "Churned"])
        })
        
    df = pd.DataFrame(data)
    
    # INTENTIONAL ISSUE 1: Duplicate IDs
    # Duplicate the first 5 rows to simulate double-firing webhooks or merge issues
    duplicates = df.head(5).copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    
    return df

def generate_email_data(customer_ids: list) -> pd.DataFrame:
    """Generates email platform data with nulls, stale dates, and casing inconsistencies."""
    data = []
    base_date = datetime(2026, 5, 1)
    
    for i in range(1, 250):
        # INTENTIONAL ISSUE 2: Inconsistent campaign casing
        campaign = random.choice(BASE_CAMPAIGNS)
        casing_choice = random.choice(["upper", "lower", "original"])
        if casing_choice == "upper":
            campaign = campaign.upper()
        elif casing_choice == "lower":
            campaign = campaign.lower()
            
        # INTENTIONAL ISSUE 3: Stale dates
        # 10% chance to insert a date from 2010 (e.g., system default date error)
        if random.random() < 0.10:
            send_date = datetime(2010, 1, 1).strftime("%Y-%m-%d")
        else:
            send_date = (base_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            
        # Base metrics
        opens = random.randint(0, 3)
        clicks = random.randint(0, opens) if opens > 0 else 0
        
        data.append({
            "email_send_id": f"ES_{i:05d}",
            "customer_id": random.choice(customer_ids),
            "campaign_name": campaign,
            "send_date": send_date,
            "opens": opens,
            "clicks": clicks
        })
        
    df = pd.DataFrame(data)
    
    # INTENTIONAL ISSUE 4: Null values in metrics
    # Randomly assign NaN to opens and clicks to simulate tracking pixel failures
    df.loc[df.sample(frac=0.15).index, 'opens'] = np.nan
    df.loc[df.sample(frac=0.15).index, 'clicks'] = np.nan
    
    return df

def generate_web_analytics_data() -> pd.DataFrame:
    """Generates web traffic data with renamed columns and casing anomalies."""
    data = []
    base_date = datetime(2026, 5, 1)
    
    for i in range(1, 300):
        # Consistent with email issues: Inconsistent campaign casing
        campaign = random.choice(BASE_CAMPAIGNS)
        casing_choice = random.choice(["upper", "lower", "original"])
        if casing_choice == "upper":
            campaign = campaign.upper()
        elif casing_choice == "lower":
            campaign = campaign.lower()
            
        session_date = (base_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        
        data.append({
            "session_id": f"SESS_{i:06d}",
            "session_date": session_date,
            "utm_source": random.choice(["google", "facebook", "email", "direct"]),
            "utm_medium": random.choice(["cpc", "social", "newsletter", "none"]),
            "utm_cmpgn_name_v2": campaign,  # INTENTIONAL ISSUE 5: Renamed column (Schema drift)
            "pageviews": random.randint(1, 15),
            "bounce": random.choice([True, False])
        })
        
    df = pd.DataFrame(data)
    return df

def main():
    print("Generating synthetic datasets with intentional data quality issues...")
    
    # Generate CRM data
    df_crm = generate_crm_data()
    df_crm.to_csv("crm_customers.csv", index=False)
    print(f"Created crm_customers.csv ({len(df_crm)} rows) - Includes duplicate IDs.")
    
    # Extract unique customer IDs to use as foreign keys in email data
    valid_customer_ids = df_crm['customer_id'].unique().tolist()
    
    # Generate Email data
    df_email = generate_email_data(valid_customer_ids)
    df_email.to_csv("email_export.csv", index=False)
    print(f"Created email_export.csv ({len(df_email)} rows) - Includes nulls, stale dates, and casing issues.")
    
    # Generate Web Analytics data
    df_web = generate_web_analytics_data()
    df_web.to_csv("web_analytics.csv", index=False)
    print(f"Created web_analytics.csv ({len(df_web)} rows) - Includes renamed campaign column and casing issues.")
    
    print("\nGeneration complete. Files are ready for the ingestion layer.")

if __name__ == "__main__":
    main()
