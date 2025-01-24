import os
import csv
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

# Initialize AWS Boto3 Client (e.g., Cost Explorer)
ce_client = boto3.client(
    "ce",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

# Get AWS cost data per service
def get_aws_cost_per_service():
    today = datetime.utcnow().date()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    response = ce_client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    return response.get("ResultsByTime", [])

# Write data to CSV file
def write_to_csv(data):
    today = datetime.utcnow()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    # Create directory structure
    folder_path = os.path.join("AWS", year, month, day)
    os.makedirs(folder_path, exist_ok=True)

    # File path for the CSV file
    file_path = os.path.join(folder_path, "aws-cost-per-service.csv")

    # Write data to CSV
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Service", "Cost (USD)"])
        for item in data:
            date = item["TimePeriod"]["Start"]
            for group in item["Groups"]:
                service = group["Keys"][0]
                cost = group["Metrics"]["UnblendedCost"]["Amount"]
                writer.writerow([date, service, cost])

    print(f"CSV file saved to {os.path.abspath(file_path)}")

# Main function
if __name__ == "__main__":
    print("Fetching AWS costs per service...")
    cost_data = get_aws_cost_per_service()

    print("Writing data to CSV...")
    write_to_csv(cost_data)

    print("Task completed.")
