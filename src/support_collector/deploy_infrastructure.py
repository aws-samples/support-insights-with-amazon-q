from datetime import datetime
import json
import argparse
import boto3

import deploy_stackset

STACKSET_PREFIX = "support-insights"
STACKSET_HISTORICAL_PREFIX = "support-insights-historical-data"
TEMPLATE_FILE = "member_account_resources.yaml"
TEMPLATE_HISTORICAL_SYNC_FILE = "member_account_historical_data_sync.yaml"
LAMBDA_ROLE_NAME = "SupportInsightsLambdaRole-9c8794ee-f9e8"
OUTPUT_DATA_COLLECTOR_BUCKET_POLICY = "output_bucket_policy.json"

org_client = boto3.client("organizations")


def get_ou_ids():
    response = org_client.list_roots()
    root_id = response["Roots"][0]["Id"]
    paginator = org_client.get_paginator("list_organizational_units_for_parent")

    ou_ids = []
    for page in paginator.paginate(ParentId=root_id):
        for ou in page["OrganizationalUnits"]:
            ou_ids.append(ou["Id"])

    return ou_ids


def get_all_ou_ids(ou_ids):
    all_ou_ids = get_ou_ids()

    user_input_ou_ids = ou_ids.split(",")

    valid_ou_ids = []
    for ou_id in user_input_ou_ids:
        if ou_id.strip() in all_ou_ids:
            valid_ou_ids.append(ou_id.strip())
        else:
            print(f"OU ID {ou_id.strip()} is not valid.")

    return valid_ou_ids


def list_accounts_for_parent(parent_id):
    accounts = []
    paginator = org_client.get_paginator("list_accounts_for_parent")
    page_iterator = paginator.paginate(ParentId=parent_id)

    for page in page_iterator:
        accounts.extend(page["Accounts"])

    return accounts


def generate_bucket_policy(management_account_bucket_name, valid_ou_ids):
    accounts_in_ous = []
    for ou_id in valid_ou_ids:
        accounts = list_accounts_for_parent(parent_id=ou_id)
        accounts_in_ous.extend(accounts)

    principal_arns = []
    for account in accounts_in_ous:
        account_id = account["Id"]
        principal_arns.append(f"arn:aws:iam::{account_id}:role/{LAMBDA_ROLE_NAME}")

    org_id = org_client.describe_organization()["Organization"]["Id"]
    org_root_id = org_client.list_roots()["Roots"][0]["Id"]

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": principal_arns},
                "Action": ["s3:GetObject", "s3:PutObject", "s3:PutObjectAcl"],
                "Resource": f"arn:aws:s3:::{management_account_bucket_name}/*",
                "Condition": {
                    "ForAnyValue:StringLike": {
                        "aws:PrincipalOrgPaths": [
                            f"{org_id}/{org_root_id}/{ou_id}/*"
                            for ou_id in valid_ou_ids
                        ]
                    }
                },
            }
        ],
    }

    with open(
        OUTPUT_DATA_COLLECTOR_BUCKET_POLICY, "w", encoding="utf-8"
    ) as policy_file:
        json.dump(policy, policy_file, indent=4)
    print(
        f"Bucket policy JSON saved to {OUTPUT_DATA_COLLECTOR_BUCKET_POLICY} for bucket {management_account_bucket_name}"
    )
    return policy


def s3_bucket_exists(bucket_name):
    s3_client = boto3.client("s3")
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise e


def update_bucket_policy(bucket_name, policy):
    s3_client = boto3.client("s3")
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))


def deploy_support_collector_resources(
    data_bucket_name, region, valid_ou_ids, stackset_name
):

    stack_params = [
        {"ParameterKey": "LambdaRoleName", "ParameterValue": LAMBDA_ROLE_NAME},
        {
            "ParameterKey": "SupportDataManagementBucketName",
            "ParameterValue": data_bucket_name,
        },
    ]
    stackset_name_result, operation_id = (
        deploy_stackset.deploy_stackset_member_accounts(
            stackset_name,
            TEMPLATE_FILE,
            region,
            stack_params,
            valid_ou_ids,
        )
    )
    return stackset_name_result, operation_id


def deploy_support_collector_historic_sync_rule(
    data_bucket_name, region, valid_ou_ids, stackset_name
):
    stack_params = [
        {
            "ParameterKey": "SupportDataManagementBucketName",
            "ParameterValue": data_bucket_name,
        }
    ]

    # after all stack are created, the policy on the bucket is set so we can deploy a stackset to run one time historical sync
    stackset_name_result, operation_id = (
        deploy_stackset.deploy_stackset_member_accounts(
            stackset_name,
            TEMPLATE_HISTORICAL_SYNC_FILE,
            region,
            stack_params,
            valid_ou_ids,
        )
    )
    return stackset_name_result, operation_id


def main(data_bucket_name, ou_ids, overwrite_data_bucket_policy):
    if not s3_bucket_exists(bucket_name=data_bucket_name):
        print(f"Bucket {data_bucket_name} does not exist. Exiting...")
        return

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stackset_name = f"{STACKSET_PREFIX}-{timestamp}"

    region = boto3.Session().region_name
    valid_ou_ids = get_all_ou_ids(ou_ids)
    if not valid_ou_ids:
        print("No valid OU IDs provided. Exiting...")
        return

    print("Creating CloudFormation stack for member account(s)...")
    stackset_name_result, operation_id = deploy_support_collector_resources(
        data_bucket_name=data_bucket_name,
        region=region,
        valid_ou_ids=valid_ou_ids,
        stackset_name=stackset_name,
    )

    print(
        f"Now waiting for the CloudFormation StackSets {stackset_name_result} to complete... Please do not exit this shell."
    )
    deployment_succeeded = deploy_stackset.wait_for_stackset_creation(
        stackset_name_result, operation_id
    )

    if deployment_succeeded:
        print("Generating policy for the data bucket...")
        policy = generate_bucket_policy(data_bucket_name, valid_ou_ids)

        if overwrite_data_bucket_policy:
            print("StackSet completed. Updating data bucket policy...")
            update_bucket_policy(data_bucket_name, policy)
            print("Data bucket policy updated.")
        else:
            print("Not updating the data bucket policy...")

        print(
            "Deploying a stack set with a one time rule to trigger a sync of the historical support data..."
        )
        stackset_name = f"{STACKSET_HISTORICAL_PREFIX}-{timestamp}"
        stackset_name_result, operation_id = (
            deploy_support_collector_historic_sync_rule(
                data_bucket_name=data_bucket_name,
                region=region,
                valid_ou_ids=valid_ou_ids,
                stackset_name=stackset_name,
            )
        )

        print(
            f"Now waiting for the CloudFormation StackSets {stackset_name_result} to complete... Please do not exit this shell."
        )
        if deploy_stackset.wait_for_stackset_creation(
            stackset_name_result, operation_id
        ):
            print("StackSet completed! All done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-bucket", dest="data_bucket", help="Data bucket name", required=True
    )
    parser.add_argument(
        "--ou-ids",
        dest="ou_ids",
        help="Organizational Units to deploy to (ie: ou-xxxxxxxxxx1,ou-xxxxxxxxxx2)",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--overwrite-data-bucket-policy",
        dest="overwrite_data_bucket_policy",
        help="Overwrite the data bucket policy",
        action=argparse.BooleanOptionalAction,
        required=False,
    )
    args = parser.parse_args()

    main(
        data_bucket_name=args.data_bucket,
        ou_ids=args.ou_ids,
        overwrite_data_bucket_policy=args.overwrite_data_bucket_policy,
    )
