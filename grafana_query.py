import gspread
from google.oauth2.service_account import Credentials
import requests
import time

# Load Grafana data
GRAFANA_API_URL = "https://monitoring.infra.yellow.ai/api/search"
GRAFANA_TOKEN = "glsa_Dj406pkZCsU2wcsHdfuqkaS6UXpav5ZP_c452680c"

headers = {"Authorization": f"Bearer {GRAFANA_TOKEN}"}
response = requests.get(GRAFANA_API_URL, headers=headers)
grafana_data = response.json()  # Assume this returns a list of dashboards

# Authenticate with Google Sheets
SERVICE_ACCOUNT_FILE = "C:\\Users\\Vidhvath28\\Downloads\\grafana-cost-management-fa82502cc524.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# Open the Google Sheet
SPREADSHEET_ID = "1YJLFsBg_YX_ePyTJtGe5tCcUbUm6ySQIdq8yGXJDNV8"
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Write data to the Google Sheet
# Clear existing content
sheet.clear()

# Add headers
sheet.append_row(["Title", "UID"])  # Modify as per your Grafana data structure

# Function to append rows with exponential backoff
def exponential_backoff_request(sheet, data, retries=5):
    for i in range(retries):
        try:
            # Attempt to append data in batches
            sheet.append_rows(data)
            break  # Exit the loop if successful
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:  # Rate limit error
                wait_time = 2 ** i  # Exponential backoff: 2^i seconds
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise e  # Raise other errors

# Prepare Grafana data for batch insertion
rows = [[dashboard["title"], dashboard["uid"]] for dashboard in grafana_data]

# Append Grafana data in batches
exponential_backoff_request(sheet, rows) 