data "aws_rds_engine_version" "postgres" {
  engine  = "postgres"
  version = "16"
  latest  = true
}
resource "aws_db_subnet_group" "app" {
  name       = "${local.name}-db"
  subnet_ids = [for subnet in aws_subnet.private : subnet.id]
}
resource "aws_security_group" "database" {
  name_prefix = "${local.name}-db-"
  description = "PostgreSQL privado: acceso solo desde nodos EKS"
  vpc_id      = aws_vpc.main.id
}
resource "aws_vpc_security_group_ingress_rule" "database_eks" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}
resource "aws_cloudwatch_log_group" "database" {
  name              = "/aws/rds/instance/${local.name}-db/postgresql"
  retention_in_days = 7
}
resource "aws_db_instance" "app" {
  identifier                      = "${local.name}-db"
  engine                          = "postgres"
  engine_version                  = data.aws_rds_engine_version.postgres.version
  engine_lifecycle_support        = "open-source-rds-extended-support-disabled"
  instance_class                  = "db.t4g.micro"
  multi_az                        = true
  allocated_storage               = 20
  storage_type                    = "gp3"
  storage_encrypted               = true
  db_name                         = "abuelito"
  username                        = "abuelito_admin"
  manage_master_user_password     = true
  db_subnet_group_name            = aws_db_subnet_group.app.name
  vpc_security_group_ids          = [aws_security_group.database.id]
  publicly_accessible             = false
  backup_retention_period         = 7
  backup_window                   = "08:00-09:00"
  maintenance_window              = "sun:09:00-sun:10:00"
  auto_minor_version_upgrade      = true
  copy_tags_to_snapshot           = true
  deletion_protection             = false
  skip_final_snapshot             = var.db_skip_final_snapshot
  final_snapshot_identifier       = var.db_skip_final_snapshot ? null : var.db_final_snapshot_identifier
  enabled_cloudwatch_logs_exports = ["postgresql"]
  depends_on                      = [aws_cloudwatch_log_group.database]
}
variable "db_final_snapshot_identifier" {
  description = "Nombre unico para el respaldo final al ejecutar destroy. Cambiarlo antes de recrear otro laboratorio."
  type        = string
  default     = "abuelito-eks-final-20261029"
}
variable "db_skip_final_snapshot" {
  description = "Solo true cuando se autoriza eliminar los datos sin snapshot final."
  type        = bool
  default     = false
}
output "database_endpoint" {
  value = aws_db_instance.app.address
}
output "database_admin_secret_arn" {
  description = "Referencia del secreto administrador; no contiene la contrasena."
  value       = aws_db_instance.app.master_user_secret[0].secret_arn
}
resource "aws_cloudwatch_metric_alarm" "database_storage" {
  alarm_name          = "${local.name}-db-poco-espacio"
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 2
  comparison_operator = "LessThanThreshold"
  threshold           = 2147483648
  treat_missing_data  = "missing"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.app.identifier }
}
