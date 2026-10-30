resource "aws_ecr_repository" "app" {
  name                 = "${local.name}-web"
  image_tag_mutability = "IMMUTABLE"
  # Laboratorio: destroy elimina tambien las imagenes publicadas aqui.
  force_delete = true
  image_scanning_configuration {
    scan_on_push = true
  }
  encryption_configuration {
    encryption_type = "AES256"
  }
}
output "app_repository_url" {
  value = aws_ecr_repository.app.repository_url
}
