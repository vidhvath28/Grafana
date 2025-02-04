import os
import datetime
import pandas as pd
from azure.identity import ClientSecretCredential
from azure.mgmt.monitor import MonitorManagementClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Credentials
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
SUBSCRIPTION_IDS = os.getenv("AZURE_SUBSCRIPTION_ID")

# Get first subscription ID from the list
if SUBSCRIPTION_IDS:
    SUBSCRIPTION_ID = SUBSCRIPTION_IDS.split(",")[0].strip()
else:
    raise ValueError("AZURE_SUBSCRIPTION_IDS is not set or invalid in .env file")

RESOURCE_GROUP = os.getenv("RESOURCE_GROUP")
RESOURCE_NAME = os.getenv("RESOURCE_NAME")

# Ensure all required values are available
if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, SUBSCRIPTION_ID, RESOURCE_GROUP, RESOURCE_NAME]):
    raise ValueError("Missing required environment variables. Check your .env file.")

# Construct RESOURCE_ID
RESOURCE_ID = f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/{RESOURCE_NAME}"

# Debugging
print(f"Using Subscription ID: {SUBSCRIPTION_ID}")
print(f"Resource Group: {RESOURCE_GROUP}")
print(f"Resource Name: {RESOURCE_NAME}")
print(f"Resource ID: {RESOURCE_ID}")

# Authenticate with Azure
credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
monitor_client = MonitorManagementClient(credential, SUBSCRIPTION_ID)

# Metrics to fetch
METRIC_NAME = "SynthesizedCharacters"
MONTHS = 6  # Fetch data for the last 6 months

# Get date range
end_date = datetime.datetime.utcnow()
start_date = end_date - datetime.timedelta(days=30 * MONTHS)

# Fetch metrics
metrics_data = monitor_client.metrics.list(
    RESOURCE_ID,
    timespan=f"{start_date}/{end_date}",
    interval="P1M",  # Monthly aggregation
    metricnames=METRIC_NAME,
    aggregation="Total"
)

# Process results
data = []
for metric in metrics_data.value:
    for timeseries in metric.timeseries:
        for data_point in timeseries.data:
            if data_point.total is not None:
                data.append([data_point.time_stamp.strftime("%Y-%m"), data_point.total])

# Convert to DataFrame
df = pd.DataFrame(data, columns=["Month", "TTS Duration (Characters)"])

# Save to CSV
csv_filename = "tts_usage.csv"
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")
