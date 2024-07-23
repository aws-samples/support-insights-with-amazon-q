import boto3
import deploy_stackset
import sys
from datetime import datetime
import json

STACKSET_PREFIX = 'support-insights-stackset'
TEMPLATE_FILE = 'member_account_resources.yaml'
LAMBDA_ROLE_NAME = 'SupportInsightsLambdaRole-9c8794ee-f9e8'
OUTPUT_DATA_COLLECTOR_BUCKET_POLICY = 'output_bucket_policy.json'

org_client = boto3.client('organizations')

def get_ou_ids():
    response = org_client.list_roots()
    root_id = response['Roots'][0]['Id']
    paginator = org_client.get_paginator('list_organizational_units_for_parent')
    
    ou_ids = []
    for page in paginator.paginate(ParentId=root_id):
        for ou in page['OrganizationalUnits']:
            ou_ids.append(ou['Id'])
    
    return ou_ids

def get_all_ou_ids():
    all_ou_ids = get_ou_ids()
    
    user_input_ou_ids = sys.argv[3].split(',')
    
    valid_ou_ids = []
    for ou_id in user_input_ou_ids:
        if ou_id.strip() in all_ou_ids:
            valid_ou_ids.append(ou_id.strip())
        else:
            print(f"OU ID {ou_id.strip()} is not valid.")
    
    if valid_ou_ids:
        return valid_ou_ids
    else:
        print("No valid OU IDs provided. Exiting...")
        exit()

def deploy_stackset_module(stackset_name, region, management_account_bucket_name, resource_management_bucket_name, valid_ou_ids):
    deploy_stackset.deploy_stackset_member_accounts(stackset_name, TEMPLATE_FILE, region, management_account_bucket_name, resource_management_bucket_name, LAMBDA_ROLE_NAME, valid_ou_ids)

def generate_bucket_policy(management_account_bucket_name, valid_ou_ids):
    accounts_in_ous = []
    for ou_id in valid_ou_ids:
        accounts = org_client.list_accounts_for_parent(ParentId=ou_id)['Accounts']
        accounts_in_ous.extend(accounts)

    principal_arns = []
    for account in accounts_in_ous:
        account_id = account['Id']
        principal_arns.append(f"arn:aws:iam::{account_id}:role/{LAMBDA_ROLE_NAME}")

    org_id = org_client.describe_organization()['Organization']['Id']
    org_root_id = org_client.list_roots()['Roots'][0]['Id']

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": principal_arns
                },
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:PutObjectAcl"
                ],
                "Resource": f"arn:aws:s3:::{management_account_bucket_name}/*",
                "Condition": {
                    "ForAnyValue:StringLike": {
                        "aws:PrincipalOrgPaths": [f"{org_id}/{org_root_id}/{ou_id}/*" for ou_id in valid_ou_ids]
                    }
                }
            }
        ]
    }

    with open(OUTPUT_DATA_COLLECTOR_BUCKET_POLICY, 'w', encoding='utf-8') as policy_file:
        json.dump(policy, policy_file, indent=4)
    print(f"Bucket policy JSON saved to {OUTPUT_DATA_COLLECTOR_BUCKET_POLICY} for bucket {management_account_bucket_name}")


def main(bucket_name, resource_bucket_name):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stackset_name = f"{STACKSET_PREFIX}-{timestamp}"
    region = boto3.Session().region_name
    valid_ou_ids = get_all_ou_ids()

    print("Creating CloudFormation stack for member account(s)...")
    deploy_stackset_module(
        stackset_name=stackset_name,
        region=region,
        management_account_bucket_name=bucket_name,
        resource_management_bucket_name=resource_bucket_name,
        valid_ou_ids=valid_ou_ids
    )

    print("Please check the status in CloudFormation StackSets.")
    generate_bucket_policy(bucket_name, valid_ou_ids)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Error: Bucket names or OU IDs not provided.")
        sys.exit(1)

    bucket_name = sys.argv[1]
    resource_bucket_name = sys.argv[2]
    main(bucket_name, resource_bucket_name)