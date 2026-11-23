# Variables del despliegue en GCP (spec 024). Los valores van en terraform.tfvars (ignorado por Git).
variable "project_id" {
  description = "ID del proyecto de GCP con la facturación de prueba vinculada"
  type        = string
}

variable "region" {
  description = "Región de GCP"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zona de la VM"
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "Tipo de máquina; la pila completa necesita 8 GB"
  type        = string
  default     = "e2-standard-2"
}

variable "disk_gb" {
  description = "Tamaño del disco de arranque en GB"
  type        = number
  default     = 50
}

variable "k3s_version" {
  description = "Versión de k3s; debe ser la misma del laboratorio (ver gitops/ y docs)"
  type        = string
  default     = "v1.32.9+k3s1"
}

variable "ip_admin" {
  description = "IP pública del equipo en formato CIDR (ej. 190.1.2.3/32) con acceso a SSH y a la API de Kubernetes"
  type        = string

  validation {
    condition     = can(cidrhost(var.ip_admin, 0)) && var.ip_admin != "0.0.0.0/0"
    error_message = "ip_admin debe ser un CIDR válido y no 0.0.0.0/0."
  }
}
