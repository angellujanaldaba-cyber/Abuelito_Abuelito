terraform {
  required_version = "~> 1.16.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  backend "s3" {
    bucket       = "abuelito-eks-tfstate-455982475279-us-east-1"
    key          = "abuelito/runner/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = ["455982475279"]
  default_tags {
    tags = { Project = "abuelito-runner", ManagedBy = "Terraform" }
  }
}
variable "vpc_id" { type = string }
variable "private_subnet_id" { type = string }
variable "cluster_security_group_id" { type = string }
variable "ami_id" {
  description = "Ubuntu 24.04 ARM64 oficial verificado el 31 de octubre; revisar antes de actualizar."
  type        = string
  default     = "ami-09a93d801db0bafae"
}
data "aws_subnet" "private" { id = var.private_subnet_id }
data "aws_ami" "runner" {
  owners = ["099720109477"]
  filter {
    name   = "image-id"
    values = [var.ami_id]
  }
  filter {
    name   = "architecture"
    values = ["arm64"]
  }
}
resource "aws_security_group" "runner" {
  name_prefix = "abuelito-runner-"
  description = "Runner privado: sin conexiones entrantes"
  vpc_id      = var.vpc_id
}
resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.runner.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}
resource "aws_vpc_security_group_egress_rule" "http_packages" {
  security_group_id = aws_security_group.runner.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}
resource "aws_vpc_security_group_ingress_rule" "eks_api" {
  security_group_id            = var.cluster_security_group_id
  referenced_security_group_id = aws_security_group.runner.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}
resource "aws_iam_role" "ssm" {
  name = "abuelito-runner-ssm"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
resource "aws_iam_instance_profile" "ssm" { role = aws_iam_role.ssm.name }
resource "aws_instance" "runner" {
  ami                                  = data.aws_ami.runner.id
  instance_type                        = "t4g.small"
  subnet_id                            = var.private_subnet_id
  associate_public_ip_address          = false
  vpc_security_group_ids               = [aws_security_group.runner.id]
  iam_instance_profile                 = aws_iam_instance_profile.ssm.name
  instance_initiated_shutdown_behavior = "terminate"
  user_data                            = templatefile("${path.module}/bootstrap.sh", { register_script = file("${path.module}/register.sh") })
  user_data_replace_on_change          = true
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    http_protocol_ipv6          = "disabled"
  }
  root_block_device {
    volume_size           = 12
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }
  lifecycle {
    precondition {
      condition     = data.aws_subnet.private.vpc_id == var.vpc_id && !data.aws_subnet.private.map_public_ip_on_launch
      error_message = "Usar una subred privada de la VPC de EKS, con salida por NAT."
    }
  }
  tags       = { Name = "abuelito-runner-ephemeral" }
  depends_on = [aws_iam_role_policy_attachment.ssm]
}
output "instance_id" { value = aws_instance.runner.id }
