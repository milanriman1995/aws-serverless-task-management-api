provider "aws" {
  region = "eu-west-2"

  default_tags {
    tags = {
      Project     = "aws-serverless-task-management-api"
      Environment = "dev"
      ManagedBy   = "Terraform"
    }
  }
}

