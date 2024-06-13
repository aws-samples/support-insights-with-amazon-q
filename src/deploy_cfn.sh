#!/usr/bin/env bash
#Function deploys Amazon Q
function deploy_Q() {

STACK_NAME_Q=amazon-q-cfn

if [[ "$CURRENT_REGION" == "us-east-1" ]];
 then
  if [[ -n "$IDC_INSTANCEARN_USE1" ]];
    then
       echo "IAM Identity Center is a pre-requisite to use Amazon Q Business. IAM Identity Center is configured in $CURRENT_REGION with ARN $IDC_INSTANCEARN_USE1. Proceeding with Amazon Q Business deployment" 
       read -r -p " Enter name for the Amazon Q Business Application (Hyphens (-) can be included, but not spaces):  " QBusinessApplicationName    
       read -r -p " Enter name of the S3 Data Source Bucket:  " S3DataSourceBucket
       echo "Creating stack..."
       aws cloudformation create-stack --template-body file://amazon-q-cfn.yaml --capabilities CAPABILITY_NAMED_IAM --stack-name $STACK_NAME_Q --parameters ParameterKey=IAMIdentityCenterARN,ParameterValue=$IDC_INSTANCEARN_USE1 ParameterKey=S3DataSourceBucket,ParameterValue=$S3DataSourceBucket ParameterKey=QBusinessApplicationName,ParameterValue=$QBusinessApplicationName --no-cli-pager
   else
       echo "IAM Identity Center is configured in us-west-2 Region with ARN $IDC_INSTANCEARN_USW2. Amazon Q Business application must be configured in the same Region as your IAM Identity Center. Re-Run Script in us-west-2 Region."; exit 1
   fi
 fi  

if [[ "$CURRENT_REGION" == "us-west-2"  ]];
 then
  if [[ -n "$IDC_INSTANCEARN_USW2" ]];
    then
       echo "IAM Identity Center is pre-requisite to configure Amazon Q Business. IAM Identity Center is configured in $CURRENT_REGION with ARN $IDC_INSTANCEARN_USW2. Proceeding with Amazon Q Deployment" 
       read -r -p " Enter name for the Amazon Q Business Application (Hyphens (-) can be included, but not spaces):  " QBusinessApplicationName    
       read -r -p " Enter name of the S3 Data Source Bucket :  " S3DataSourceBucket
       echo "Creating stack..."
       aws cloudformation create-stack --template-body file://amazon-q-cfn.yaml --capabilities CAPABILITY_NAMED_IAM --stack-name $STACK_NAME_Q --parameters ParameterKey=IAMIdentityCenterARN,ParameterValue=$IDC_INSTANCEARN_USW2 ParameterKey=S3DataSourceBucket,ParameterValue=$S3DataSourceBucket ParameterKey=QBusinessApplicationName,ParameterValue=$QBusinessApplicationName --no-cli-pager
    else
       echo "IAM Identity Center is configured in us-east-1 Region with ARN $IDC_INSTANCEARN_USE1. Amazon Q Business application must be configured in the same Region as your IAM Identity Center. Re-Run Script in us-east-1 Region."; exit 1
  fi   
fi     
}

#Checking Pre-requistes to deploy Amazon Q.

echo "   --------------------------------------------------------- "
echo "                   Amazon Q Deployment                       "
echo "   --------------------------------------------------------- "
cd q_application

CURRENT_REGION="${AWS_REGION}"
echo "Starting Deployment of Amazon Q Business in $CURRENT_REGION. This script will check pre-requisites to deploy Amazon Q Business."
if [[ "$CURRENT_REGION" != us-east-1 && "$CURRENT_REGION" != us-west-2 ]];
 then
  echo "Exiting from script. Amazon Q Business is only available in us-west-2 and us-east-1. Re-run script in us-west-2 or us-east-1." ; exit 1
fi

IDC_INSTANCEARN_USE1=$(aws sso-admin list-instances --query "Instances[*].InstanceArn" --region us-east-1 --output text)
IDC_INSTANCEARN_USW2=$(aws sso-admin list-instances --query "Instances[*].InstanceArn" --region us-west-2 --output text)

if [[ -z "$IDC_INSTANCEARN_USE1" && -z "$IDC_INSTANCEARN_USW2" ]];
 then
   echo "Exiting from script. Please check pre-requistes and re-run script." exit 1
 else
  deploy_Q
fi
echo "Done"
cd ../
