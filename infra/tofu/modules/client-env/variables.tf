# Parámetros del entorno de un cliente (spec 011, T06).
variable "name" {
  description = "Nombre corto del cliente y directorio de su overlay."
  type        = string
}

variable "host" {
  description = "Dominio del sitio del cliente."
  type        = string
}

variable "plan" {
  description = "Código del plan del cliente."
  type        = string
}

variable "quota" {
  description = "Cuotas CPU y memoria tomadas del catálogo de planes."
  type = object({
    cpu    = string
    memory = string
  })
}

variable "image_tag" {
  description = "Etiqueta inicial de la imagen del sitio."
  type        = string
  default     = "v1"
}

variable "image_name" {
  description = "Nombre de la imagen del sitio; los clientes nuevos empiezan con la plantilla genérica."
  type        = string
  default     = "plantilla"
}
