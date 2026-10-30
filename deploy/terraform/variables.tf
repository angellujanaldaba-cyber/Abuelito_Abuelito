variable "admin_cidrs" {
  description = "IPv4 publicas autorizadas para kubectl; usar tu IP con /32."
  type        = list(string)
  validation {
    condition = length(var.admin_cidrs) > 0 && alltrue([
      for cidr in var.admin_cidrs : can(cidrnetmask(cidr)) && try(tonumber(split("/", cidr)[1]) >= 24, false)
    ])
    error_message = "Usa al menos un CIDR IPv4 /24 o mas restrictivo; preferentemente tu IP/32."
  }
}
variable "admin_principal_arn" {
  description = "ARN IAM de usuario o rol administrador; no usar ARN STS assumed-role ni root."
  type        = string
  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:(user|role)/.+$", var.admin_principal_arn))
    error_message = "Se requiere un ARN IAM de usuario o rol."
  }
}
variable "kubernetes_version" {
  type    = string
  default = "1.37"
}
variable "capacity_type" {
  type    = string
  default = "ON_DEMAND"
  validation {
    condition     = contains(["SPOT", "ON_DEMAND"], var.capacity_type)
    error_message = "Usa SPOT u ON_DEMAND."
  }
}
