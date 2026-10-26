# Variables de entrada para la infraestructura de clientes (spec 011, T03).
variable "gitea_token" {
  description = "Token de acceso a Gitea; se entrega por TF_VAR_gitea_token y no se versiona."
  type        = string
  sensitive   = true
}

variable "clients" {
  description = "Inventario de clientes, con dominio y código de plan."
  type = map(object({
    host = string
    plan = string
  }))
  default = {}
}
