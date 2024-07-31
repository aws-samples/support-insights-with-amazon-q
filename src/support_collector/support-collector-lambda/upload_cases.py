import json
import datetime
from collections import defaultdict
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

session = boto3.Session()


def save_to_s3(cases_by_account, bucket_name):
    region = session.region_name
    s3 = session.client("s3", region_name=region)
    current_date = datetime.datetime.now().strftime(
        "%Y-%m-%d"
    )  # Format the date as YYYY-MM-DD

    print(f"The Support cases are being uploaded to S3 bucket {bucket_name}...")
    for account_id, cases in cases_by_account.items():
        for case in cases:
            case_id = case["case"]["displayId"]  # Extracting case ID for filename
            case_json = json.dumps(case, ensure_ascii=False).encode(
                "utf-8"
            )  # Serialize case data to JSON with UTF-8 encoding
            file_key = f"support-cases/{account_id}/{current_date}/{case_id}.json"
            s3.put_object(Bucket=bucket_name, Key=file_key, Body=case_json)
            print(f"Uploaded {file_key}")
    print("Support cases upload done!")


def get_support_cases(credentials):
    support_client = session.client(
        "support",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )
    cases = []
    paginator = support_client.get_paginator("describe_cases")
    for page in paginator.paginate():
        cases.extend(page["cases"])
    return cases


def describe_cases(after_time, resolved):
    """
    Describe support cases over a period of time, optionally filtering
    by status.

    :param after_time: The start time to include for cases.
    :param before_time: The end time to include for cases.
    :param resolved: True to include resolved cases in the results,
        otherwise results are open cases.
    :return: The final status of the case.
    """
    cases = []
    try:
        support_client = session.client("support")
        paginator = support_client.get_paginator("describe_cases")
        for page in paginator.paginate(
            afterTime=after_time,
            includeResolvedCases=resolved,
            includeCommunications=True,
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
            logger.error(
                "Couldn't describe cases. Error Code: %s, Error Message: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
    return cases


def list_all_cases(days):
    include_communications = True
    end_date = datetime.datetime.utcnow().date()
    start_date = end_date - datetime.timedelta(days)
    start_time = str(start_date)
    all_cases = describe_cases(start_time, include_communications)

    return all_cases


def create_support_case_context(case, account_id):
    display_id = case["displayId"]  # Use the correct key for the case ID
    time_created = case["timeCreated"]
    case_status = case["status"]
    service_code = case["serviceCode"]
    severity_code = case["severityCode"]

    # Create the context for search
    support_case_context = f"This is an AWS support case ID {display_id} in account ID {account_id}. The case was opened on {time_created}; It is a {case_status} case related to the {service_code} service with {severity_code} severity. The details are on the body fields of the JSON."

    return support_case_context


def upload_all_cases_to_s3(bucket_name, past_no_of_days, account_id):
    cases_by_account = defaultdict(list)
    cases = list_all_cases(past_no_of_days)

    for case in cases:
        case_dict = {
            "account_id": account_id,
            "case": case,
            "support_case_context": create_support_case_context(
                case, account_id
            ),  # Add the custom field
        }
        cases_by_account[account_id].append(case_dict)

    save_to_s3(cases_by_account, bucket_name)
