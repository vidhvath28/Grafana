import os
import csv
import boto3
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

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
        GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
    )
    return response.get("ResultsByTime", [])

def write_to_csv(data):
    today = datetime.utcnow()
    folder_path = f"AWS/{today.year}/{today.strftime('%m')}"
    os.makedirs(folder_path, exist_ok=True)

    file_path = f"{folder_path}/aws-cost-per-account.csv"
    with open(file_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Date", "Account", "Daily Cost (USD)"])

        for item in data:
            date = item["TimePeriod"]["Start"]
            for group in item["Groups"]:
                account = group["Keys"][0]
                cost = group["Metrics"]["UnblendedCost"]["Amount"]
                writer.writerow([date, account, cost])

    print(f"CSV file saved to {file_path}")

if __name__ == "__main__":
    print("Fetching AWS costs per account...")
    cost_data = get_aws_costs()
    print("Writing data to CSV...")
    write_to_csv(cost_data)
    print("Task completed.")
