#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the configured AWS region
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="us-west-2"  # Default to us-west-2 if no region is configured
fi

# Function to validate S3 bucket
validate_bucket() {
    local bucket_name=$1
    if ! aws s3 ls "s3://${bucket_name}" >/dev/null 2>&1; then
        echo -e "${RED}Error: Bucket '${bucket_name}' does not exist or is not accessible${NC}"
        return 1
    fi
    return 0
}

# Function to validate ARN format for IAM Identity Center
validate_arn() {
    #local arn=$1
    #if [[ ! $arn =~ ^arn:aws:sso:::instance/ssoins-[a-f0-9]{12}$ ]]; then
        #echo -e "${RED}Error: Invalid IAM Identity Center ARN format. Expected format: #arn:aws:sso:::instance/ssoins-<12-character-id>${NC}"
        #return 1
    #fi
    return 0
}


# Function to check stack status
check_stack_status() {
    local stack_name=$1
    local wait_message=$2
    
    echo -e "${YELLOW}${wait_message}${NC}"
    
    while true; do
        status=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --query 'Stacks[0].StackStatus' \
            --output text \
            --region $REGION)
            
        if [[ $status == *"COMPLETE"* ]]; then
            if [[ $status == "CREATE_COMPLETE" || $status == "UPDATE_COMPLETE" ]]; then
                echo -e "${GREEN}Stack $stack_name completed successfully${NC}"
                return 0
            else
                echo -e "${RED}Stack $stack_name failed with status: $status${NC}"
                return 1
            fi
        elif [[ $status == *"FAILED"* || $status == *"ROLLBACK"* ]]; then
            echo -e "${RED}Stack $stack_name failed with status: $status${NC}"
            return 1
        fi
        
        echo -n "."
        sleep 10
    done
}

# Function to deploy stack
deploy_stack() {
    local stack_name=$1
    local template_file=$2
    local parameters=$3
    local capabilities=$4
    
    echo -e "${YELLOW}Deploying stack: $stack_name${NC}"
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$stack_name" --region $REGION 2>&1 | grep -q 'does not exist'; then
        # Create stack
        aws cloudformation create-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities $capabilities \
            --region $REGION
            
        check_stack_status "$stack_name" "Creating stack $stack_name..."
    else
        # Update stack
        if aws cloudformation update-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities $capabilities \
            --region $REGION 2>/dev/null; then
            
            check_stack_status "$stack_name" "Updating stack $stack_name..."
        else
            echo -e "${GREEN}No updates required for $stack_name${NC}"
            return 0
        fi
    fi
}

# Function to get stack output
get_stack_output() {
    local stack_name=$1
    local output_key=$2
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
        --output text \
        --region $REGION
}

# Main script starts here
echo "AWS CloudFormation Deployment Script"
echo "----------------------------------------"
echo "Using AWS Region: $REGION"
echo ""

# Get input values with validation
while true; do
    echo "Enter the S3 bucket name for storing support data: "
    read SUPPORT_DATA_BUCKET
    if validate_bucket "$SUPPORT_DATA_BUCKET"; then
        break
    fi
done

while true; do
    echo "Enter the S3 bucket name for storing Lambda resources: "
    read RESOURCE_BUCKET
    if validate_bucket "$RESOURCE_BUCKET"; then
        break
    fi
done

while true; do
    echo "Enter the IAM Identity Center ARN: "
    read IAM_IDENTITY_CENTER_ARN
    if validate_arn "$IAM_IDENTITY_CENTER_ARN"; then
        break
    fi
done

# Confirm inputs
echo -e "\nPlease confirm your inputs:"
echo "AWS Region: $REGION"
echo "Support Data Bucket: $SUPPORT_DATA_BUCKET"
echo "Resource Bucket: $RESOURCE_BUCKET"
echo "IAM Identity Center ARN: $IAM_IDENTITY_CENTER_ARN"

echo -e "\nDo you want to proceed with these values? (y/n)"
read CONFIRM

if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

# Step 1: Deploy case metadata stack
METADATA_PARAMS="ParameterKey=ExistingDataBucketName,ParameterValue=$SUPPORT_DATA_BUCKET"
if deploy_stack "case-metadata-stack" "resources-for-case-metadata-cfn.yaml" "$METADATA_PARAMS" "CAPABILITY_NAMED_IAM"; then
    echo -e "${GREEN}Case metadata stack deployed successfully${NC}"
    
    # Step 2: Deploy Amazon Q Business stack
    Q_PARAMS="ParameterKey=S3DataSourceBucket,ParameterValue=$SUPPORT_DATA_BUCKET \
              ParameterKey=IAMIdentityCenterARN,ParameterValue=$IAM_IDENTITY_CENTER_ARN \
              ParameterKey=QBusinessApplicationName,ParameterValue=qsi-app"
              
    if deploy_stack "amazon-q-stack" "amazon-q-cfn.yaml" "$Q_PARAMS" "CAPABILITY_IAM"; then
        echo -e "${GREEN}Amazon Q Business stack deployed successfully${NC}"
        
        # Get Q Application ID
        Q_APP_ID=$(get_stack_output "amazon-q-stack" "QBusinessApplicationId")
        
        if [ ! -z "$Q_APP_ID" ]; then
            # Step 3: Deploy custom plugin stack
            PLUGIN_PARAMS="ParameterKey=QApplicationId,ParameterValue=$Q_APP_ID \
                          ParameterKey=ExistingDataBucketName,ParameterValue=$SUPPORT_DATA_BUCKET \
                          ParameterKey=ExistingResultsBucketName,ParameterValue=$RESOURCE_BUCKET"
                          
            if deploy_stack "custom-plugin-stack" "custom-plugin.yaml" "$PLUGIN_PARAMS" "CAPABILITY_IAM"; then
                echo -e "${GREEN}Custom plugin stack deployed successfully${NC}"
                
                # Display important outputs
                API_ENDPOINT=$(get_stack_output "custom-plugin-stack" "APIEndpoint")
                API_TOKEN=$(get_stack_output "custom-plugin-stack" "GeneratedAPIToken")
                
                echo -e "\nDeployment Complete! Important Information:"
                echo "API Endpoint: $API_ENDPOINT"
                echo "API Token: $API_TOKEN"
                
                # Save outputs to a file
                echo -e "\nSaving deployment information to deploy-outputs.txt"
                {
                    echo "Deployment Information"
                    echo "====================="
                    echo "Date: $(date)"
                    echo "Region: $REGION"
                    echo "Support Data Bucket: $SUPPORT_DATA_BUCKET"
                    echo "Resource Bucket: $RESOURCE_BUCKET"
                    echo "Q Application ID: $Q_APP_ID"
                    echo "API Endpoint: $API_ENDPOINT"
                    echo "API Token: $API_TOKEN"
                } > deploy-outputs.txt
                
                echo "Deployment information saved to deploy-outputs.txt"
            else
                echo "Failed to deploy custom plugin stack"
                exit 1
            fi
        else
            echo "Failed to get Q Application ID"
            exit 1
        fi
    else
        echo "Failed to deploy Amazon Q Business stack"
        exit 1
    fi
else
    echo "Failed to deploy case metadata stack"
    exit 1
fi
