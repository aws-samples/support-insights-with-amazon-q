import boto3

def deploy_stackset_member_accounts(stackset_name, template_file, region, master_account_bucket_name, resource_master_bucket_name, role_name, valid_ou_ids):
    cf_client = boto3.client('cloudformation')
    with open(template_file, 'r', encoding='utf-8') as file:
        template_body = file.read()
    try:
        # Create StackSet with Parameters
        response = cf_client.create_stack_set(
            StackSetName=stackset_name,
            TemplateBody=template_body,
            Parameters=[
                {
                    'ParameterKey': 'LambdaRoleName',
                    'ParameterValue': role_name
                },
                {
                    'ParameterKey': 'MasterAccountBucketName',
                    'ParameterValue': master_account_bucket_name
                },
                {
                    'ParameterKey': 'ResourceMasterBucketName',
                    'ParameterValue': resource_master_bucket_name
                }
            ],
            Capabilities=['CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'],
            PermissionModel='SERVICE_MANAGED',
            AutoDeployment={
                'Enabled': True,
                'RetainStacksOnAccountRemoval': False
            }
        )
        print(f"StackSet {stackset_name} created.")

        # Create Stack Instances
        deployment_targets = {
            'OrganizationalUnitIds': valid_ou_ids
        }

        cf_client.create_stack_instances(
            StackSetName=stackset_name,
            DeploymentTargets=deployment_targets,
            Regions=[region]
        )
        print(f"Stack instances for {stackset_name} are being deployed in {region}.")
    except Exception as e:
        print(f"Error in deploying StackSet: {e}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--stackset-name', required=True, help='Name of the StackSet')
    parser.add_argument('--template-file', required=True, help='Path to the CloudFormation template file')
    parser.add_argument('--region', required=True, help='AWS region for the StackSet deployment')
    parser.add_argument('--master-account-bucket-name', required=True, help='Name of the S3 bucket in the master account for data collection')
    parser.add_argument('--resource-master-bucket-name', required=True, help='Name of the S3 bucket in the master account for Lambda package')
    parser.add_argument('--role-name', required=True, help='Name of the IAM role for the Lambda function')
    parser.add_argument('--valid-ou-ids', required=True, nargs='+', help='List of valid OU IDs')

    args = parser.parse_args()

    deploy_stackset_member_accounts(args.stackset_name, args.template_file, args.region, args.master_account_bucket_name, args.resource_master_bucket_name, args.role_name, args.valid_ou_ids)