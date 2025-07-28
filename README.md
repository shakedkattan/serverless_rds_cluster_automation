🌀 Automated Serverless RDS Cluster Provisioning
Overview
This project provides a fully automated, serverless solution for provisioning RDS clusters on AWS based on developer requests. It leverages API Gateway, SNS, SQS, Lambda, GitHub, Terraform, and CircleCI to enable a scalable and secure workflow.

Key Features:

Developers send a JSON request (via API Gateway)
Request is routed through SNS → SQS → Lambda
Lambda creates a GitHub Pull Request with Terraform code
CI/CD pipeline applies the infrastructure using Terraform
Supports both MySQL and PostgreSQL, in dev and prod environments
Deployment Instructions
1. GitHub & CircleCI Setup
Fork this repository and keep the name: automated_serverless_rds_cluster.
Go to CircleCI GitHub Auth and connect your GitHub account.
Navigate to Projects > Set up Project:
Select the repo
Branch: main
Select the Fastest setup option
Click on the three dots next to your project → Project Settings:
Go to Environment Variables and define the following:
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
DB_USERNAME=your-db-user
DB_PASSWORD=your-db-pass
GITHUB_TOKEN=your-personal-access-token
