# 🌀 Automated Serverless RDS Cluster Provisioning

##  OVERVIEW

This project provides a fully automated, serverless solution for provisioning **RDS PostgreSQL/MySQL clusters** on AWS based on developer requests. It leverages API Gateway, SNS, SQS, Lambda, SSM, ASM, GitHub, Terraform, and CircleCI to enable a scalable and secure workflow.

**KEY FEATURES**
- Developers send a JSON request (via API Gateway)
- Request is routed through SNS → SQS → Lambda
- Lambda creates a GitHub Pull Request with Terraform code merge
- CI/CD pipeline applies the infrastructure using Terraform
- Supports both **MySQL** and **PostgreSQL**, in **dev** and **prod** environments

---

##  INSTRUCTIONS

1. Fork this repository and keep the name: serverless_rds_cluster_automation
2. In your AWS account, create a new Secret in ASM:
   - Name: github-lambda-token
   - key: token
   - value: your github token value
2. [Log in to CircleCI](https://circleci.com/vcs-authorize) using your GitHub Auth
3. Set up a Project by selecting the repo, Branch = main
4. In Project Settings, set up 2 GitHub Triggers: Push to default branch, PR merged
4. Define Environment Variables:
   - AWS_ACCESS_KEY_ID=your-secret-access-key
   - AWS_SECRET_ACCESS_KEY=your-secret-key
   - AWS_REGION=any-region-1
   - DB_USERNAME=db-username-you-want
   - DB_PASSWORD=db-password-you-want
5. Run the pipeline. Only for the first time, it will run bootstrap.py to set everything. then it will create the SAM stack
6. That's it! your SAM stack is now expecting JSONs from the API Gateway's /request Invoke URL
    JSON Curl Example:
 ```bash
  curl -X POST https://YOUR_URL.execute-api.YOUR_REGION.amazonaws.com/provision/request \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "testdb",
    "env": "prod",
    "engine": "postgres"
  }'
```
* Private note to you, Orel - I wanted to cost-optimize the lambda function even more using layers, editing resource usage configuration like Memory and more, but couldn't reach it on time. Even though, this Lambda isn't expected to run frequently in production, so it shouldn't hurt our wallet too much. 🙂
