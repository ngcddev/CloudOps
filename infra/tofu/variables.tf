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

  validation {
    condition = alltrue([
      for client in values(var.clients) : contains(keys(local.plans), client.plan)
    ])
    error_message = format(
      "Plan inexistente para cliente(s): %s. Planes disponibles: %s.",
      join(", ", [
        for name, client in var.clients : "${name}=${client.plan}"
        if !contains(keys(local.plans), client.plan)
      ]),
      join(", ", sort(keys(local.plans)))
    )
  }
}
