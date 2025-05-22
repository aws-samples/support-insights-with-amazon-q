import importlib
import os

def upload_case_on_case_event(event, account_id):
    try:
        # Get bucket name from environment variable for event-based triggers
        bucket_name = os.environ['S3_BUCKET_NAME']

        # Import the upload_cases module
        bulk_upload_cases = importlib.import_module("upload_cases")

        case_id = event['detail']['display-id']
        event_name = event['detail']['event-name']

        print(f"Processing support case event: {event_name} for case {case_id}")
        print(f"Using bucket: {bucket_name}")

        # Upload the specific case to S3
        bulk_upload_cases.upload_case_to_s3(
            bucket_name=bucket_name,
            account_id=account_id,
            case_id=case_id
        )

        return {
            "statusCode": 200,
            "body": f"Successfully processed {event_name} event for case {case_id}"
        }

    except KeyError as e:
        error_msg = f"Missing required field: {str(e)}"
        print(error_msg)
        return {
            "statusCode": 500,
            "body": error_msg
        }
    except Exception as e:
        error_msg = f"Error processing support case event: {str(e)}"
        print(error_msg)
        return {
            "statusCode": 500,
            "body": error_msg
        }


def upload_case_on_scheduler_run(event, account_id):
    # Handle scheduled runs (using event parameters)
    bucket_name = event.get("bucket_name")
    if not bucket_name:
        return {
            "statusCode": 400,
            "body": "Error: bucket_name parameter is missing.",
        }

    past_no_of_days = event.get("past_no_of_days")
    if past_no_of_days is None:
        return {
            "statusCode": 400,
            "body": "Error: PAST_NO_OF_DAYS parameter is missing.",
        }

    run_case = event.get("case", False)
    run_health = event.get("health", False)
    run_ta = event.get("ta", False)

    # Check if any script flags are provided
    if not (run_case or run_health or run_ta):
        return {
            "statusCode": 400,
            "body": "Error: No scripts specified to run. Please provide at least one flag ('case', 'health', 'ta').",
        }

    # Check each flag and run the corresponding script
    response_messages = []

    if run_case:
        bulk_upload_cases = importlib.import_module("upload_cases")
        response_messages.append("Searching AWS Support Cases..")
        bulk_upload_cases.upload_all_cases_to_s3(
            bucket_name, past_no_of_days, account_id
        )
        response_messages.append("Cases uploaded successfully.")

    if run_ta:
        bulk_upload_ta = importlib.import_module("upload_ta")
        response_messages.append("Searching AWS Trusted Advisor recommendations..")
        bulk_upload_ta.upload_all_recommendations_to_s3(bucket_name, account_id)
        response_messages.append(
            "Trusted Advisor recommendations uploaded successfully."
        )

    if run_health:
        bulk_upload_health = importlib.import_module("upload_health")
        response_messages.append("Searching AWS Health notifications..")
        bulk_upload_health.upload_health_events_to_s3(
            bucket_name, past_no_of_days, account_id
        )
        response_messages.append("Health events uploaded successfully.")

    return {"statusCode": 200, "body": "\n".join(response_messages)}

def lambda_handler(event, context):
    account_id = context.invoked_function_arn.split(":")[4]

    # Check if this is a Support Case Update event
    if event.get('source') == 'aws.support' and event.get('detail-type') == 'Support Case Update':
        return upload_case_on_case_event(event, account_id)

    return upload_case_on_scheduler_run(event, account_id)
