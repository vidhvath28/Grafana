import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the necessary Azure environment variables
client_id = os.getenv('AZURE_CLIENT_ID')
client_secret = os.getenv('AZURE_CLIENT_SECRET')
tenant_id = os.getenv('AZURE_TENANT_ID')
subscription_ids = os.getenv('AZURE_SUBSCRIPTION_IDS')

# Split the subscription IDs into a list if they are provided
if subscription_ids:
    subscription_ids = subscription_ids.split(',')

# Function to get Azure authentication token
def get_auth_token():
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://management.azure.com/.default"
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()['access_token']

# Function to fetch data from the Azure Cost Management API
def fetch_cost_data(subscription_id, auth_token):
    url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2021-10-01"
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
    query = {
        "type": "Usage",
        "timeframe": "BillingPeriod",
        "dataset": {
            "granularity": "Monthly",
            "aggregation": {
                "totalCost": {
                    "name": "PreTaxCost",
                    "function": "Sum"
                }
            },
            "filter": {
                "dimensions": {
                    "name": "Currency",
                    "operator": "In",
                    "values": ["INR"]
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=query)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

# Function to process and write the data into CSV
def write_to_csv(data):
    import csv
    with open('usage_report.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Subscription ID", "PreTaxCost", "BillingMonth", "Currency"])
        for item in data:
            writer.writerow(item)

# Main function to execute the script logic
def main():
    # Get the authentication token
    try:
        auth_token = get_auth_token()
    except requests.exceptions.HTTPError as e:
        print(f"Error getting auth token: {e}")
        return

    # List to hold all the data from different subscriptions
    all_data = []

    # Process each subscription ID
    for subscription_id in subscription_ids:
        print(f"Fetching data for Subscription {subscription_id}...")
        try:
            data = fetch_cost_data(subscription_id, auth_token)
            for row in data.get('properties', {}).get('rows', []):
                all_data.append([subscription_id] + row)
        except requests.exceptions.HTTPError as e:
            print(f"Error while fetching data for Subscription {subscription_id}: {e}")
    
    # If data is fetched, write it to a CSV file
    if all_data:
        write_to_csv(all_data)
        print("Data successfully written to 'usage_report.csv'")
    else:
        print("No data available.")

if __name__ == "__main__":
    main()
