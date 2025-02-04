import os
import requests
import csv
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure Subscription ID from .env (single subscription)
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')

# Azure Credentials from .env
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')

# Function to get Azure access token
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

# Function to get resource details for the subscription
def get_resources(subscription_id):
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resources?api-version=2021-04-01"
    headers = {"Authorization": f"Bearer {get_access_token()}"}

    max_retries = 5
    retries = 0

    while retries < max_retries:
        response = requests.get(url, headers=headers)

        if response.status_code == 429:  # Too Many Requests
            print("Rate limit hit, retrying in 30 seconds...")
            time.sleep(30)
            retries += 1
        else:
            response.raise_for_status()
            data = response.json()
            return data.get("value", [])  # List of resources

    raise Exception(f"Failed after {max_retries} retries due to rate limiting.")

# Function to write resource data to CSV
def write_to_csv(resource_data):
    csv_filename = "azure_resources.csv"

    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["SubscriptionID", "ResourceName", "ResourceType", "Location"])  # Header

        for resource in resource_data:
            writer.writerow([
                resource["subscriptionId"],
                resource.get("name", "Unknown"),
                resource.get("type", "Unknown"),
                resource.get("location", "Unknown")
            ])

    print(f"Data has been written to {csv_filename}")

# Main function
def main():
    all_resources = []

    try:
        resources = get_resources(AZURE_SUBSCRIPTION_ID)
        for resource in resources:
            resource["subscriptionId"] = AZURE_SUBSCRIPTION_ID  # Add subscription ID to each resource
            all_resources.append(resource)

    except requests.exceptions.RequestException as e:
        print(f"Error while fetching resources for Subscription {AZURE_SUBSCRIPTION_ID}: {e}")
    except Exception as e:
        print(f"An error occurred while fetching resources for Subscription {AZURE_SUBSCRIPTION_ID}: {e}")

    if all_resources:
        write_to_csv(all_resources)
    else:
        print("No resource data available.")

if __name__ == "__main__":
    main()
