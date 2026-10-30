variable "ci_deploy_role_arn" {
  description = "Rol OIDC para deploy, limitado al namespace abuelito. Null no crea acceso adicional."
  type        = string
  default     = null
}
resource "aws_eks_access_entry" "ci" {
  count         = var.ci_deploy_role_arn == null ? 0 : 1
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = var.ci_deploy_role_arn
  type          = "STANDARD"
}
resource "aws_eks_access_policy_association" "ci" {
  count         = var.ci_deploy_role_arn == null ? 0 : 1
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_eks_access_entry.ci[0].principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"
  access_scope {
    type       = "namespace"
    namespaces = ["abuelito"]
  }
}
