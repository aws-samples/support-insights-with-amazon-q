import json
from collections import defaultdict
import boto3

session = boto3.Session()

# Load trustedadvisorchecksinfo.json
with open("ta_checks_info.json", "r", encoding="utf-8") as f:
    checks_info = json.load(f)

# Create a dictionary for easy lookup
checks_info_dict = {
    check["checkId"]: {"name": check["name"], "description": check["description"]}
    for check in checks_info
}


def save_to_s3(recommendations_by_account, bucket_name):
    region = session.region_name
    s3 = session.client("s3", region_name=region)

    print(f"The TA recommendations are being uploaded to S3 bucket {bucket_name}...")
    for account_id, recommendations in recommendations_by_account.items():
        for recommendation in recommendations:
            status = recommendation["recommendation"]["status"].lower()
            # Filter for warning or error status
            if status in [
                "warning",
                "error",
                "yellow",
                "red",
            ]:
                # Extract the checkId from the recommendation
                check_id = recommendation["recommendation"]["checkId"]
                # Get the description from the checks_info_dict
                description = checks_info_dict.get(check_id, {}).get(
                    "description", "No description provided"
                )
                # Update the recommendation with name and modified description
                recommendation["recommendation"][
                    "description"
                ] = f"The Trusted Advisor (TA) recommendation is for AWS account Id {account_id} that has TA status as '{status}'. This status {status} indicates the account owner should take action on the resources stated here as per this recommendation. The recommendation is as follows: {description}"
                recommendation_json = json.dumps(
                    recommendation, ensure_ascii=False
                ).encode("utf-8")
                # Construct the file key using account_id, date, and checkId
                file_key = f"ta/{account_id}/{check_id}.json"
                s3.put_object(
                    Bucket=bucket_name, Key=file_key, Body=recommendation_json
                )
                print(f"Uploaded {file_key}")
    print("TA upload done!")


def get_ta_recommendations():
    support_client = session.client("support")
    recommendations = []

    # Call describe_trusted_advisor_checks directly
    checks = support_client.describe_trusted_advisor_checks(language="en")["checks"]

    for check in checks:
        result = support_client.describe_trusted_advisor_check_result(
            checkId=check["id"], language="en"
        )
        recommendations.append(result["result"])

    return recommendations


def upload_all_recommendations_to_s3(bucket_name, account_id):

    recommendations_by_account = defaultdict(list)

    recommendations = get_ta_recommendations()
    print(f"Finding TA recommendations in {account_id}")
    for recommendation in recommendations:
        recommendation_dict = {
            "account_id": account_id,
            "recommendation": recommendation,
        }
        recommendations_by_account[account_id].append(recommendation_dict)

    save_to_s3(recommendations_by_account, bucket_name)
