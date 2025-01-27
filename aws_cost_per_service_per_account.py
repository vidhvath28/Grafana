import os
import csv
import boto3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

ce_client = boto3.client(
    "ce",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

def get_aws_costs():
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=7)
    end_date = today - timedelta(days=1)

    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.strftime("%Y-%m-%d"),
            "End": end_date.strftime("%Y-%m-%d"),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
            {"Type": "DIMENSION", "Key": "SERVICE"}
        ],
    )
    return response.get("ResultsByTime", [])

def write_to_csv(data):
    today = datetime.utcnow()
    folder_path = f"AWS/{today.year}/{today.strftime('%m')}"
    
    file_path = f"{folder_path}/aws-cost-per-service-per-account.csv"
    
    with open(file_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Date", "Account", "Service", "Daily Cost (USD)"])
        
        for item in data:
            date = item["TimePeriod"]["Start"]
            for group in item["Groups"]:
                account = group["Keys"][0]
                service = group["Keys"][1]
                cost = group["Metrics"]["UnblendedCost"]["Amount"]
                writer.writerow([date, account, service, cost])

    return file_path

def upload_to_google_drive(file_path):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    
    drive_service = build("drive", "v3", credentials=credentials)
    
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [GOOGLE_DRIVE_FOLDER_ID],
    }
    
    media = MediaFileUpload(file_path, mimetype="text/csv")
    
    try:
        # Upload the file to Google Drive
        uploaded_file = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        
        print(f"File uploaded to Google Drive with ID: {uploaded_file['id']}")
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")

if __name__ == "__main__":
    print("Fetching AWS costs per service per account...")
    cost_data = get_aws_costs()
    
    print("Writing data to CSV...")
    file_path = write_to_csv(cost_data)
    
    print("Uploading CSV to Google Drive...")
    upload_to_google_drive(file_path)
    
    print("Task completed.")
