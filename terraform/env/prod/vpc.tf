module "prod_vpc" {
  source = "git::https://github.com/shakedkattan/serverless_rds_cluster_automation.git//terraform/modules/vpc?ref=main"

  name                 = "prod"
  vpc_cidr             = "10.0.0.0/16"

  public_subnet_cidr   = "10.0.1.0/24"
  public_subnet_az     = "eu-central-1a"

  private_subnet_cidrs  = ["10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_azs    = ["eu-central-1a", "eu-central-1b"]
}


resource "aws_db_subnet_group" "prod_rds" {
  name       = "prod-rds-subnet-group"
  subnet_ids = module.prod_vpc.private_subnet_ids

  tags = {
    Name = "prod-rds-subnet-group"
  }
}


resource "aws_security_group" "prod_rds" {
  name        = "prod-rds-sg"
  description = "Allow DB traffic"
  vpc_id      = module.prod_vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.prod_vpc.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "prod-rds-sg"
  }
}
