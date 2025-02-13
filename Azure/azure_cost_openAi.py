import os
import requests
import csv
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load Azure Subscription IDs from .env
AZURE_SUBSCRIPTION_IDS = os.getenv('AZURE_SUBSCRIPTION_ID').split(',')

# Azure Credentials from .env
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = "014e9593-90f9-4b53-a505-0e1b303fd1d6"

# Function to get the Azure access token
def get_access_token():
    url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "scope": "https://management.azure.com/.default"
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Function to get cost data for a specific subscription
def get_cost_data(subscription_id):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()
    
    url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2019-11-01"
    
    query = {
        "type": "Usage",
        "timeframe": "Custom",
        "timePeriod": {"from": start_date, "to": end_date},
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": "ServiceName"}]
        }
    }
    
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    
    max_retries = 5
    retries = 0
    
    while retries < max_retries:
        response = requests.post(url, json=query, headers=headers)
        
        if response.status_code == 429:
            print("Rate limit hit, retrying in 30 seconds...")
            time.sleep(30)
            retries += 1
        else:
            response.raise_for_status()
            data = response.json()
            return data
    
    raise Exception(f"Failed after {max_retries} retries due to rate limiting.")

# Function to write filtered Cognitive Services cost data to CSV
def write_to_csv(all_data):
    csv_filename = "azure_cognitive_services_cost_data.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["SubscriptionID", "PreTaxCost", "UsageDate", "ServiceName", "Currency"])
        
        for subscription_id, data in all_data.items():
            rows = data.get("properties", {}).get("rows", [])
            if rows:
                for row in rows:
                    service_name = row[2]  # Assuming ServiceName is the third column
                    if "Cognitive Services" in service_name:
                        writer.writerow([subscription_id] + row)
    
    print(f"Data has been written to {csv_filename}")

# Main function
def main():
    all_data = {}
    
    for subscription_id in AZURE_SUBSCRIPTION_IDS:
        try:
            data = get_cost_data(subscription_id)
            all_data[subscription_id] = data
        except requests.exceptions.RequestException as e:
            print(f"Error while fetching data for Subscription {subscription_id}: {e}")
        except Exception as e:
            print(f"An error occurred while fetching data for Subscription {subscription_id}: {e}")
    
    if all_data:
        write_to_csv(all_data)
    else:
        print("No data available.")

if __name__ == "__main__":
    main()
