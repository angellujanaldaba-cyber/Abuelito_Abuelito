terraform {
  required_version = "~> 1.16.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = ["455982475279"]
  default_tags {
    tags = {
      Project   = "abuelito-eks"
      ManagedBy = "Terraform"
      Purpose   = "learning"
    }
  }
}
