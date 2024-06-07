import boto3
import time
import os

def deploy_lambda_function(bucket_name, master_account_bucket_name):
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
            'ParameterKey': 'MasterAccountBucketName',
            'ParameterValue': master_account_bucket_name
        },
        {
            'ParameterKey': 'MemberBucketName',
            'ParameterValue': bucket_name
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
    parser.add_argument('--bucket-name', required=True, help='Name of the S3 bucket containing the Lambda package')
    parser.add_argument('--master-account-bucket-name', required=True, help='Name of the S3 bucket in the master account')
    args = parser.parse_args()

    deploy_lambda_function(args.bucket_name, args.master_account_bucket_name)