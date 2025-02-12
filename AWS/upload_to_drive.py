import boto3
import csv
import os
import glob
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

if __name__ == "__main__":
    # Uploading the generated CSV files to Google Drive
    today = datetime.now()
    folder_structure = f"AWS/{today.year}/{today.month}/{today.day}"

    # Use glob to find all .csv files in the current directory
    csv_files = glob.glob("*.csv")

    # Upload each file to Google Drive
    for csv_file in csv_files:
        print(f"Uploading {csv_file}...")
        upload_to_google_drive(csv_file, folder_structure)
