# Pendiente: ARN de certificado ACM emitido en us-east-1 para el dominio real.
variable "acm_certificate_arn" {
  description = "Certificado ACM emitido y validado en us-east-1. Null mantiene HTTP de laboratorio."
  type        = string
  default     = null
  nullable    = true
  validation {
    condition     = var.acm_certificate_arn == null ? true : can(regex("^arn:aws:acm:us-east-1:[0-9]{12}:certificate/", var.acm_certificate_arn))
    error_message = "El certificado debe ser de ACM en us-east-1."
  }
}
resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  count             = var.acm_certificate_arn == null ? 0 : 1
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}
resource "aws_lb_listener" "https" {
  count             = var.acm_certificate_arn == null ? 0 : 1
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
