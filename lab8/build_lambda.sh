#!/bin/bash
sudo apt update && sudo apt install zip -y
cd lambda
rm -rf package *.zip
pip install --target ./package -r requirements.txt
cd package
zip -r ../my_deployment_package.zip .
cd ..
zip my_deployment_package.zip ./lab8_lambda_mcp_acg.py
