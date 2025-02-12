import boto3
import csv
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_aws_cost_per_service():
    client = boto3.client(
        "ce",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION"),
    )

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)

    response = client.get_cost_and_usage(
        TimePeriod={"Start": str(start_date), "End": str(end_date)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    rows = [["Service", "Date", "Cost"]]
    for result in response["ResultsByTime"]:
        date = result["TimePeriod"]["Start"]
        for group in result["Groups"]:
            service = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            rows.append([service, date, cost])

    filename = "aws-cost-per-service.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return filename

if __name__ == "__main__":
    print("Fetching AWS Cost per Service...")
    file_path = get_aws_cost_per_service()
    print(f"File saved: {file_path}")
