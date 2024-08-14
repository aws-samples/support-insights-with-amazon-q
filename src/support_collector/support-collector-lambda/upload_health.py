import json
import datetime
from collections import defaultdict
import logging
import boto3


# Set up logging
logging.basicConfig(level=logging.INFO)

session = boto3.Session()


class DatetimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)


def save_to_s3(events_by_account, bucket_name):
    region = session.region_name
    s3 = session.client("s3", region_name=region)

    print(f"The Health events are being uploaded to S3 bucket {bucket_name}...")
    for account_id, account_events in events_by_account.items():
        for event_dict in account_events:
            event = event_dict["event"]

            # Clean ARN for use as filename
            arn = event["arn"].split(":")[-1].replace("/", "_")
            event_json = json.dumps(
                event, cls=DatetimeEncoder, ensure_ascii=False
            ).encode("utf-8")

            # Extracting start time for partitioning in S3
            dt = event["startTime"]
            start_date = f"{dt.year}/{dt.month}"

            # Construct the file key using account_id, date, and arn
            file_key = f"health/{account_id}/{start_date}/{arn}.json"
            s3.put_object(Bucket=bucket_name, Key=file_key, Body=event_json)

            print(f"Uploaded {file_key}")
    print("Health upload done!")


def assume_role(account_id, role_name):
    sts_client = session.client("sts")
    response = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/{role_name}",
        RoleSessionName="HealthEventSession",
    )
    return response["Credentials"]


def list_health_events(past_no_of_days):
    health_client = session.client(
        "health",
        region_name="us-east-1",  # AWS Health API must be called from us-east-1
    )
    health_events = []
    events_paginator = health_client.get_paginator("describe_events")

    # Describe events using the same default filters as the Personal Health Dashboard (PHD).
    events_pages = events_paginator.paginate(
        filter={
            "startTimes": [
                {
                    "from": datetime.datetime.now()
                    - datetime.timedelta(days=past_no_of_days)
                },
                {"to": datetime.datetime.now()},
            ],
            "eventStatusCodes": ["open", "upcoming", "closed"],
        }
    )

    event_arns = []
    for events_page in events_pages:
        for event in events_page["events"]:
            event_arns.append(event["arn"])
            health_events.append(event)  # Collecting basic event data

    # Fetching detailed information about each event in chunks of 10 - there is a limit of 10
    while event_arns:
        arns_chunk = event_arns[:10]
        event_arns = event_arns[10:]
        details_response = health_client.describe_event_details(eventArns=arns_chunk)
        for detail in details_response["successfulSet"]:
            # Update each event with its detailed description
            for event in health_events:
                if event["arn"] == detail["event"]["arn"]:
                    event.update(
                        {"details": detail["eventDescription"]["latestDescription"]}
                    )

    return health_events


def upload_health_events_to_s3(bucket_name, past_no_of_days, account_id):
    org_client = session.client("organizations")
    events_by_account = defaultdict(list)

    events = list_health_events(past_no_of_days)

    for event in events:
        event_dict = {"account_id": account_id, "event": event}
        events_by_account[account_id].append(event_dict)

    save_to_s3(events_by_account, bucket_name)
