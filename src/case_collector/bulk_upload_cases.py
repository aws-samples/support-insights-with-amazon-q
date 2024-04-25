import boto3
import json
import sys
import datetime
from datetime import timedelta
from collections import defaultdict
from botocore.exceptions import ClientError
from boto3.session import Session

# Accept bucket name from command line arguments
if len(sys.argv) < 2:
    print("Usage: python bulk_upload_cases.py <BUCKET_NAME>")
    sys.exit(1)

BUCKET_NAME = sys.argv[1]
PAST_NO_OF_DAYS = 180
EXCLUDE_ACCOUNTS = []
MEMBER_ACCOUNT_ROLE_NAME = 'CentralUserSupportCaseInsightsRole'
PROFILE_NAME = 'support'

session = Session(profile_name=PROFILE_NAME)

def save_to_s3(cases_by_account):
  region = session.region_name

  s3 = session.client('s3', region_name=region)
  
  # Check if bucket exists and create it if not
  try:
    s3.head_bucket(Bucket=BUCKET_NAME) 
  except ClientError:
    location = {'LocationConstraint': region}
    s3.create_bucket(Bucket=BUCKET_NAME, CreateBucketConfiguration=location)

  print(f"The Support cases are being uploaded to S3 bucket {BUCKET_NAME}...")
  for account_id, account_cases in cases_by_account.items():
    account_cases_json = json.dumps(account_cases)  
    s3.put_object(
      Bucket= BUCKET_NAME,
      Key=f"{account_id}.json", 
      Body=account_cases_json
    )
    print(f"{account_id}.json")
  print("Done!")


def assume_role(account_id, role_name):
    sts_client = session.client('sts')
    response = sts_client.assume_role(
        RoleArn=f'arn:aws:iam::{account_id}:role/{role_name}',
        RoleSessionName='SupportCaseSession'
    )
    return response['Credentials']
    
def get_support_cases(credentials):
    support_client = session.client(
        'support',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )
    cases = []
    paginator = support_client.get_paginator('describe_cases')
    for page in paginator.paginate():
        cases.extend(page['cases'])
    return cases
    
def describe_cases(credentials, after_time, resolved):
    """
    Describe support cases over a period of time, optionally filtering
    by status.

    :param after_time: The start time to include for cases.
    :param before_time: The end time to include for cases.
    :param resolved: True to include resolved cases in the results,
        otherwise results are open cases.
    :return: The final status of the case.
    """
    try:
        support_client = session.client(
            'support',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
        )
        cases = []
        paginator = support_client.get_paginator("describe_cases")
        for page in paginator.paginate(
            afterTime=after_time,
            includeResolvedCases=resolved,
            includeCommunications = True,
            language="en",
        ):
            cases += page["cases"]
    except ClientError as err:
        if err.response["Error"]["Code"] == "SubscriptionRequiredException":
            logger.info(
                "You must have a Business, Enterprise On-Ramp, or Enterprise Support "
                "plan to use the AWS Support API. \n\tPlease upgrade your subscription to run these "
                "examples."
            )
        else:
            print(err.response["Error"]["Message"])
            logger.error(
                "Couldn't describe cases. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
    else:
        return cases
        
def list_all_cases(days, credentials):
  
  includeCommunications=True
  end_date = datetime.datetime.utcnow().date()
  start_date = end_date - datetime.timedelta(days)
  start_time = str(start_date)
  all_cases = describe_cases(credentials, start_time, includeCommunications)
  
  return all_cases


def upload_all_cases_across_member_accounts_to_s3():
    org_client = session.client('organizations')
    cases_by_account = defaultdict(list)
    
    for account in org_client.list_accounts()['Accounts']:
        account_id = account['Id']
        if account_id not in EXCLUDE_ACCOUNTS:
            credentials = assume_role(account_id, MEMBER_ACCOUNT_ROLE_NAME)
            cases = list_all_cases(PAST_NO_OF_DAYS, credentials)

            for case in cases:
              case_dict = {
                "account_id": account_id,
                "case": case 
              }
              cases_by_account[account_id].append(case_dict)
                         
    save_to_s3(cases_by_account)


upload_all_cases_across_member_accounts_to_s3()
