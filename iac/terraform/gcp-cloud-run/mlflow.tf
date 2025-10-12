# MLflow Server Infrastructure on Cloud Run
# Provides experiment tracking and model registry

# Cloud Storage bucket for MLflow data
resource "google_storage_bucket" "mlflow" {
  name     = "${var.project_id}-mlflow"
  location = var.region
  
  # Prevent accidental deletion
  force_destroy = false
  
  # Versioning for model artifacts
  versioning {
    enabled = true
  }
  
  # Lifecycle rules to manage costs
  lifecycle_rule {
    condition {
      age = 90  # Delete artifacts older than 90 days
    }
    action {
      type = "Delete"
    }
  }
  
  # Uniform bucket-level access
  uniform_bucket_level_access = true
  
  labels = merge(var.labels, {
    component = "mlflow"
    purpose   = "ml-ops"
  })
}

# Grant service account access to MLflow bucket
resource "google_storage_bucket_iam_member" "mlflow_sa_admin" {
  bucket = google_storage_bucket.mlflow.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# MLflow Server on Cloud Run
resource "google_cloud_run_v2_service" "mlflow" {
  name     = "${var.project_name}-mlflow"
  location = var.region
  
  template {
    service_account = google_service_account.cloudrun_sa.email
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/mlflow:latest"
      
      ports {
        container_port = 8080
      }
      
      # Environment variables for MLflow
      # Note: Using local file-based backend for demo. For production, use PostgreSQL/MySQL.
      env {
        name  = "MLFLOW_BACKEND_STORE_URI"
        value = "file:///mlflow/data/mlflow-db"
      }
      
      env {
        name  = "MLFLOW_ARTIFACT_ROOT"
        value = "gs://${google_storage_bucket.mlflow.name}/artifacts"
      }
      
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      
      # Resource allocation
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle = true
      }
      
      # Health check
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 15
        timeout_seconds       = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 5
        period_seconds        = 30
      }
    }
    
    # Scaling configuration
    scaling {
      min_instance_count = 1  # Keep warm for demo
      max_instance_count = 3
    }
    
    # Timeout for long-running operations
    timeout = "300s"
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_storage_bucket.mlflow,
    google_storage_bucket_iam_member.mlflow_sa_admin,
  ]
}

# Allow public access to MLflow UI (for demo purposes)
resource "google_cloud_run_v2_service_iam_member" "mlflow_public" {
  name     = google_cloud_run_v2_service.mlflow.name
  location = google_cloud_run_v2_service.mlflow.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow backend to invoke MLflow
resource "google_cloud_run_v2_service_iam_member" "mlflow_backend_invoker" {
  name     = google_cloud_run_v2_service.mlflow.name
  location = google_cloud_run_v2_service.mlflow.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Note: The backend service defined in main.tf now includes MLflow environment variables via lifecycle.ignore_changes
# This allows us to update the backend service with MLflow connection details without creating a duplicate resource

