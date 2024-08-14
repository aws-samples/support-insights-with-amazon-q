#!/bin/bash

echo "This script will deploy the solution to a single account.\n"

echo "Enter the name of the S3 bucket to store your support data:"
read SUPPORT_BUCKET_NAME

echo "Invoking deploy_lambda_function.py..."
python3 "$PWD/individual-account-deployments/deploy_lambda_function.py" --support-data-bucket-name $SUPPORT_BUCKET_NAME