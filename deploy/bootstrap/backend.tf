# Administrado por un operador; independiente del state del laboratorio.
terraform {
  backend "s3" {
    bucket       = "abuelito-eks-tfstate-455982475279-us-east-1"
    key          = "abuelito/bootstrap/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
