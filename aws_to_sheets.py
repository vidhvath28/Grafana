import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access the credentials from .env
GRAFANA_API_URL = os.getenv("GRAFANA_API_URL")
GRAFANA_TOKEN = os.getenv("GRAFANA_TOKEN")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Fetch data from Grafana
headers = {"Authorization": f"Bearer {GRAFANA_TOKEN}"}
response = requests.get(GRAFANA_API_URL, headers=headers)

if response.status_code == 200:
    grafana_data = response.json()
    print("Grafana Data Fetched Successfully!")

    # Write data to Google Sheets
    sheet.append_row(["Dashboard Name", "Type", "URL"])  # Header row (optional)
    for dashboard in grafana_data:
        sheet.append_row([dashboard.get("title"), dashboard.get("type"), dashboard.get("url")])

    print("Data written to Google Sheets successfully.")
else:
    print(f"Failed to fetch Grafana data: {response.status_code}, {response.text}")
