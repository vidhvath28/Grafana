import boto3
import csv
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def get_gpu_ec2_cost():
    # AWS Cost Explorer client setup
    client = boto3.client(
        "ce",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION"),
    )

    # Set the time period for the last 7 days
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)

    # Define the instance types that have GPU support (e.g., p3, p4, g4, g5)
    instance_types_with_gpu = ["p3", "p4", "g4", "g5"]

    # Query AWS Cost Explorer for EC2 costs related to GPU instances
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

    # Prepare the CSV data
    rows = [["Account", "Date", "Cost"]]
    for result in response["ResultsByTime"]:
        date = result["TimePeriod"]["Start"]
        for group in result["Groups"]:
            account = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            rows.append([account, date, cost])

    # Save the data into a CSV file
    filename = "aws-gpu-cost-per-account.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return filename

if __name__ == "__main__":
    print("Fetching AWS Cost for EC2 GPU Instances...")
    file_path = get_gpu_ec2_cost()
    print(f"File saved: {file_path}")
