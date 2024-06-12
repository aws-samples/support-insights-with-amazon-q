# Q Support Insights (QSI) - AWS Support Collection Deployment

This repository contains scripts and resources to automate the deployment of AWS Lambda functions in designated member accounts. The deployed resources collect and upload AWS Support data (AWS Support Cases, AWS Health Events, and Trusted Advisor Checks) to an existing Amazon S3 bucket in the Data Collection Central account. The collected data can be utilized with Amazon Q to analyze and gain insights into your support cases, service health events, and Trusted Advisor recommendations.

## Prerequisites

- An AWS account for resources with the necessary permissions to create and manage resources (IAM roles, Lambda functions, CloudFormation stacks, etc.).
- A Support plan such as Business, Enterprise On-Ramp, or Enterprise Support to access the AWS Support API.
- It is recommended to utilize AWS CloudShell, as it comes pre-installed with the required libraries and tools. Alternatively, you can use a local machine with the AWS CLI installed and configured with valid credentials.
- An Amazon S3 bucket for Data Collection in Master Account
- An Amazon S3 bucket for Resources for infrastructure deployment in Master Account

## Lambda Function Configuration

The default Lambda function configuration is set to:

- Memory: 128MB
- Ephemeral storage: 512MB

However, it is recommended to update these settings based on the volume of data you expect to collect. You can modify the Lambda function configuration in the `member_account_resources.yaml` 


## Directory Structure

```
├── deploy_collector.sh
├── deploy_infrastructure.py
├── deploy_stackset.py
├── individual-account-deployments
│   ├── deploy_collector_lambda_member.sh
│   ├── deploy_lambda_function.py
│   └── member_account_resources.yaml
├── member_account_resources.yaml
└── support-collector-lambda
    ├── health_client.py
    ├── lambda_function.py
    ├── region_lookup.py
    ├── ta_checks_info.json
    ├── upload_cases.py
    ├── upload_health.py
    └── upload_ta.py
```

## Deployment Options

You have two options for deploying the necessary resources:

### Option 1: Leveraging AWS Organizations - Bulk Deployment via StackSet

Utilize this option if you have AWS Organizations set up. You can leverage AWS CloudFormation StackSets across multiple linked or member accounts with a single operation. AWS Organizations integrates with CloudFormation, enabling centralized management as you scale across multiple accounts. It will setup the lambda function and EventBridge in all the AWS accounts that accounts that belong to the AWS Organization units provided by the user.

#### Resource Bucket Policy

Before running the deployment scripts, ensure that the bucket policy of the Resource S3 bucket (in the Data Collection Central account) is updated to grant access to the organizational units (OUs) where the member accounts reside. Replace the placeholders in the following bucket policy with your specific values:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAccessToQInsightsCollectorBucket",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::<your-resource-bucket-name>",
                "arn:aws:s3:::<your-resource-bucket-name>/*"
            ],
            "Condition": {
                "ForAnyValue:StringLike": {
                    "aws:PrincipalOrgPaths": "<organization-id>/<root-id>/<ou-id>/*"
                }
            }
        }
    ]
}
```

To find the `<organization-id>`, `<root-id>`, and `<ou-id>` values, refer to the AWS Organizations User Guide: [Viewing Details of an Organization](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_org_details.html#orgs_view_ou). Note that the organization ID starts with the prefix o-, the root ID starts with r-, and the OU ID starts with ou-  (e.g., o-xxxxx/r-xxxxx/ou-xxxxx).



#### Deployment Steps

1. In the Data Collection Central account, launch AWS CloudShell or open a terminal window on your local machine.
2. Clone the repository:

```bash
git clone https://github.com/aws-samples/support-insights-with-amazon-q.git
```

3. Navigate to the `support_collector` directory:

```bash
cd support-insights-with-amazon-q/src/support_collector
```

4. Run the `deploy_collector.sh` script with the name of your S3 bucket as an argument:

```bash
chmod +x deploy_collector.sh 
./deploy_collector.sh
```
The script will prompt you for the following inputs:
- Enter the OU IDs separated by commas (e.g., `o-xxxxxxxxxx, o-xxxxxxxxxx`)
- Enter the data collection S3 bucket name in the master account
- Enter the resource S3 bucket name that will contain the Lambda package in the master account

5. The script will perform the following tasks:
   - Install dependencies and create a deployment package for the AWS Lambda functions.
   - Create a CloudFormation StackSet to deploy necessary resources (IAM roles, Lambda functions, etc.) in member accounts.
   - Set up an Amazon EventBridge scheduler to periodically trigger the AWS Lambda function.
   - Generate a JSON file for the bucket policy that you can use to update the Data Collector S3 Bucket.

6. Once the StackSet deployment is completed, update the Data Collector S3 Bucket policy. Optionally, you can copy the JSON from the `output_bucket_policy.json` file generated by the script in the root directory. The bucket policy should look like:  

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::111122223333:role/SupportInsightsLambdaRole-9c8794ee-f9e8",
                    "arn:aws:iam::444455556666:role/SupportInsightsLambdaRole-9c8794ee-f9e8",
                    "arn:aws:iam::777788889999:role/SupportInsightsLambdaRole-9c8794ee-f9e8"
                ]
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::DATA-COLLECTOR_BUCKET/*",
            "Condition": {
                "ForAnyValue:StringLike": {
                    "aws:PrincipalOrgPaths": "o-xxxxxxxxxx/r-xxxx/ou-xxxx-xxxxxxxx/*"
                }
            }
        }
    ]
}
```

### Option 2: Manual Deployment in Each Account via CloudFormation

Utilize this option if you do not wish to leverage AWS Organizations and want to target a few accounts.

#### Deployment Steps

1. In the member account, launch AWS CloudShell or open a terminal window on your local machine.
2. Clone the repository:

