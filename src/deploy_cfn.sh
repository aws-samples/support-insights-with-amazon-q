#!/bin/bash
# Check if a bucket name is passed as an argument
if [ "$#" -ne 2 ]; then
    echo "Specify a bucket that will store the deployment resources and the datasource bucket."
    echo "Usage: $0 <deployment-bucket-name> <datasource-bucket-name>"
    exit 1
fi

# Assign the first argument to BUCKET_NAME
DEPLOYMENT_BUCKET_NAME=$1
DATASOURCE_BUCKET_NAME=$2
cd q_application

STACK_NAME=amazon-q-cfn

echo "Creating zip for lambda function..."
rm -f amazon-q-lambda*.zip

chmod -R u=rwx,go=r ./*

zip amazon-q-lambda.zip *.py requirements.txt 
aws s3api put-object --bucket $DEPLOYMENT_BUCKET_NAME --key amazon-q-lambda.zip --body amazon-q-lambda.zip --no-cli-pager 

echo "Creating zip for the lambda layer..."
rm -rf python
pip install --target=python/ -r requirements.txt 

zip -r9 amazon-q-lambda-layer.zip python
aws s3api put-object --bucket $DEPLOYMENT_BUCKET_NAME --key amazon-q-lambda-layer.zip --body amazon-q-lambda-layer.zip --no-cli-pager 

# for testing, publishing layer manually
# aws lambda publish-layer-version --layer-name q-support-lambda-layer --zip-file fileb://amazon-q-lambda-layer.zip --compatible-runtimes python3.12 --region us-east-1

echo "Deleting stack..."
aws cloudformation delete-stack --stack-name $STACK_NAME --no-cli-pager 
# sleep 3
echo "Creating stack..."
aws cloudformation create-stack --template-body file://amazon-q-cfn.yaml --capabilities CAPABILITY_NAMED_IAM --stack-name $STACK_NAME --output json \
--parameters ParameterKey=S3LambdaBucket,ParameterValue=$DEPLOYMENT_BUCKET_NAME ParameterKey=S3DataSourceBucket,ParameterValue=$DATASOURCE_BUCKET_NAME --no-cli-pager

echo "Done"
cd ../
