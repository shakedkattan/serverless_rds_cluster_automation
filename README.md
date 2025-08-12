# 🌀 Serverless RDS Cluster Provisioning Automation

##  OVERVIEW

This project provides a fully automated, serverless solution for provisioning **RDS PostgreSQL/MySQL clusters** on AWS based on developer requests. It leverages API Gateway, SNS, SQS, Lambda, SSM, ASM, GitHub, Terraform, and CircleCI to enable a scalable and secure workflow.

**KEY FEATURES**
- Developers send a JSON request (via API Gateway)
- Request is routed through SNS → SQS → Lambda
- Lambda creates a GitHub Pull Request with Terraform code merge
- After merging, CI/CD pipeline applies the infrastructure using Terraform
- Supports both **MySQL** and **PostgreSQL**, in **dev** and **prod** environments
- Stores sensitive data in ASM & SSM
- SAM Stack monitored by CloudWatch, Application Insights, and special alerts.
- Least privilege IAM roles usage
---

##  INSTRUCTIONS

1. Fork this repository and keep the name: serverless_rds_cluster_automation
2. In your AWS account, create a new Secret in ASM:
   - Name: github-lambda-token
   - key: token
   - value: your github token value
3. [Log in to CircleCI](https://circleci.com/vcs-authorize) using your GitHub Auth
4. Set up a Project by selecting the repo, Branch = main
5. In Project Settings, set up 2 GitHub Triggers: Push to default branch, PR merged
6. Define Environment Variables:
   - AWS_ACCESS_KEY_ID=your-secret-access-key
   - AWS_SECRET_ACCESS_KEY=your-secret-key
   - AWS_REGION=any-region-1
   - DB_USERNAME=db-username-you-want
   - DB_PASSWORD=db-password-you-want
7. Run the pipeline. Only for the first time, it will run bootstrap.py to set everything. then it will create the SAM stack
8. That's it! Your SAM stack is now expecting JSONs from the API Gateway's /request Invoke URL
9. JSON Curl Example:
 ```bash
  curl -X POST https://YOUR_URL.execute-api.YOUR_REGION.amazonaws.com/provision/request \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "testdb",
    "env": "prod",
    "engine": "postgres"
  }'
```
