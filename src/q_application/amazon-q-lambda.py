# https://aws.amazon.com/blogs/infrastructure-and-automation/aws-cloudformation-custom-resource-creation-with-python-aws-lambda-and-crhelper/

import os
import logging
import time
import boto3
import json
from crhelper import CfnResource

logger = logging.getLogger(__name__)

helper = CfnResource(
    json_logging=False,
    log_level='DEBUG',
    boto_level='CRITICAL')


def lambda_handler(event, context):
    helper(event, context)


@helper.create
def create(event, context):
    # Fetch parameters
    resource_properties = event['ResourceProperties']
    logger.info(resource_properties)
    region = resource_properties['Region']
    q_app_role = resource_properties['QAppIAMRole']
    logger.info(q_app_role)

    # Create the Q Business Application
    q_app = create_qbusiness_application(region, q_app_role)

    # Update outputs
    helper.Data.update(q_app)
    logger.info(helper.Data)

    return json.dumps(q_app)


@helper.update
def update(event, context):
    logger.info("Got Update")
    # If the update resulted in a new resource being created, return an id for the new resource. CloudFormation will send a delete event with the old id when stack update completes


@helper.delete
def delete(event, context):
    logger.info('Deleting application...')
    logger.info(event)

    region = os.environ.get('AWS_REGION')
    resource_ids = json.loads(event['PhysicalResourceId'])
    app_id = resource_ids["ApplicationId"]

    client = boto3.client('qbusiness', region_name=region)
    client.delete_application(applicationId=app_id)

    logger.info("Resource Deleted")


def create_qbusiness_application(region, role_arn):
    client = boto3.client('qbusiness', region_name=region)
    time_stamp = int(time.time())
    app_name = f'support-q-app-{time_stamp}'
    create_response = client.create_application(
        roleArn=role_arn,
        displayName=app_name
    )
    logger.info(f'Q Application Creation Response: {create_response}')
    q_app_id = create_response.get('applicationId')

    index_name = f'support-q-app-{time_stamp}'
    create_index_response = client.create_index(
        applicationId=q_app_id,
        displayName=index_name
    )
    logger.info(f'Q Index Creation Response: {create_index_response}')
    index_id = create_index_response.get('indexId')

    retriever_name = f'support-q-app-{time_stamp}'
    create_retriever_response = client.create_retriever(
        applicationId=q_app_id,
        displayName=retriever_name,
        configuration={
            'nativeIndexConfiguration': {
                'indexId': index_id
            }
        },
        type='NATIVE_INDEX'
    )
    logger.info(f'Q Index Retriever Response: {create_retriever_response}')
    retriever_id = create_retriever_response.get('retrieverId')

    create_web_experience_response = client.create_web_experience(
        applicationId=q_app_id,
    )
    web_experience_id = create_web_experience_response.get('webExperienceId')

    return {'ApplicationId': q_app_id, 'IndexId': index_id, 'RetrieverId': retriever_id, 'WebExperienceId': web_experience_id}
