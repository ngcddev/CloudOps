# Recursos que registran el overlay del cliente y su Application de Argo CD (spec 011, T06).
terraform {
  required_providers {
    gitea = {
      source = "go-gitea/gitea"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
  }
}

resource "gitea_repository_file" "overlay" {
  username  = "forja-digital"
  name      = "hub-gitops"
  branch    = "main"
  file_path = "clients/${var.name}/kustomization.yaml"
  content = templatefile("${path.module}/overlay.tftpl", {
    name       = var.name
    host       = var.host
    plan       = var.plan
    quota      = var.quota
    image_tag  = var.image_tag
    image_name = var.image_name
  })
  commit_message = "feat(infra): crear overlay de ${var.name}"

  lifecycle {
    ignore_changes = [content]
  }
}

resource "kubernetes_manifest" "application" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name       = "cliente-${var.name}"
      namespace  = "argocd"
      finalizers = ["resources-finalizer.argocd.argoproj.io"]
      labels = {
        "hub/client" = var.name
      }
    }
    spec = {
      project = "default"
      source = {
        repoURL        = "http://gitea.gitea.svc:3000/forja-digital/hub-gitops.git"
        targetRevision = "main"
        path           = "clients/${var.name}"
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = "cliente-${var.name}"
      }
      syncPolicy = {
        automated = {
          prune    = true
          selfHeal = true
        }
      }
    }
  }

  depends_on = [gitea_repository_file.overlay]
}
