import os
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the API token from the environment
token = os.getenv("GRAFANA_API_KEY")

# Grafana API base URL
base_url = "https://monitoring.infra.yellow.ai/api"

# API endpoint to search dashboards
endpoint = "/search"

# Set the authorization header
headers = {
    "Authorization": f"Bearer {token}"
}

# Send the GET request to the Grafana API
response = requests.get(base_url + endpoint, headers=headers)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # If successful, print the JSON response
    dashboards = response.json()
    print("Dashboards:")
    for dashboard in dashboards:
        print(f"Title: {dashboard['title']}, UID: {dashboard['uid']}")
else:
    # If not successful, print the error
    print(f"Error: {response.status_code}")
    print(response.text)
