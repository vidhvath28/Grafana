import boto3
import csv
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

load_dotenv()

def upload_to_google_drive(file_path, folder_structure):
    """Upload file to Google Drive in specified folder structure."""
    creds = Credentials.from_service_account_file(os.getenv("SERVICE_ACCOUNT_FILE"))
    service = build("drive", "v3", credentials=creds)

    # Create folders if not present
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    for folder in folder_structure.split("/"):
        query = f"'{folder_id}' in parents and name='{folder}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query, spaces="drive").execute()
        folders = results.get("files", [])
        if folders:
            folder_id = folders[0]["id"]
        else:
            file_metadata = {
                "name": folder,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [folder_id],
            }
            folder = service.files().create(body=file_metadata, fields="id").execute()
            folder_id = folder.get("id")

    # Upload file
    file_metadata = {"name": os.path.basename(file_path), "parents": [folder_id]}
    media = MediaFileUpload(file_path)
    service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"Uploaded {file_path} to Google Drive.")

def get_gpu_ec2_cost():
    """Fetch and save AWS GPU EC2 cost data."""
    client = boto3.client(
        "ce",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION"),
    )

    # Set the time period for the last 7 days
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)

    # Query AWS Cost Explorer for EC2 GPU instances cost
    response = client.get_cost_and_usage(
        TimePeriod={"Start": str(start_date), "End": str(end_date)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "Dimensions": {
                "Key": "SERVICE",
                "Values": ["Amazon Elastic Compute Cloud - Compute"]
            }
        },
        GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
    )

    # Prepare CSV data for GPU EC2 costs
    rows = [["Account", "Date", "Cost"]]
    for result in response["ResultsByTime"]:
        date = result["TimePeriod"]["Start"]
        for group in result["Groups"]:
            account = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            rows.append([account, date, cost])

    # Save the data into a CSV file
    filename = "aws_gpu_cost_per_account.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return filename

if __name__ == "__main__":
    # Fetching AWS Cost for EC2 GPU Instances
    print("Fetching AWS Cost for EC2 GPU Instances...")
    gpu_file_path = get_gpu_ec2_cost()
    print(f"File saved: {gpu_file_path}")

    # Uploading the generated CSV file to Google Drive
    today = datetime.now()
    folder_structure = f"AWS/{today.year}/{today.month}/{today.day}"

    # List of all CSV files to upload to Google Drive
    csv_files = [
        "aws-cost-per-service.csv",
        "aws-cost-per-service-per-account.csv",
        "aws-cost-per-account.csv",
        gpu_file_path,  # Add GPU EC2 cost file to the list
    ]

    # Upload each file to Google Drive
    for csv_file in csv_files:
        print(f"Uploading {csv_file}...")
        upload_to_google_drive(csv_file, folder_structure)
