# Configuración de los proveedores de Kubernetes y Gitea para OpenTofu/Terraform (spec 011, T03).
terraform {
  required_version = ">= 1.10.0" # use_lockfile (backend_remoto.tf.example) exige OpenTofu 1.10 o más (auditoría IA-03)

  backend "local" {
    path = "../state/terraform.tfstate"
  }

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "= 3.4.0"
    }
    gitea = {
      source  = "go-gitea/gitea"
      version = "= 0.8.1"
    }
  }
}

provider "kubernetes" {}

provider "gitea" {
  base_url = "http://gitea.hub.local"
  token    = var.gitea_token
}