```bash
git clone https://github.com/aws-samples/support-insights-with-amazon-q.git
```

3. Navigate to the `individual-account-deployments` directory:

```bash
cd support-insights-with-amazon-q/src/support_collector/individual-account-deployments
```

4. Run the `deploy_collector_lambda_member.sh` script:

```bash
chmod +x deploy_collector.sh
./deploy_collector_lambda_member.sh
```

5. The script will prompt you to provide the input bucket name (in the member account) and the name of the S3 bucket in the Data Collection Central account.
6. The script will perform the following tasks:
   - Install dependencies and create a deployment package for the AWS Lambda function.
   - Upload the deployment package to the S3 bucket in the member account.
   - Create an IAM role `SupportInsightsLambdaRole-9c8794ee-f9e8` with the necessary permissions to access the AWS Support and Health services, as well as the S3 bucket in the Data Collection Central account.
   - Deploy the Lambda function with the created IAM role, using a CloudFormation stack.
   - Set up an Amazon EventBridge scheduler to periodically trigger the AWS Lambda function.

#### Bucket Policy

The bucket policy of the S3 bucket (in the Data Collection Central account) needs to be updated to grant access to the specific member accounts. Replace the placeholders in the following bucket policy with your specific values:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<member_account_id>:role/SupportInsightsLambdaRole-9c8794ee-f9e8"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::<your-bucket-name>/*"
    }
  ]
}
```

Replace `<member_account_id>` with the actual AWS account ID of the member account, and `<your-bucket-name>` with the name of the S3 bucket in the Data Collection Central account. You can add multiple accounts. Please note 'SupportInsightsLambdaRole-9c8794ee-f9e' is going to be the name of the role created in the member accounts to grant permission to Lambda function as indicated in the deployment steps below .

## Data Collection Process

After the successful deployment, an Amazon EventBridge scheduler will periodically trigger the AWS Lambda function. The Lambda function will collect and store the support data in the specified S3 bucket.

- The initial execution of the Lambda function will collect and store up to 180 days of historical data (support cases, health events, and Trusted Advisor checks). However, you can modify the number of days by updating the `ScheduleExpression` in the `EventBridgeRuleForHistoricalSupportData` resource in the `member_account_resources.yaml` CloudFormation template.
- Subsequent executions will collect and store data for the previous day.
- You have the flexibility to configure the Lambda function to collect one, two, or all three of the support cases, health events, and Trusted Advisor checks by modifying the input parameters in the `EventBridgeRuleForHistoricalSupportData` and `EventBridgeRuleForDailyRun` resources. You can also create separate EventBridge rules for each type of data (cases, health, and Trusted Advisor) if desired.

The user does not need to manually trigger the Lambda function, as the data collection process is automated and managed by the deployed resources.

## Optional - Testing the Lambda Function

You can test the Lambda function by invoking it with a custom payload. The payload should be a JSON object with the following properties:

- `past_no_of_days` (integer): The number of past days for which you want to retrieve support data.
- `bucket_name` (string): The name of the S3 bucket where the support data will be stored.
- `case` (boolean): Whether to include case data or not.
- `health` (boolean): Whether to include health data or not.
- `ta` (boolean): Whether to include Trusted Advisor data or not.

Example payload:

```json
{
  "past_no_of_days": 2,
  "bucket_name": "<DATA-COLLECTION-BUCKET>",
  "case": true,
  "health": true,
  "ta": true
}
```

In this example, the Lambda function will retrieve support data for the past 180 days, including case data, health data, and Trusted Advisor data. The data will be stored in the `<DATA-COLLECTION-BUCKET>` S3 bucket.

To test the Lambda function:

1. Navigate to the AWS Lambda console.
2. Select the Lambda function you want to test.
3. Click the "Test" button.
4. Under "Configure test event", choose "Create new event".
5. Enter an event name (e.g., "TestEvent").
6. Replace the default JSON payload with the desired payload (e.g., the example payload above).
7. Click "Create".
8. Click "Test" to invoke the Lambda function with the provided payload.

The Lambda function will execute, and you can review the output and logs in the "Execution result" section.

Note: Make sure to replace `<DATA-COLLECTION-BUCKET>` with the actual name of your S3 bucket.

## Cleanup

To clean up the deployed resources, follow these steps:

1. Delete the CloudFormation StackSet (for option 1):
   - Navigate to the CloudFormation console in the Central account.
   - Select the StackSet named `support-insights-stackset-*`.
   - Delete the StackSet.

   Alternatively, you can use the CLI commands as below:
   - Delete the Stack Instances (replace the placeholders):
   ```
   aws cloudformation delete-stack-instances --stack-set-name support-insights-stackset-<time-stamp> --deployment-targets OrganizationalUnitIds=<ou ids> --regions us-west-2 --operation-preferences FailureToleranceCount=0,MaxConcurrentCount=1 --no-retain-stacks
   ```
   - Delete the StackSet:
   ```
   aws cloudformation delete-stack-set --stack-set-name support-insights-stackset-<time-stamp>
   ```

2. Delete the member account CloudFormation stack (for option 2):
   - Navigate to the CloudFormation console in the member account.
   - Select the stack named `SupportInsightsLambdaStack`.
   - Delete the stack.

   Alternatively, you can use the CLI command:
   ```
   aws cloudformation delete-stack --stack-name SupportInsightsLambdaStack
   ```

> **Warning:** Before proceeding with the next step, ensure that no critical data is present in the S3 bucket containing the support data. Deleting the S3 bucket will permanently remove all data stored in it.

3. Empty and delete the S3 bucket containing the support data.

## Disclaimer

The sample code provided in this solution is for educational purposes only. Users should thoroughly test and validate the solution before deploying it in a production environment.