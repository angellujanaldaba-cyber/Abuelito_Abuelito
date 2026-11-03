# Ejecuciones administradas efimeras: sin registrar runners GitHub ni PAT.
variable "pipeline_bucket" {
  type        = string
  description = "Bucket bootstrap privado para state, planes y paquetes CodeBuild."
  default     = "abuelito-eks-tfstate-455982475279-us-east-1"
}
locals {
  execution_stages  = toset(["bootstrap", "deploy"])
  execution_account = "455982475279"
}
resource "aws_security_group" "pipeline" {
  name_prefix = "${local.name}-pipeline-"
  vpc_id      = aws_vpc.main.id
  description = "CodeBuild privado, sin conexiones entrantes"
}
resource "aws_vpc_security_group_egress_rule" "pipeline_https" {
  security_group_id = aws_security_group.pipeline.id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}
resource "aws_vpc_security_group_ingress_rule" "pipeline_eks" {
  security_group_id            = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  referenced_security_group_id = aws_security_group.pipeline.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}
resource "aws_cloudwatch_log_group" "pipeline" {
  for_each          = local.execution_stages
  name              = "/aws/codebuild/${local.name}-${each.key}"
  retention_in_days = 7
}
resource "aws_iam_role" "pipeline" {
  for_each             = local.execution_stages
  name                 = "${local.name}-codebuild-${each.key}"
  permissions_boundary = "arn:aws:iam::${local.execution_account}:policy/abuelito-ci-boundary-${each.key}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow", Principal = { Service = "codebuild.amazonaws.com" }, Action = "sts:AssumeRole"
      Condition = { StringEquals = { "aws:SourceAccount" = local.execution_account }, ArnEquals = {
        "aws:SourceArn" = "arn:aws:codebuild:us-east-1:${local.execution_account}:project/${local.name}-${each.key}"
      } }
    }]
  })
}
resource "aws_iam_role_policy" "pipeline" {
  for_each = local.execution_stages
  role     = aws_iam_role.pipeline[each.key].id
  name     = "private-execution"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      { Effect = "Allow", Action = ["eks:DescribeCluster"], Resource = aws_eks_cluster.main.arn },
      { Effect = "Allow", Action = ["s3:GetObject"], Resource = "arn:aws:s3:::${var.pipeline_bucket}/codebuild/dev/bundles/*" },
      { Effect = "Allow", Action = ["s3:PutObject"], Resource = "arn:aws:s3:::${var.pipeline_bucket}/codebuild/dev/results/*/${each.key}-*.json" },
      { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.pipeline[each.key].arn}:*" },
      { Effect = "Allow", Action = ["ec2:CreateNetworkInterface", "ec2:DeleteNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DescribeDhcpOptions", "ec2:DescribeSubnets", "ec2:DescribeSecurityGroups", "ec2:DescribeVpcs"], Resource = "*", Condition = { StringEquals = { "aws:RequestedRegion" = "us-east-1" } } },
      { Effect = "Allow", Action = ["ec2:CreateNetworkInterfacePermission"], Resource = "arn:aws:ec2:us-east-1:${local.execution_account}:network-interface/*", Condition = {
        StringEquals = { "ec2:AuthorizedService" = "codebuild.amazonaws.com" }, ArnEquals = { "ec2:Subnet" = [for s in aws_subnet.private : s.arn] }
      } }
      ], each.key == "bootstrap" ? [
      { Effect = "Allow", Action = ["rds:DescribeDBInstances"], Resource = aws_db_instance.app.arn },
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = aws_db_instance.app.master_user_secret[0].secret_arn }
      ] : [
      { Effect = "Allow", Action = ["elasticloadbalancing:DescribeTargetHealth"], Resource = aws_lb_target_group.app.arn }
    ])
  })
}
resource "aws_eks_access_entry" "pipeline" {
  for_each      = local.execution_stages
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.pipeline[each.key].arn
  type          = "STANDARD"
}
resource "aws_eks_access_policy_association" "pipeline" {
  for_each      = local.execution_stages
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_eks_access_entry.pipeline[each.key].principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/${each.key == "bootstrap" ? "AmazonEKSClusterAdminPolicy" : "AmazonEKSEditPolicy"}"
  access_scope {
    type       = each.key == "bootstrap" ? "cluster" : "namespace"
    namespaces = each.key == "bootstrap" ? null : ["abuelito"]
  }
}
resource "aws_codebuild_project" "pipeline" {
  for_each               = local.execution_stages
  name                   = "${local.name}-${each.key}"
  service_role           = aws_iam_role.pipeline[each.key].arn
  build_timeout          = 30
  queued_timeout         = 10
  concurrent_build_limit = 1
  artifacts { type = "NO_ARTIFACTS" }
  source {
    type = "NO_SOURCE"
    buildspec = jsonencode({
      version = 0.2
      phases  = { build = { commands = ["python3 - <<'FETCH_BUNDLE'\n${file("${path.module}/../codebuild/fetch_bundle.py")}\nFETCH_BUNDLE", "bash deploy/codebuild/run.sh"] } }
    })
  }
  environment {
    type                        = "ARM_CONTAINER"
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux-aarch64-standard:3.0"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = false
    dynamic "environment_variable" {
      for_each = {
        PIPELINE_STAGE       = each.key, PIPELINE_BUCKET = var.pipeline_bucket,
        DB_RESOURCE_ID       = aws_db_instance.app.resource_id,
        ALB_TARGET_GROUP_ARN = aws_lb_target_group.app.arn, ALB_DNS_NAME = aws_lb.main.dns_name
      }
      content {
        name  = environment_variable.key
        value = environment_variable.value
      }
    }
  }
  vpc_config {
    vpc_id             = aws_vpc.main.id
    subnets            = [for subnet in aws_subnet.private : subnet.id]
    security_group_ids = [aws_security_group.pipeline.id]
  }
  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.pipeline[each.key].name
      status     = "ENABLED"
    }
  }
  depends_on = [aws_iam_role_policy.pipeline, aws_eks_access_policy_association.pipeline, aws_eks_node_group.main, aws_route.nat, aws_route_table_association.private, aws_vpc_security_group_ingress_rule.pipeline_eks]
}
