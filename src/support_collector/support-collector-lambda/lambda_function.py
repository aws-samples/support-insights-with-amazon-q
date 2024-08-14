import importlib

def lambda_handler(event, context):
    account_id = context.invoked_function_arn.split(":")[4]

    # Get PAST_NO_OF_DAYS from event parameters
    past_no_of_days = event.get("past_no_of_days")
    if past_no_of_days is None:
        return {
            "statusCode": 400,
            "body": "Error: PAST_NO_OF_DAYS parameter is missing.",
        }

    bucket_name = event.get("bucket_name")
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
