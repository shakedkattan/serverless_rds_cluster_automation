# ================================================================================
#     Entry point for the Lambda function triggered by SQS messages.
#     Parses the incoming event, extracts RDS parameters (db_name, env, engine),
#     and triggers a GitHub PR creation to provision a new RDS cluster.
# ================================================================================

# Imports
import os
import json
import boto3
import logging
from github import Github
from datetime import datetime
import re

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

# ENV Vars
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ.get("GITHUB_REPO", "shakedkattan/serverless_rds_cluster_automation")
BRANCH_BASE = os.environ.get("BRANCH_BASE", "main")

# GitHub Client
gh = Github(GITHUB_TOKEN)
repo = gh.get_repo(GITHUB_REPO)


# ================================================================================
#     This function receives HCL text as a string, locates a specific list 
#     (e.g., mysql_list = [ ... ]), and appends a new value to that list 
#     without duplicating existing entries. Basically creating a new RDS Cluster
# ================================================================================
def append_to_list_in_hcl(hcl_text, list_name, new_value):
    pattern = rf'({list_name}\s*=\s*\[)([^\]]*)(\])'
    match = re.search(pattern, hcl_text)
    if not match:
        raise ValueError(f"List '{list_name}' not found in HCL")

    list_start, list_body, list_end = match.groups()
    items = [item.strip().strip('"') for item in list_body.split(',') if item.strip()]

    if new_value in items:
        return hcl_text  

    items.append(new_value)

    # Always add trailing comma
    new_items_str = ', '.join(f'"{item}"' for item in items) + ', '

    new_list_str = f'{list_start}{new_items_str}{list_end}'
    return hcl_text[:match.start()] + new_list_str + hcl_text[match.end():]

    items.append(new_value)
    new_items_str = ', '.join(f'"{item}"' for item in items)
    new_list_str = f'{match.group(1)}{new_items_str}{match.group(3)}'

    return hcl_text[:match.start()] + new_list_str + hcl_text[match.end():]


# ================================================================================
#     This function receives HCL text as a string, locates a specific list 
#     (e.g., mysql_list = [ ... ]), and appends a new value to that list 
#     without duplicating existing entries. Basically creating a new RDS Cluster
# ================================================================================
def lambda_handler(event, context):
    logger.info("Incoming event: %s", json.dumps(event))
    logger.info("Raw SQS Body: %s", event["Records"][0]["body"])

# ================================================================================
#     Extracts and validates the incoming JSON payload from SQS message body.
#     Ensures required keys (db_name, env, engine) are present.
#     Returns HTTP 400 if the payload is malformed or missing fields.
# ================================================================================
    
    try:
        raw_body = json.loads(event["Records"][0]["body"])  # SQS body
        db_name = raw_body["db_name"]
        env = raw_body["env"]
        engine = raw_body["engine"]
    except (KeyError, json.JSONDecodeError) as e:
        logger.error("❌ Bad payload: %s", str(e))
        return {"statusCode": 400, "body": "Invalid request"}

    branch_name = f"rds-pr-{db_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    tf_path = f"terraform/env/{env}/main.tf"
    list_name = "mysql_list" if engine == "mysql" else "postgres_list"

# ================================================================================
#     Creates a new Git branch based on the default branch (e.g., "main").
#     Retrieves the existing Terraform file corresponding to the environment.
#     Determines which list (MySQL/Postgres) to append the new DB name to.
# ================================================================================
    
    try:
        base = repo.get_branch(BRANCH_BASE)
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base.commit.sha)

        file = repo.get_contents(tf_path, ref=BRANCH_BASE)
        existing = file.decoded_content.decode()

# ================================================================================
#     Calls helper function to inject the new DB name into the appropriate
#     list (mysql_list / postgres_list) inside the Terraform file.
#     Ensures no duplicate entries. Keeps formatting and adds trailing comma.
# ================================================================================
        
        new_content = append_to_list_in_hcl(existing, list_name=list_name, new_value=db_name)

        repo.update_file(
            path=tf_path,
            message=f"Add {db_name} to {list_name}",
            content=new_content,
            sha=file.sha,
            branch=branch_name
        )

# ================================================================================
#     Updates the Terraform file in the new branch and commits the changes.
#     Then creates a Pull Request (PR) from the new branch to main.
#     The PR contains a title and body describing the provisioned DB.
# ================================================================================   
        
        pr = repo.create_pull(
            title=f"Provision {db_name}",
            body=f"Automated PR to add `{db_name}` to `{list_name}`.",
            head=branch_name,
            base=BRANCH_BASE
        )
        
# ================================================================================  
        
        logger.info("✅ PR URL: %s", pr.html_url)
        return {"statusCode": 200, "body": f"PR created: {pr.html_url}"}

    except Exception as e:
        logger.error("❌ Failed to create PR: %s", str(e))
        return {"statusCode": 500, "body": "Error creating PR"}
