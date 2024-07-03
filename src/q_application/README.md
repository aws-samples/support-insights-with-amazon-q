# Q Support Insights (QSI) - Amazon Q Business Deployment
Note: Amazon Q Business is only available in us-east-1 and us-west-2 at this time.

The steps below will utilize a shell script which will check the pre-requisites required to deploy an Amazon Q Business application. The script will deploy an Amazon Q Business application, S3 data source connector, required IAM roles, and Web Experience (web experience to provide support insights with a chatbot, conversational and interactive user experience) for the Q Business application using AWS IAM Identity Center (IDC) as the identity provider (IdP). The deployed web experience can be used by users to log in and securely use the application, based only on the content the logged-in user has permissions to access.

# Pre-requisites
 1. Amazon Q Business is only available in AWS Regions "us-east-1" and "us-west-2".
 2. [AWS IAM Identity Center](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html) as the SAML 2.0-compliant identity provider (IdP) configured in the same region as your Q Application. Please ensure that you have enabled an [IAM Identity Center instance](https://docs.aws.amazon.com/singlesignon/latest/userguide/get-set-up-for-idc.html), provisioned at least one user, and provided each user with a valid email address. For more details, see [Configure user access](https://docs.aws.amazon.com/singlesignon/latest/userguide/quick-start-default-idc.html) with the default IAM Identity Center directory. 
 
# Deployment

**a. Deploy Amazon Q Business Application, S3 Datasource Connector and Web Experience**

1.	Launch AWS CloudShell in either AWS Region (us-east-1 or us-west-2) in your Data Collection Central account and clone the QCI repository from GitHub using the command:
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


**b. Synchronize Amazon Q Datasource**

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
1. To delete the Q Application, delete the corresponding Cloudformation Stack.
2. Empty and delete the S3 bucket that contains the data that was configured during Amazon Q Business Deployment.   

## Disclaimer
The sample code provided in this solution is for educational purposes only and users should thoroughly test and validate the solution before deploying it in a production environment.
