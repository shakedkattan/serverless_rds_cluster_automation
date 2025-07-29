data "aws_ssm_parameter" "db_username" {
  name = "/project/db/username"
}

data "aws_ssm_parameter" "db_password" {
  name            = "/project/db/password"
  with_decryption = true
}

locals {
  mysql_list    = []
  postgres_list = []

  # Map DB name
  engine_map = merge(
    { for name in local.mysql_list    : name => { engine = "mysql" } },
    { for name in local.postgres_list : name => { engine = "postgres" } }
  )


  shared_settings = {
    instance_class       = "db.t3.micro"
    db_username = data.aws_ssm_parameter.db_username.value
    db_password = data.aws_ssm_parameter.db_password.value
    db_subnet_group_name = aws_db_subnet_group.prod_rds.name
    security_group_ids   = [aws_security_group.prod_rds.id]
    allocated_storage    = 20
  }

  rds_customs = {
    #"payments-db" = {
      #instance_class = "db.t3.small"
    #},
    #"analytics-db" = {
      #allocated_storage = 21
    #}
  }


  rds_list = concat(local.mysql_list, local.postgres_list)
  rds_definitions = {
    for name in local.rds_list :
    name => merge(
      local.shared_settings,
      local.engine_map[name],
      lookup(local.rds_customs, name, {}),
      { name = "prod-${name}" }
    )
  }
}

module "prod_rds_instances" {
  for_each = local.rds_definitions

  source = "git::https://github.com/shakedkattan/serverless_rds_cluster_automation.git//terraform/modules/rds?ref=main"

  name                 = each.value.name
  engine               = each.value.engine
  instance_class       = each.value.instance_class
  username             = each.value.db_username
  password             = each.value.db_password
  db_subnet_group_name = each.value.db_subnet_group_name
  security_group_ids   = each.value.security_group_ids
  allocated_storage    = each.value.allocated_storage
}
