import requests
import csv
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Azure API details (loaded from .env)
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")

# URL to fetch usage details
url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/usageDetails?api-version=2021-10-01"

# Authentication (Azure Service Principal)
headers = {
    "Content-Type": "application/json"
}

# Get Azure Token (Using the service principal credentials)
auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
auth_data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://management.azure.com/.default"
}

# Request access token
auth_response = requests.post(auth_url, data=auth_data)
auth_token = auth_response.json().get("access_token")

# If no token, stop here
if not auth_token:
    print("Authentication failed, no access token received.")
    exit(1)

# Headers with the access token
headers["Authorization"] = f"Bearer {auth_token}"

# Payload to request usage details (without ServiceName filter)
payload = {
    "type": "Usage",
    "timeframe": "LastSixMonths",  # Adjust the time frame to the last 6 months
    "dataset": {
        "granularity": "Monthly",
        "aggregation": {
            "total_usage": {
                "name": "UsageQuantity",
                "function": "Sum"
            }
        },
        "grouping": [
            {"type": "Dimension", "name": "Region"},
            {"type": "Dimension", "name": "ServiceName"}
        ]
    }
}

# Make API Request
response = requests.post(url, json=payload, headers=headers)

# Print response status and data to check if it's empty
print(response.status_code)  # Should print 200 if the request was successful
response_data = response.json()  # Get the JSON response
print(json.dumps(response_data, indent=2))  # Print the full response for inspection

# Check if data exists
if 'value' not in response_data or not response_data['value']:
    print("No usage data returned.")
else:
    # Open CSV file to write results
    with open('tts_usage_report.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Region", "ServiceName", "Total Usage (mins)"])
        
        # Iterate over the results and write to CSV
        for item in response_data['value']:
            region = item['properties']['usageStart']
            service_name = item['properties']['serviceName']
            usage_quantity = item['properties']['usageQuantity']
            
            # Write the row to the CSV file
            writer.writerow([region, service_name, usage_quantity])

    print("Data written to tts_usage_report.csv")
