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
      env {
        name  = "MLFLOW_BACKEND_STORE_URI"
        value = "gs://${google_storage_bucket.mlflow.name}/mlflow-db"
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

# Update backend service to connect to MLflow
resource "google_cloud_run_v2_service" "backend_with_mlflow" {
  name     = "${var.project_name}-backend"
  location = var.region
  
  template {
    service_account = google_service_account.cloudrun_sa.email
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/backend:latest"
      
      ports {
        container_port = 8080
      }
      
      # Existing environment variables
      env {
        name  = "NEO4J_URI"
        value = var.neo4j_uri
      }
      
      env {
        name  = "NEO4J_USERNAME"
        value = var.neo4j_username
      }
      
      env {
        name = "NEO4J_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.neo4j_password.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      # NEW: MLflow connection
      env {
        name  = "MLFLOW_TRACKING_URI"
        value = google_cloud_run_v2_service.mlflow.uri
      }
      
      env {
        name  = "MLFLOW_EXPERIMENT_NAME"
        value = var.mlflow_experiment_name
      }
      
      env {
        name  = "MODEL_NAME"
        value = var.mlflow_model_name
      }
      
      env {
        name  = "MODEL_STAGE"
        value = "production"
      }
      
      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }
      
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle = true
      }
      
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 3
        period_seconds        = 30
      }
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = var.max_instances
    }
    
    timeout = "300s"
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_iam_member.openai_key_access,
    google_secret_manager_secret_iam_member.neo4j_password_access,
    google_cloud_run_v2_service.mlflow,  # Wait for MLflow to be ready
  ]
  
  lifecycle {
    create_before_destroy = true
  }
}

