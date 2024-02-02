import boto3
import json
import argparse

MEMBER_ACCOUNTS_TEMPLATE_PATH = 'member_accounts_resources.yaml' 
DATA_COLLECTION_TEMPLATE_PATH = 'central_account_resources.yaml' 
REGION = boto3.session.Session().region_name #'us-west-2'
CFN_MEMBER_STACK_NAME = 'MemberAccountResourcesStackSet3' #CloudFormation STACK to run in member account
CFN_CENTRAL_STACK_NAME = 'CentralAccountResourcesStack' #CloudFormation STACK to run in central account
EXCLUDE_ACCOUNTS = []

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--account_id", required=True, help="The AWS account ID for the central account")
args = parser.parse_args()

DATA_COLLECTION_ACCOUNT_ID = args.account_id 

# Invokes the CFN to create role in each member account that enables invoking support API 
# and assuming role from the central account with trust relationship
def deploy_stackset_member_accounts(stackset_name, template_file, ous, region, DATA_COLLECTION_ACCOUNT_ID):
    cf_client = boto3.client('cloudformation')
    with open(template_file) as file:
        template_body = file.read()
    try:
        # Create StackSet with Parameters
        response = cf_client.create_stack_set(
            StackSetName=stackset_name,
            TemplateBody=template_body,
            Parameters=[
                {
                    'ParameterKey': 'ManagementAccountID',
                    'ParameterValue': DATA_COLLECTION_ACCOUNT_ID
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
        #operation_id = response['OperationId']
        #if operation_id:
            #waiter = cf_client.get_waiter('stack_set_operation_complete')
            #waiter.wait(StackSetName=stackset_name, OperationId=operation_id)
        #else:
            #print("No OperationId returned; proceeding without waiting.")
        # Create Stack Instances
        cf_client.create_stack_instances(
            StackSetName=stackset_name,
            DeploymentTargets={
                'OrganizationalUnitIds': ous
            },
            Regions=[region]
        )
        print(f"Stack instances for {stackset_name} are being deployed in {region}.")
    except Exception as e:
        print(f"Error in deploying StackSet: {e}")

# Invokes the CFN to create role in central account that collects the support cases from other member accounts
def deploy_stack_in_central_account(stack_name, template_file): 
    cf_client = boto3.client('cloudformation')
    with open(template_file) as file:
        template_body = file.read()
    try:
        # Create Stack
        cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']
        )
        print(f"Stack {stack_name} is being created.")
        waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
        print('Central account stack deployed successfully!')
    except Exception as e:
        print(f"Error in deploying stack: {e}")

def get_organizational_units(parent_id):
    org_client = boto3.client('organizations')
    ous = []
    paginator = org_client.get_paginator('list_organizational_units_for_parent')
    page_iterator = paginator.paginate(ParentId=parent_id)
    for page in page_iterator:
        for ou in page['OrganizationalUnits']:
            ous.append(ou['Id'])
    return ous

def get_root_id():
    client = boto3.client('organizations')
    try:
        # List all roots in the organization
        roots = client.list_roots()['Roots']
        if roots:
            # Typically, there is only one root in an AWS Organization
            root_id = roots[0]['Id']
            return root_id
        else:
            print("No roots found in the organization.")
            return None
    except client.exceptions.AWSOrganizationsNotInUseException:
        print("AWS Organizations is not set up.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def main():
    
    deploy_stack_in_central_account(CFN_CENTRAL_STACK_NAME, DATA_COLLECTION_TEMPLATE_PATH)
    
    root_id = get_root_id()
    if root_id:
        root_id = get_root_id() 
        ous = get_organizational_units(root_id)
        if ous:
            deploy_stackset_member_accounts(CFN_MEMBER_STACK_NAME, MEMBER_ACCOUNTS_TEMPLATE_PATH, ous, REGION, DATA_COLLECTION_ACCOUNT_ID)
        else:
            print("No Organizational Units found, skipping member accounts(s) stackset deployment")
    

if __name__ == '__main__':
    main()
