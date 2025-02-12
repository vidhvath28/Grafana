import boto3
import csv
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json  # Added for debugging

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

    # GPU-enabled EC2 instance types
    instance_types_with_gpu = [
        "g5.12xlarge", "g5.2xlarge", "g5.4xlarge",
        "ml.g5.2xlarge-Hosting", "ml.g5.2xlarge-Notebook",
        "g4dn.2xlarge", "g4dn.4xlarge", "g4dn.xlarge",
        "p4d.24xlarge"
    ]

    # Query AWS Cost Explorer for EC2 GPU instance costs
    response = client.get_cost_and_usage(
        TimePeriod={"Start": str(start_date), "End": str(end_date)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "And": [
                {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
                {"Dimensions": {"Key": "INSTANCE_TYPE", "Values": instance_types_with_gpu}}
            ]
        },
        GroupBy=[
            {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
            {"Type": "DIMENSION", "Key": "INSTANCE_TYPE"}
        ],
    )

    # Print full API response for debugging
    print("AWS Response:", json.dumps(response, indent=4))

    # Prepare the CSV data
    rows = [["Account", "Date", "Instance Type", "Cost"]]
    for result in response["ResultsByTime"]:
        date = result["TimePeriod"]["Start"]
        for group in result["Groups"]:
            account = group["Keys"][0]  # AWS Account ID
            instance_type = group["Keys"][1]  # Instance Type
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            rows.append([account, date, instance_type, cost])

    # Save the data into a CSV file
    filename = "aws-gpu-cost-per-instance.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return filename

if __name__ == "__main__":
    print("Fetching AWS Cost for Specific EC2 GPU Instances...")
    file_path = get_gpu_ec2_cost()
    print(f"File saved: {file_path}")
