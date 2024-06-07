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

echo "Enter the bucket name for resource upload: "
read MEMBER_BUCKET_NAME

echo "Enter the name of the S3 bucket in the master account: "
read MASTER_BUCKET_NAME

echo "Uploading deployment package to S3..."
aws s3 cp support-collector-lambda.zip s3://$MEMBER_BUCKET_NAME/

echo "Invoking deploy_lambda_function.py..."
python3 "$PWD/individual-account-deployments/deploy_lambda_function.py" --bucket-name $MEMBER_BUCKET_NAME --master-account-bucket-name $MASTER_BUCKET_NAME