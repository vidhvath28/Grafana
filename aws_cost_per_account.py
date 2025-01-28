import os
import csv
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment variables
load_dotenv()

# AWS Credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

# Google Drive credentials
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Initialize AWS Boto3 Client (e.g., Cost Explorer)
ce_client = boto3.client(
    "ce",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

# Get AWS cost data per account
def get_aws_cost_per_account():
    today = datetime.utcnow().date()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    response = ce_client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
    )
    return response.get("ResultsByTime", [])

# Write data to a CSV file locally (before uploading to Google Drive)
def write_to_csv(data):
    today = datetime.utcnow()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    # Create directory structure
    folder_path = os.path.join("AWS", year, month, day)
    os.makedirs(folder_path, exist_ok=True)

    # File path for the CSV file
    file_path = os.path.join(folder_path, "aws-cost-per-account.csv")

    # Write data to CSV
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Account ID", "Cost (USD)"])
        for item in data:
            date = item["TimePeriod"]["Start"]
            for group in item["Groups"]:
                account_id = group["Keys"][0]
                cost = group["Metrics"]["UnblendedCost"]["Amount"]
                writer.writerow([date, account_id, cost])

    return file_path

# Upload CSV to Google Drive
def upload_to_google_drive(file_path):
    # Authenticate with Google Drive using the service account
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive.file"]
    )

    # Build the Google Drive API client
    drive_service = build("drive", "v3", credentials=credentials)

    # Upload the file to Google Drive
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [GOOGLE_DRIVE_FOLDER_ID],
    }
    media = MediaFileUpload(file_path, mimetype="text/csv")

    try:
        uploaded_file = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        print(f"File uploaded to Google Drive with ID: {uploaded_file['id']}")
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")

# Main function
if __name__ == "__main__":
    print("Fetching AWS costs per account...")
    cost_data = get_aws_cost_per_account()

    print("Writing data to CSV...")
    file_path = write_to_csv(cost_data)

    print("Uploading CSV to Google Drive...")
    upload_to_google_drive(file_path)

    print("Task completed.")
