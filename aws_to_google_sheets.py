import os
import boto3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

# Google Sheets credentials
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Initialize AWS Boto3 Client (e.g., Cost Explorer)
ce_client = boto3.client(
    "ce",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

# Query AWS Cost Explorer (Detailed data by service)
def get_aws_costs():
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": "2025-01-01",
            "End": "2025-01-20",
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
        ],
    )
    return response.get("ResultsByTime", [])

# Write data to Google Sheets
def write_to_google_sheets(data):
    # Authorize Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    # Write header row
    sheet.append_row(["Date", "Service", "Cost (USD)"])

    # Write cost data
    for item in data:
        date = item["TimePeriod"]["Start"]
        for group in item["Groups"]:
            service = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            sheet.append_row([date, service, cost])

# Main Function
if __name__ == "__main__":
    print("Fetching AWS costs (detailed by service)...")
    cost_data = get_aws_costs()

    print("Writing detailed data to Google Sheets...")
    write_to_google_sheets(cost_data)

    print("Data transfer complete!")
