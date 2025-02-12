import os
import requests
import csv
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv  # Import the dotenv module

# Load environment variables from .env file
load_dotenv()

# Load Azure Subscription IDs from .env
AZURE_SUBSCRIPTION_IDS = os.getenv('AZURE_SUBSCRIPTION_ID').split(',')

# Azure Credentials from .env
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')

# Function to get the Azure access token
def get_access_token():
    url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "scope": "https://management.azure.com/.default"
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()["access_token"]

# Function to get subscription details (including account name)
def get_subscription_details(subscription_id):
    url = f"https://management.azure.com/subscriptions/{subscription_id}?api-version=2020-01-01"
    headers = {
        "Authorization": f"Bearer {get_access_token()}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    subscription_data = response.json()
    
    # Extract subscription name and account number (ID)
    subscription_name = subscription_data.get("displayName", "Unknown")
    subscription_account_number = subscription_data.get("subscriptionId", "Unknown")
    
    return subscription_name, subscription_account_number

# Function to get the cost data for each subscription, per service
def get_cost_data(subscription_id):
    # Set the date range for the last 7 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)  # Last 7 days

    # Format dates in ISO 8601 format (Azure API requires this)
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()

    # Cost Management API endpoint for each subscription
    url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2019-11-01"

    # Set query parameters for the Cost Management API (cost data per service)
    query = {
        "type": "Usage",
        "timeframe": "Custom",
        "timePeriod": {
            "from": start_date,
            "to": end_date
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
                {"type": "Dimension", "name": "ServiceName"}  # Grouping by service
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {get_access_token()}"
    }

    # Retry logic for handling 429 (Too Many Requests) error
    max_retries = 5
    retries = 0

    while retries < max_retries:
        response = requests.post(url, json=query, headers=headers)

        if response.status_code == 429:  # Too Many Requests
            print("Rate limit hit, retrying in 30 seconds...")
            time.sleep(30)  # Wait for 30 seconds before retrying
            retries += 1
        else:
            response.raise_for_status()
            data = response.json()

            # Print the response to check if data is returned
            print(f"API Response for Subscription {subscription_id}:", data)
            return data

    raise Exception(f"Failed after {max_retries} retries due to rate limiting.")

# Function to write cost data to CSV
def write_to_csv(all_data):
    # Prepare the CSV file
    csv_filename = "azure_cost_data_per_service_per_account.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["SubscriptionID", "SubscriptionName", "PreTaxCost", "UsageDate", "ServiceName"])

        # Write the data rows for all subscriptions
        for subscription_id, data in all_data.items():
            rows = data.get("properties", {}).get("rows", [])
            if rows:
                subscription_name, subscription_account_number = get_subscription_details(subscription_id)
                for row in rows:
                    writer.writerow([subscription_account_number, subscription_name] + row)  # Add account number and name to each row

    print(f"Data has been written to {csv_filename}")

# Main function to fetch and store data
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
