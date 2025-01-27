import os
import csv
import boto3
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import StringIO


load_dotenv()


AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")


ce_client = boto3.client(
    "ce",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)


SCOPES = ["https://www.googleapis.com/auth/drive.file"]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)


def get_aws_costs():
    """Fetch daily AWS costs for the past 7 days."""
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=7)
    end_date = today - timedelta(days=1)

    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.strftime("%Y-%m-%d"),
            "End": end_date.strftime("%Y-%m-%d"),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
    )
    return response.get("ResultsByTime", [])


def write_to_google_drive(data):
    """Write AWS cost data to a CSV file and upload it to Google Drive."""
    today = datetime.now(timezone.utc)
    file_name = f"aws-cost-per-account-{today.strftime('%Y-%m-%d')}.csv"

 
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Date", "Account", "Daily Cost (USD)"])

    for item in data:
        date = item["TimePeriod"]["Start"]
        for group in item["Groups"]:
            account = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            writer.writerow([date, account, cost])

    csv_buffer.seek(0)

    file_metadata = {"name": file_name, "parents": ["1GwBrcNRfOsfilO00OM_Fl9W4Q_7lOJcU"]}
    media = MediaIoBaseUpload(csv_buffer, mimetype="text/csv")

    drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"CSV file uploaded to Google Drive with the name: {file_name}")


if __name__ == "__main__":
    print("Fetching AWS costs per account...")
    cost_data = get_aws_costs()
    print("Uploading data to Google Drive...")
    write_to_google_drive(cost_data)
    print("Task completed.")
