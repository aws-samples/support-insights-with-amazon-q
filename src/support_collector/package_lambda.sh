#!/bin/bash

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
