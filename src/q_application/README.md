# Q Support Insights (QSI) - Amazon Q Business Deployment
Note: Amazon Q Business is only available in us-west-2 and us-east-1 at this time.

The steps below will deploy an shell script which will check pre-requisites required to deploy an Amazon Q Business application. The script will deploy an Amazon Q Business application, S3 data source connector, required IAM roles, Lambda Function and Web Experience (web experience to provide support insights with chatbot, conversational and interactive user experience) for Q Business application using AWS IAM Identity Center (IDC) as identity provider (IdP). The deployed web experience can be used by users to login and securely use the application, based only on the content the logged in user has permissions to access.

# Pre-requisites
 1. Amazon Q Business is only available in AWS Regions "us-east-1" and "us-west-2".
 2. AWS IAM Identity Center (IDC) can create only one instance per account and across all Amazon Web Services Regions. AWS IAM Identity Center must be  configured in the same region as your Q Application. Hence script will be create IAM Identity Center(IDC) only in "us-east-1" and "us-west-2" as Amazon Q Business is currently only available in this regions if there is no IAM Identity Center (IDC) currently configured.

 # Limitations
 1. Script should be executed from one of member account where Data Source Bucket resides. The script can only create IAM Identity Center instance from member accounts and not from an Organization Account as the CreateInstance API of IAM Identity Center will only create the instance in member account of AWS Organization.
 2. If there is requirement to create IAM Identity center at Organizational Account, you can Enable AWS Identity center manually using following [guide](https://docs.aws.amazon.com/singlesignon/latest/userguide/get-set-up-for-idc.html) from Organization Account and then run the script.


# Deployment

**a. Deploy Amazon Q Business Application, S3 Datasource Connector and Web Experience**

1.	Launch AWS CloudShell in either AWS Region (us-east-1 or us-west-2)  and clone the QCI repository from GitHub using the command:
```bash
git clone https://github.com/aws-samples/support-insights-with-amazon-q.git
```

2.	Navigate to the support-insights-with-amazon-q directory, and run the deployment script.
```bash
cd support-insights-with-amazon-q/src
chmod +x deploy_cfn.sh
./deploy_cfn.sh
```
3. Provide the inputs as requested in the script.

**Note:**
- The script will check **pre-requisites to deploy Amazon Q Business Application**. Amazon Q Business requires AWS IAM Identity Center (IDC) for user and/or group subscription management, authentication and authorization. The script will check if AWS IAM Identity Center (IDC) is configured in us-east-1 or us-west-2. 
- **If AWS IAM Identity Center (IDC) is not configured in us-east-1 or us-west-2** script will enable and create AWS IAM Identity Center (IDC) Instance, provision with one User and Group called "QUsers" along with resources required for setting up Amazon Q Business Application using a CloudFormation template in region where AWS CloudShell was launched to run script based on user input. The script will exit if User Input ("no") is selected. 
- **If AWS IAM Identity Center (IDC) is already configured in us-east-1 or us-west-2**, the script will create resources required for setting up Amazon Q Business Application using a CloudFormation template. AWS IAM Identity Center needs to configured in the same region as your Q Application. The script will exit if AWS IAM Identity Center (IDC) is not configured in region (us-east-1 or us-west-2) where AWS CloudShell is being launched to run the script (ie: running the script in us-east-1 when IAM Identity Center is configured in us-west-2).

**b. Syncronize Amazon Q Datasource.**

The data source created above is scheduled to synchronize the data stored in provided Amazon S3 Bucket every day at midnight UTC.
1.	Login to AWS Account where the script was executed and navigate to the Amazon Q console and select your Q application with the name that was provided during deployment step.
2. Select the datasource qci-insights-datasource and click Sync now.

**c. Add Groups and Users Access**

1.	Login to AWS Account where script was executed and navigate to the Amazon Q console and select your Q application with name that was provided in above Step.
2. Navigate to Groups and users and click on Add Groups and users, select Assign existing users and groups, click Next and click Get Started.
3. In the Assign users and groups window use the search box to find users and groups by name. Clich Assign to add the group/users to the application.
4. Selected the newly added user/group ,click the Choose Subscription, select Q Business Pro/Q Business Lite .

**d. Use Web Experience**

At this stage, the Amazon Q Application with web experience is created.
1.	Login to AWS Account where script was executed and navigate to the Amazon Q console and select your Q application with name that was provided in above Step.
2. In the Data sources, check the Current sync state status. If it states Syncing, you will have to wait until it is completed.
2. Click on Deployed URL under Web experience settings to launch the deployed web experience.
3. Type your query and it should return a response after a few seconds. 

## Cleanup
To clean up the environment you have setup:
1. Delete the Q Application: delete the corresponding Cloudformation Stack.
2. Empty and delete the S3 bucket:
   * S3 bucket that contains the data that was configured during Amazon Q Business Deployment.
   

## Disclaimer
The sample code provided in this solution is for educational purposes only and users should thoroughly test and validate the solution before deploying it in a production environment.
