# Salidas del despliegue en GCP (spec 024).
output "ip_publica" {
  description = "IP estática del Hub"
  value       = google_compute_address.hub.address
}

output "host_sslip" {
  description = "Dirección HTTPS base sin dominio propio"
  value       = "${replace(google_compute_address.hub.address, ".", "-")}.sslip.io"
}

output "bucket_respaldo" {
  description = "Bucket para los respaldos de la base y de la plataforma"
  value       = google_storage_bucket.respaldo.name
}

output "ssh" {
  description = "Comando para entrar a la VM"
  value       = "gcloud compute ssh hub --zone ${var.zone} --project ${var.project_id}"
}
