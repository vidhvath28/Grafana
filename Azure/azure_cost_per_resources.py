import requests
import json
import csv
import os
from datetime import datetime
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Azure credentials from environment variables
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")

# Get Azure Access Token
def get_access_token():
    try:
        credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        token = credential.get_token("https://management.azure.com/.default")
        return token.token
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

# Fetch Cost Data for Today
def fetch_cost_data():
    today = datetime.today().strftime('%Y-%m-%d')  # Get today's date in YYYY-MM-DD format
    
    url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01"
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {
            "from": today,  # Start date (today)
            "to": today     # End date (today)
        },
        "dataset": {
            "granularity": "Daily",
            "aggregation": {
                "totalCost": {
                    "name": "PreTaxCost",
                    "function": "Sum"
                }
            },
            "grouping": [
                {"type": "Dimension", "name": "ResourceId"},
                {"type": "Dimension", "name": "ResourceType"},
                {"type": "Dimension", "name": "ResourceLocation"},
                {"type": "Dimension", "name": "ResourceGroupName"},
                {"type": "Dimension", "name": "ServiceName"},
                {"type": "Dimension", "name": "ServiceTier"},
                {"type": "Dimension", "name": "Meter"}
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching cost data: {response.status_code}, {response.text}")
        return None

# Save Data to CSV
def save_to_csv(data):
    if not data or "properties" not in data or "rows" not in data["properties"]:
        print("No data available to save.")
        return
    
    filename = "azure_cost_resources.csv"

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        
        writer.writerow([
            "UsageDate", "CostUSD", "ResourceId", "ResourceType", "ResourceLocation", 
            "ResourceGroupName", "ServiceName", "ServiceTier", "Meter", "Currency"
        ])
        
        for row in data["properties"]["rows"]:
            if len(row) >= 7:
                usage_date = datetime.today().strftime('%Y-%m-%d')
                cost_usd = row[-1]
                writer.writerow([usage_date, cost_usd] + row[:-1] + ["USD"])

    print(f"Data successfully saved to {filename}")

# Main Execution
if __name__ == "__main__":
    cost_data = fetch_cost_data()
    save_to_csv(cost_data)
