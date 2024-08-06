#!/bin/bash

echo "Cleaning up old files..."
rm -rf support-collector-lambda.zip support-collector-lambda-layer.zip python temp_dir

echo "Installing dependencies into a temporary directory..."
mkdir temp_dir
pip3 install -r ../requirements.txt -t temp_dir/

echo "Copying dependencies to the lambda directory..."
cp -r temp_dir/* ../support-collector-lambda/

echo "Creating deployment package..."
cd ../support-collector-lambda
zip -r ../support-collector-lambda.zip . -x '*.DS_Store' 2>/dev/null || true
cd ..

echo "Current directory: $PWD"

# Clean up the temporary directory
rm -rf temp_dir
echo "Deployment package created: support-collector-lambda.zip"

echo "Enter the bucket name to store the Lambda function resource: "
# read RESOURCE_BUCKET_NAME
RESOURCE_BUCKET_NAME=support-amazon-q-resource-account03

echo "Enter the name of the S3 bucket to store your support data: "
# read SUPPORT_BUCKET_NAME
SUPPORT_BUCKET_NAME=support-amazon-q-data-account03

echo "Uploading deployment package to S3..."
aws s3 cp support-collector-lambda.zip s3://$RESOURCE_BUCKET_NAME/

echo "Invoking deploy_lambda_function.py..."
python3 "$PWD/individual-account-deployments/deploy_lambda_function.py" --resource-bucket-name $RESOURCE_BUCKET_NAME --support-data-bucket-name $SUPPORT_BUCKET_NAME