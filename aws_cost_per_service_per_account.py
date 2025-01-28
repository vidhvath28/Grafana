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

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_DEFAULT_REGION:
    raise ValueError("Missing AWS credentials. Check environment variables.")
if not SERVICE_ACCOUNT_FILE or not GOOGLE_DRIVE_FOLDER_ID:
    raise ValueError("Missing Google Drive credentials. Check environment variables.")

# Initialize AWS Boto3 Client for Cost Explorer
try:
    ce_client = boto3.client(
        "ce",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize AWS client: {e}")

# Get AWS cost data per service per account
def get_aws_cost_per_service_per_account():
    today = datetime.utcnow().date()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[
                {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
                {"Type": "DIMENSION", "Key": "SERVICE"}
            ],
        )
        return response.get("ResultsByTime", [])
    except Exception as e:
        raise RuntimeError(f"Error fetching cost data from AWS: {e}")

# Write data to a CSV file inside the folder structure
def write_to_csv(data):
    today = datetime.utcnow()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    # Create directory structure
    folder_path = os.path.join("AWS", year, month, day, "aws_cost_per_service_per_account")
    os.makedirs(folder_path, exist_ok=True)

    # File path for the CSV file
    file_path = os.path.join(folder_path, "aws_cost_per_service_per_account.csv")

    # Write or append data to the CSV file
    try:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Account", "Service", "Cost (USD)"])  # Header row
            for item in data:
                date = item["TimePeriod"]["Start"]
                for group in item["Groups"]:
                    account = group["Keys"][0]
                    service = group["Keys"][1]
                    cost = group["Metrics"]["UnblendedCost"]["Amount"]
                    writer.writerow([date, account, service, cost])
    except Exception as e:
        raise RuntimeError(f"Error writing to CSV: {e}")

    return folder_path

# Upload folder to Google Drive
def upload_to_google_drive(folder_path):
    # Authenticate with Google Drive using the service account
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        drive_service = build("drive", "v3", credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"Failed to authenticate with Google Drive: {e}")

    # Upload files in the folder to Google Drive
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_metadata = {
                "name": file_name,
                "parents": [GOOGLE_DRIVE_FOLDER_ID],
            }
            media = MediaFileUpload(file_path, mimetype="text/csv")
            try:
                uploaded_file = drive_service.files().create(
                    body=file_metadata, media_body=media, fields="id"
                ).execute()
                print(f"File uploaded to Google Drive with ID: {uploaded_file['id']}")
            except Exception as e:
                print(f"Error uploading {file_name} to Google Drive: {e}")

# Main function
if __name__ == "__main__":
    try:
        print("Fetching AWS costs per service per account...")
        cost_data = get_aws_cost_per_service_per_account()

        print("Writing data to CSV...")
        folder_path = write_to_csv(cost_data)

        print("Uploading CSV to Google Drive...")
        upload_to_google_drive(folder_path)

        print("Task completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
