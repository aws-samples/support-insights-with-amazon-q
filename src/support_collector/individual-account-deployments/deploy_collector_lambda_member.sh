#!/bin/bash

printf "This script will deploy the solution to a single account.\n"

printf  "Enter the name of the S3 bucket to store your support data:\n"
read SUPPORT_BUCKET_NAME

printf "Invoking deploy_lambda_function.py...\n"
python3 "$PWD/deploy_lambda_function.py" --support-data-bucket-name $SUPPORT_BUCKET_NAME