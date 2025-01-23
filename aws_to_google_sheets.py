import os
import boto3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

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

# Calculate date range for the previous 7 days
def get_date_range():
    today = datetime.today()
    end_date = today.strftime("%Y-%m-%d")  # current date
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")  # 7 days ago
    return start_date, end_date

# Query AWS Cost Explorer (Detailed data by service)
def get_aws_costs(start_date, end_date):
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End": end_date,
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    return response.get("ResultsByTime", [])

# Write data to Google Sheets in batches
def write_to_google_sheets(data):
    # Authorize Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    # Clear the existing data in the sheet (but keep the header)
    sheet.clear()
    
    # Prepare the rows
    rows = [["Date", "Service", "Cost (USD)"]]  # header row
    for item in data:
        date = item["TimePeriod"]["Start"]
        for group in item["Groups"]:
            service = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            rows.append([date, service, cost])

    # Write all rows at once
    sheet.append_rows(rows)

    # Introduce a delay to avoid exceeding rate limit
    time.sleep(2)  # Delay to prevent hitting Google Sheets API rate limit

# Main Function
if __name__ == "__main__":
    # Get date range for the last 7 days
    start_date, end_date = get_date_range()
    print(f"Fetching AWS costs from {start_date} to {end_date}...")

    # Fetch cost data from AWS
    cost_data = get_aws_costs(start_date, end_date)

    print("Writing detailed data to Google Sheets...")
    write_to_google_sheets(cost_data)

    print("Data transfer complete!")
