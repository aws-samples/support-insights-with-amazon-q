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

    q_app_id = resource_properties['QApplicationId']
    q_index_id = resource_properties['QIndexId']
    q_datasource_bucket = resource_properties['QDataSourceS3Bucket']
    q_s3_role_arn = resource_properties['QS3IAMRole']

    # Create the datasource
    q_datasource_response = create_qbusiness_data_source(region=region,
                                                         q_app_id=q_app_id,
                                                         q_index_id=q_index_id,
                                                         q_s3_role_arn=q_s3_role_arn,
                                                         q_datasource_bucket=q_datasource_bucket)

    # Update outputs
    response = {
        'dataSourceArn': q_datasource_response.get('dataSourceArn'),
        'dataSourceId': q_datasource_response.get('dataSourceId')
    }
    helper.Data.update(response)
    logger.info(helper.Data)

    return json.dumps(response)


@helper.update
def update(event, context):
    logger.info("Got Update")
    # If the update resulted in a new resource being created, return an id for the new resource. CloudFormation will send a delete event with the old id when stack update completes


@helper.delete
def delete(event, context):
    logger.info('Deleting datasource...')
    logger.info(event)


def create_qbusiness_data_source(region, q_app_id, q_index_id, q_s3_role_arn, q_datasource_bucket):
    client = boto3.client('qbusiness', region_name=region)
    time_stamp = int(time.time())
    data_source_name = f'support-q-data-source-{time_stamp}'

    configuration = {
        "additionalProperties": {
            "exclusionPatterns": [],
            "inclusionPatterns": [],
            "inclusionPrefixes": [],
            "maxFileSizeInMegaBytes": "50",
        },
        "type": "S3",
        "version": "1.0.0",
        "syncMode": "FORCED_FULL_CRAWL",
        "enableIdentityCrawler": "false",
        "connectionConfiguration": {
            "repositoryEndpointMetadata": {
                "BucketName": q_datasource_bucket
            }
        },
        "repositoryConfigurations": {
            "document": {
                "fieldMappings": [
                    {
                        "indexFieldName": "s3_document_id",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "s3_document_id"
                    }
                ]
            }
        },
    }
    create_response = client.create_data_source(
        applicationId=q_app_id,
        indexId=q_index_id,
        roleArn=q_s3_role_arn,
        syncSchedule='cron(0 0 * * ? *)',
        displayName=data_source_name,
        configuration=configuration
    )
    logger.info(create_response)
    return create_response
