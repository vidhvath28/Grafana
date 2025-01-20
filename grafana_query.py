import gspread
from google.oauth2.service_account import Credentials
import requests
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Load sensitive data from environment variables
GRAFANA_API_URL = os.getenv("GRAFANA_API_URL")
GRAFANA_TOKEN = os.getenv("GRAFANA_TOKEN")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

if not all([GRAFANA_API_URL, GRAFANA_TOKEN, SERVICE_ACCOUNT_FILE, SPREADSHEET_ID]):
    raise ValueError("One or more environment variables are missing. Check the .env file.")

# Fetch data from Grafana API
headers = {"Authorization": f"Bearer {GRAFANA_TOKEN}"}
response = requests.get(GRAFANA_API_URL, headers=headers)

if response.status_code != 200:
    raise Exception(f"Failed to fetch Grafana data. Status code: {response.status_code}")

grafana_data = response.json()  # Assume this returns a list of dashboards

if not grafana_data:
    raise Exception("Grafana API returned no data.")

# Extract all keys from the first dashboard entry (assuming all entries have the same structure)
keys = grafana_data[0].keys()

# Authenticate with Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# Open the Google Sheet
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Clear existing content
sheet.clear()

# Add headers dynamically based on keys from the Grafana data
sheet.append_row(list(keys))

# Function to append rows with exponential backoff
def exponential_backoff_request(sheet, data, retries=5):
    for i in range(retries):
        try:
            # Attempt to append data in batches
            sheet.append_rows(data)
            break  # Exit the loop if successful
        except gspread.exceptions.APIError as e:
            if "Rate Limit Exceeded" in str(e):
                wait_time = 2 ** i  # Exponential backoff: 2^i seconds
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise e  # Raise other errors

# Prepare Grafana data for batch insertion
rows = [[dashboard.get(key, "") for key in keys] for dashboard in grafana_data]

# Append Grafana data in batches
exponential_backoff_request(sheet, rows)

print("Data successfully written to the Google Sheet.")
