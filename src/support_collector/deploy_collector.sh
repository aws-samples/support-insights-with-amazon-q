#!/bin/bash
echo "This script will deploy the solution to an organization.\n"

echo "Enter the OU IDs separated by commas (ie: ou-xxxxxxxxxx1,ou-xxxxxxxxxx2): "
read OU_IDS
echo ""

echo "Enter the data collection S3 bucket name in the management account: "
read DATA_BUCKET_NAME
echo ""

echo "Do you want the script to overwrite the data collection bucket policy on your behalf?\nThis requires PutBucketPolicy permission and it will OVERWRITE the current policy.\nIf the policy is not set, member accounts may not be able to store their data properly. (Y/N, default: Y): "
read OVERWRITE_DATA_BUCKET_POLICY_ANSWER
if [ "$OVERWRITE_DATA_BUCKET_POLICY_ANSWER" != "${OVERWRITE_DATA_BUCKET_POLICY_ANSWER#[Yy]}" ] ;then
    OVERWRITE_DATA_BUCKET_POLICY=--overwrite-data-bucket-policy
else
    OVERWRITE_DATA_BUCKET_POLICY="--no-overwrite-data-bucket-policy"
fi
echo ""

# Check if the bucket exist
if ! aws s3 ls "s3://${DATA_BUCKET_NAME}" 2>/dev/null; then
    echo "Error: The bucket '${DATA_BUCKET_NAME}' does not exist or you do not have permission to access it."
    exit 1
fi

echo "Invoking deploy_infrastructure.py..."
python3 deploy_infrastructure.py --data-bucket "${DATA_BUCKET_NAME}" --ou-ids "${OU_IDS}" "${OVERWRITE_DATA_BUCKET_POLICY}"
