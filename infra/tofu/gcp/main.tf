# Red, cortafuegos, IP estática, bucket de respaldo y la VM del Hub en GCP (spec 024, T04 y T05).
terraform {
  required_version = ">= 1.10.0"

  # Estado local propio, separado del de los clientes (infra/tofu). No se sube a Git (*.tfstate está ignorado).
  backend "local" {
    path = "../../state/gcp.tfstate"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "hub" {
  name                    = "hub-red"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "hub" {
  name          = "hub-subred"
  ip_cidr_range = "10.20.0.0/24"
  region        = var.region
  network       = google_compute_network.hub.id
}

resource "google_compute_address" "hub" {
  name   = "hub-ip"
  region = var.region
}

# Solo 80 y 443 abiertos al mundo.
resource "google_compute_firewall" "web" {
  name    = "hub-web"
  network = google_compute_network.hub.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["hub"]
}

# SSH y la API de Kubernetes (6443) solo desde la IP del equipo.
resource "google_compute_firewall" "admin" {
  name    = "hub-admin"
  network = google_compute_network.hub.name

  allow {
    protocol = "tcp"
    ports    = ["22", "6443"]
  }

  source_ranges = [var.ip_admin]
  target_tags   = ["hub"]
}

# Cuenta de servicio de la VM: solo escribe en el bucket de respaldo.
resource "google_service_account" "vm" {
  account_id   = "hub-vm"
  display_name = "VM del CloudOps Hub"
}

resource "google_storage_bucket" "respaldo" {
  name                        = "${var.project_id}-hub-respaldo"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_iam_member" "vm_respaldo" {
  bucket = google_storage_bucket.respaldo.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.vm.email}"
}

resource "google_compute_instance" "hub" {
  name         = "hub"
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["hub"]

  # Se puede apagar sin que Tofu la recree (infra/gcp/apagar.sh).
  desired_status = "RUNNING"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = var.disk_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.hub.id
    access_config {
      nat_ip = google_compute_address.hub.address
    }
  }

  service_account {
    email  = google_service_account.vm.email
    scopes = ["https://www.googleapis.com/auth/devstorage.read_write"]
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  metadata_startup_script = templatefile("${path.module}/arranque.sh.tftpl", {
    ip_publica  = google_compute_address.hub.address
    k3s_version = var.k3s_version
  })

  # Evita recrear la VM (y perder k3s) por cambios del script de arranque; para aplicarlo, usar -replace.
  lifecycle {
    ignore_changes = [metadata_startup_script, desired_status]
  }
}
