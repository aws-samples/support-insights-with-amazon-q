# Amazon Q AWS Support Case Insights (QCI) - AWS Support Case Collection

If you already have support cases stored in an S3 bucket in JSON, TXT, or HTML format, you may skip this section. 

The steps below performs IAM roles creation in both the DataCollection and Linked accounts and use the [AWS Support API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/support.html) to get the list of support cases in JSON-formatted objects. 

### Case Collector Resources - Deployment
**Option 1:** Using setup script leveraging [AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html) - Bulk deployment via StackSet. Use this option if you have AWS Organizations setup. You can leverage [AWS CloudFormation StackSets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html) across multiple linked or member accounts with a single operation. AWS Organizations integrates with CloudFormation and helps you centrally manage as you scale to multiple accounts. 

1.	Launch AWS CloudShell and clone the QCI repository from GitHub using the command:

```bash
git clone https://github.com/aws-samples/support-case-insights-with-amazon-q.git
```

2.	Navigate to the q-support-case-insights directory, and run the setup script.

```bash
cd support-case-insights-with-amazon-q/src/case_collector
python3 deploy_infrastructure.py
```

**Option 2:** Manual Deployment in each account via CloudFormation.
Use this option if you don't have [AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html) setup and you do not have mutiple accounts. You will have to login to each member or linked account to run the CloudFormation template.

**Linked Account Deployment**
You will need to create necessary roles in each linked or member account for accessing AWS Support API.
1.	Login to AWS Linked account and navigate to the AWS CloudFormation console. 
2.	Download the linked account template [member-account-template.yaml](https://github.com/aws-samples/support-case-insights-with-amazon-q/blob/main/src/case_collector/member_accounts_resources.yaml).
3.	Create an AWS CloudFormation Stack with the downloaded template.
4.	Provide the inputs.
5.	Submit.

**DataCollection Account Deployment**
The CloudFormation will create necessary resources in DataCollection for accessing AWS Support API in Linked Accounts and uploading JSON response to S3.
1.	In Data Collection account, login and navigate to the AWS CloudFormation console. 
2.	Download the link account template [member-account-template.yaml](https://github.com/aws-samples/support-case-insights-with-amazon-q/blob/main/src/case_collector/central_account_resources.yaml).
3.	Create an AWS CloudFormation Stack with the downloaded template.
4.	Provide the inputs.
5.	Submit.


### Historical Cases Upload to S3
Now that you have IAM role setup to get support cases across your selected accounts using the AWS Support API, you can run the script as indicated below to upload the support cases in JSON format to your Data Collection S3 bucket.

Before running the script, verify the support profile is configured in the AWS credentials file. You can create access key for the user *support_case_insights* and update the AWS credentials file. 

```bash
[support]
aws_access_key_id = xxxxxxxxxx
aws_secret_access_key = xxxxxxxxxxxxxx
```

Run the upload cases script:
```
python bulk_upload_cases.py <name of the bucket in the DataCollection account that contains the case data>
```

This script assumes roles in member accounts, collects existing support cases, and uploads them to the designated Amazon S3 bucket. 


## Cleanup
To clean up the environment you have setup:
1. Delete the Q Application: delete the corresponding Cloudformation Stack.
2. Empty and delete the two S3 buckets:
   * S3 bucket that contains the support case data.
   * S3 bucket that contains Q Application deployment resources.
3. Delete the case collector resources: depending on the option you have selected for deployment, delete the Stackset or delete the IAM roles and corresponding Cloudformation stack.

## Disclaimer
The sample code provided in this solution is for educational purposes only and users should thoroughly test and validate the solution before deploying it in a production environment.
