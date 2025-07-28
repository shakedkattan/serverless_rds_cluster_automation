import boto3
import os
import re
import json
import base64
import subprocess
from pathlib import Path

# ================================================================================
# BOOTSTRAP SCRIPT FOR SERVERLESS RDS PROJECT VIA CIRCLECI (manual trigger)
# This script:
# - Creates a secure versioned S3 bucket for Terraform state
# - Edits backend.tf, vpc.tf, and main.tf for both dev/prod to reflect user and region
# - Creates SSM Parameters for DB credentials
# - Commits changes back to GitHub
# ================================================================================

AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")  # Default region if not set
AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
GITHUB_USERNAME = os.environ["CIRCLE_PROJECT_USERNAME"]
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

REPO_NAME = "automated_serverless_rds_cluster"
REPO_PATH = Path.cwd()  # Local path for working with the repo

# =============================================================================
#  Update file contents based on regex replacements (used for region/source URLs)
# =============================================================================
def update_file(file_path, replacements):
    path = REPO_PATH / file_path
    content = path.read_text()
    for old, new in replacements.items():
        content = re.sub(old, new, content)
    path.write_text(content)

# =============================================================================
#  Create S3 bucket with versioning and best practices for Terraform backend
# =============================================================================
def create_tf_bucket():
    print(f" Creating S3 bucket in region: {AWS_REGION}")
    bucket_name = f"{GITHUB_USERNAME}-devops-tfstate-bucket"

    s3 = boto3.client("s3", region_name=AWS_REGION,
                      aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY)

    # us-east-1 requires no LocationConstraint
    if AWS_REGION == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": AWS_REGION}
        )

    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"}
    )

    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    print(f" Bucket '{bucket_name}' created and secured.")
    return bucket_name

# =============================================================================
#  Store DB username and password as SecureString in AWS SSM Parameter Store
# =============================================================================
def update_ssm_parameters():
    ssm = boto3.client("ssm", region_name=AWS_REGION,
                       aws_access_key_id=AWS_ACCESS_KEY,
                       aws_secret_access_key=AWS_SECRET_KEY)
    ssm.put_parameter(
        Name="/project/db/username",
        Value=DB_USERNAME,
        Type="SecureString",
        Overwrite=True,
    )
    ssm.put_parameter(
        Name="/project/db/password",
        Value=DB_PASSWORD,
        Type="SecureString",
        Overwrite=True,
    )
    
# =============================================================================
#  Commit and push local changes to GitHub using GitPython-style interaction
# =============================================================================
def commit_to_github():
    subprocess.run(["git", "config", "user.email", "ci-bot@yourdomain.com"], check=True)
    subprocess.run(["git", "config", "user.name", "CI Bootstrap Bot"], check=True)
    subprocess.run(["git", "add", "."], check=True)

    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print(" No changes to commit.")
        return

    subprocess.run(["git", "commit", "-m", "bootstrap: update tf files with region, modules, and ssm"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    
# =============================================================================
#  Main orchestration logic — create bucket, store credentials, update TF files
# =============================================================================
def main():
    create_tf_bucket()
    update_ssm_parameters()
    
    for env in ["dev", "prod"]:
        update_file(f"terraform/env/{env}/backend.tf", {
    r'region\s*=\s*".*?"': f'region = "{AWS_REGION}"',
    r'bucket\s*=\s*".*?"': f'bucket = "{GITHUB_USERNAME}-devops-tfstate-bucket"'
        })
        update_file(f"terraform/env/{env}/vpc.tf", {
            r'git::https://github.com/.+?/automated_serverless_rds_cluster.git//terraform/modules/vpc\?ref=main':
            f'git::https://github.com/{GITHUB_USERNAME}/automated_serverless_rds_cluster.git//terraform/modules/vpc?ref=main',
            r'public_subnet_az\s*=\s*".*?"': f'public_subnet_az = "{AWS_REGION}a"',
            r'private_subnet_azs\s*=\s*\[.*?\]': f'private_subnet_azs = ["{AWS_REGION}a", "{AWS_REGION}b"]',
            r'private_subnet_cidrs\s*=\s*\[.*?\]': 'private_subnet_cidrs = ["10.0.2.0/24", "10.0.3.0/24"]',
        })
        update_file(f"terraform/env/{env}/main.tf", {
            r'git::https://github.com/.+?/automated_serverless_rds_cluster.git//terraform/modules/rds\?ref=main':
            f'git::https://github.com/{GITHUB_USERNAME}/automated_serverless_rds_cluster.git//terraform/modules/rds?ref=main',
            r'name\s*=\s*"/project/db/username"': 'name = "/project/db/username"',
            r'name\s*=\s*"/project/db/password"': 'name = "/project/db/password"',
        })

    commit_to_github()

if __name__ == "__main__":
    main()
