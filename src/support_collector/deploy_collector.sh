#!/bin/bash
echo "************************************************************************************************"
echo "* WARNING: Before running this script, make sure you have                                      *"
echo "* updated the bucket policy of the resource bucket to give                                     *"
echo "* access to download the Lambda package for the accounts                                       *"
echo "* residing in the organizational units; they will need to use                                  *"
echo "* the bucket for deployment. The bucket policy should look                                     *" 
echo "* similar to the following:                                                                    *"
echo "*                                                                                              *"
echo "* {                                                                                            *"
echo "*     \"Version\": \"2012-10-17\",                                                             *"
echo "*     \"Statement\": [                                                                         *"
echo "*         {                                                                                    *"
echo "*             \"Sid\": \"AllowAccessToQInsightsCollectorBucket\"                               *"
echo "*             \"Effect\": \"Allow\",                                                           *"
echo "*             \"Principal\": \"*\",                                                            *"
echo "*             \"Action\": [                                                                    *"
echo "*                 \"s3:GetObject\",                                                            *"
echo "*                 \"s3:ListBucket\",                                                           *"
echo "*                 \"s3:PutObject\"                                                             *"
echo "*             ],                                                                               *"
echo "*             \"Resource\": [                                                                  *"
echo "*                 \"arn:aws:s3:::<bucket_name>\",                                              *"
echo "*                 \"arn:aws:s3:::<bucket_name>/*\"                                             *"
echo "*             ],                                                                               *"
echo "*             \"Condition\": {                                                                 *"
echo "*                 \"ForAnyValue:StringLike\": {                                                *"
echo "*                     \"aws:PrincipalOrgPaths\": [                                             *"
echo "*                          \"o-xxxxxxxxxx/r-xxxx/ou-xxxx-xxxxxxx1/*\",                         *"
echo "*                          \"o-xxxxxxxxxx/r-xxxx/ou-xxxx-xxxxxxx2/*\"                          *"
echo "*                     ]                                                                        *"
echo "*                 }                                                                            *"
echo "*             }                                                                                *"
echo "*         }                                                                                    *"
echo "*     ]                                                                                        *"
echo "* }                                                                                            *"
echo "************************************************************************************************"

echo "Enter the OU IDs separated by commas (ie: ou-xxxxxxxxxx1,ou-xxxxxxxxxx2): "
read OU_IDS

echo "Enter the data collection S3 bucket name in the management account: "
read DATA_BUCKET_NAME

echo "Do you want the script to overwrite the data collection bucket policy on your behalf? This requires PutBucketPolicy permission and it will OVERWRITE the current policy. If the policy is not set, the data from member accounts may not be saved properly. (Y/N, default: Y): "
read OVERWRITE_DATA_BUCKET_POLICY_ANSWER
if [ "$OVERWRITE_DATA_BUCKET_POLICY_ANSWER" != "${OVERWRITE_DATA_BUCKET_POLICY_ANSWER#[Yy]}" ] ;then 
    OVERWRITE_DATA_BUCKET_POLICY=--overwrite-data-bucket-policy
else
    OVERWRITE_DATA_BUCKET_POLICY="--no-overwrite-data-bucket-policy"
fi

echo "Enter the resource S3 bucket name that will contain the Lambda package in the management account for deployment: "
read RESOURCE_BUCKET_NAME

# Check if the buckets exist
if ! aws s3 ls "s3://${DATA_BUCKET_NAME}" 2>/dev/null; then
    echo "Error: The bucket '${DATA_BUCKET_NAME}' does not exist or you do not have permission to access it."
    exit 1
fi

if ! aws s3 ls "s3://${RESOURCE_BUCKET_NAME}" 2>/dev/null; then
    echo "Error: The bucket '${RESOURCE_BUCKET_NAME}' does not exist or you do not have permission to access it."
    exit 1
fi

echo "Cleaning up old files..."
rm -rf support-collector-lambda.zip support-collector-lambda-layer.zip python temp_dir

echo "Installing dependencies into a temporary directory..."
mkdir temp_dir
pip3 install -r requirements.txt -t temp_dir/

echo "Copying dependencies to the Lambda directory..."
cp -r temp_dir/* support-collector-lambda/

echo "Creating deployment package..."
cd support-collector-lambda
zip -r ../support-collector-lambda.zip . -x '*.DS_Store' 2>/dev/null || true
cd ..

echo "Current directory: $PWD"

Clean up the temporary directory
rm -rf temp_dir
echo "Uploading deployment package to S3..."
aws s3 cp support-collector-lambda.zip s3://${RESOURCE_BUCKET_NAME}/

echo "Invoking deploy_infrastructure.py..."
python3 deploy_infrastructure.py --data-bucket "${DATA_BUCKET_NAME}" --resource-bucket "${RESOURCE_BUCKET_NAME}" --ou-ids "${OU_IDS}" "${OVERWRITE_DATA_BUCKET_POLICY}"