#!/bin/bash
printf "This script will deploy the solution to an organization.\n\n"

printf "Enter the OU IDs separated by commas (ie: ou-xxxxxxxxxx1,ou-xxxxxxxxxx2): "
read OU_IDS
printf "\n\n"

printf "Enter the data collection S3 bucket name in the management account: "
read DATA_BUCKET_NAME
printf "\n\n"

printf "Do you want the script to overwrite the data collection bucket policy on your behalf?\nThis requires PutBucketPolicy permission and it will OVERWRITE the current policy.\nIf the policy is not set, member accounts may not be able to store their data properly. (Y/N, default: Y): "
read OVERWRITE_DATA_BUCKET_POLICY_ANSWER
if [ "$OVERWRITE_DATA_BUCKET_POLICY_ANSWER" != "${OVERWRITE_DATA_BUCKET_POLICY_ANSWER#[Yy]}" ] ;then
if [ "$OVERWRITE_DATA_BUCKET_POLICY_ANSWER" != "${OVERWRITE_DATA_BUCKET_POLICY_ANSWER#[Yy]}" ] ;then
    OVERWRITE_DATA_BUCKET_POLICY=--overwrite-data-bucket-policy
else
    OVERWRITE_DATA_BUCKET_POLICY="--no-overwrite-data-bucket-policy"
fi
printf "\n\n"

printf "Invoking deploy_infrastructure.py...\n"
python3 deploy_infrastructure.py --data-bucket "${DATA_BUCKET_NAME}" --ou-ids "${OU_IDS}" "${OVERWRITE_DATA_BUCKET_POLICY}"
