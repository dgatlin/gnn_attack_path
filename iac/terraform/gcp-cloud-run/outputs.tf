# Outputs for GCP Cloud Run deployment

output "frontend_url" {
  description = "URL of the frontend service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_url" {
  description = "URL of the backend API service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "backend_api_docs" {
  description = "URL of the backend API documentation"
  value       = "${google_cloud_run_v2_service.backend.uri}/docs"
}

output "artifact_registry" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "service_account_email" {
  description = "Service account email for Cloud Run services"
  value       = google_service_account.cloudrun_sa.email
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "mlflow_url" {
  description = "URL of the MLflow tracking server"
  value       = google_cloud_run_v2_service.mlflow.uri
}

output "mlflow_bucket" {
  description = "Cloud Storage bucket for MLflow artifacts"
  value       = google_storage_bucket.mlflow.name
}

output "deployment_info" {
  description = "Quick access information"
  value = {
    frontend        = google_cloud_run_v2_service.frontend.uri
    backend         = google_cloud_run_v2_service.backend.uri
    mlflow          = google_cloud_run_v2_service.mlflow.uri
    api_docs        = "${google_cloud_run_v2_service.backend.uri}/docs"
    mlflow_bucket   = google_storage_bucket.mlflow.name
    logs_command    = "gcloud logging read 'resource.type=cloud_run_revision' --limit 50 --format json"
    metrics_command = "gcloud monitoring dashboards list"
  }
}

