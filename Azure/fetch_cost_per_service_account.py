import os
import csv
import datetime
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Authenticate
credentials = ClientSecretCredential(
    client_id=os.getenv("AZURE_CLIENT_ID"),
    client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    tenant_id=os.getenv("AZURE_TENANT_ID"),
)
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
client = CostManagementClient(credentials)

# Get last 7 days date range
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=7)

# Fetch cost per service per account
query = client.query.usage(
    scope=f"/subscriptions/{subscription_id}",
    parameters={
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {"from": str(start_date), "to": str(end_date)},
        "dataset": {
            "granularity": "None",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            "grouping": [
                {"type": "Dimension", "name": "ServiceName"},
                {"type": "Dimension", "name": "SubscriptionId"},
            ],
        },
    },
)

# Save to CSV
output_folder = f"Azure/{end_date.year}/{end_date.month:02}/{end_date.day:02}/"
os.makedirs(output_folder, exist_ok=True)

csv_file = os.path.join(output_folder, "azure-cost-per-service-per-account.csv")
with open(csv_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Subscription", "Service", "Cost (USD)", "Currency"])
    for row in query.rows:
        writer.writerow([row[1], row[0], row[2], "USD"])

print(f"✅ Azure cost per service per account saved: {csv_file}")
