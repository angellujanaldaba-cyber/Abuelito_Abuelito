output "cluster_name" {
  value = aws_eks_cluster.main.name
}
output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}
output "vpc_id" {
  value = aws_vpc.main.id
}
output "subnet_ids" {
  value = [for subnet in aws_subnet.private : subnet.id]
}
output "public_subnet_ids" {
  value = [for subnet in aws_subnet.public : subnet.id]
}
output "alb_url" {
  description = "Direccion tecnica del ALB; con TLS habilitado redirige a HTTPS pero el certificado es para el dominio real."
  value       = "http://${aws_lb.main.dns_name}"
}
output "application_url" {
  value = "${var.acm_certificate_arn == null ? "http" : "https"}://dev.miguelinfra.com"
}
output "cloudflare_cname_target" {
  description = "Destino del CNAME dev en Cloudflare; cambiarlo solo cuando Abuelito este sano."
  value       = aws_lb.main.dns_name
}
output "node_role_arn" {
  value = aws_iam_role.nodes.arn
}
output "configure_kubectl" {
  value = "aws eks update-kubeconfig --region us-east-1 --name ${aws_eks_cluster.main.name}"
}
