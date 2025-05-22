import os
import boto3

def deploy_lambda_function(resource_bucket_name, support_data_bucket_name):
    # Create CloudFormation client
    cf_client = boto3.client('cloudformation')

    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))

    # Construct the absolute path to the CloudFormation template
    template_path = os.path.join(project_root, 'individual-account-deployments', 'member_account_resources.yaml')

    # Read the CloudFormation template
    with open(template_path, 'r', encoding='utf-8') as template_file:
        template_body = template_file.read()

    # Generate a unique role name
    role_name = 'SupportInsightsLambdaRole-9c8794ee-f9e8'

    # Create the CloudFormation stack
    stack_name = 'SupportInsightsLambdaStack'
    params = [
        {
            'ParameterKey': 'LambdaRoleName',
            'ParameterValue': role_name
        },
        {
            'ParameterKey': 'SupportDataBucketName',
            'ParameterValue': support_data_bucket_name
        },
        {
            'ParameterKey': 'ResourceBucketName',
            'ParameterValue': resource_bucket_name
        }
    ]

    response = cf_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=params,
        Capabilities=['CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']
    )

    print(f"Creating CloudFormation stack '{stack_name}'...")

    # Wait for stack creation to complete
    waiter = cf_client.get_waiter('stack_create_complete')
    waiter.wait(StackName=stack_name)

    print(f"CloudFormation stack '{stack_name}' created successfully.")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--resource_bucket_name', required=True, help='Name of the S3 bucket containing the Lambda package')
    parser.add_argument('--support_data_bucket_name', required=True, help='Name of the S3 bucket containing support data')
    args = parser.parse_args()

    deploy_lambda_function(args.resource_bucket_name, args.support_data_bucket_name)
    