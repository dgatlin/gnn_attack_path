# GCP Cloud Run Infrastructure for GNN Attack Path Demo
# This configuration deploys a production-ready demo on Cloud Run

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  # Uncomment to use remote state (recommended for team collaboration)
  # backend "gcs" {
  #   bucket = "gnn-demo-terraform-state"
  #   prefix = "cloud-run"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required GCP APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])
  
  service = each.key
  disable_on_destroy = false
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "${var.project_name}-images"
  description   = "Docker images for GNN Attack Path Demo"
  format        = "DOCKER"
  
  depends_on = [google_project_service.required_apis]
}

# Secret Manager for sensitive configuration
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret" "neo4j_password" {
  secret_id = "neo4j-password"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

# Service Account for Cloud Run services
resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.project_name}-cloudrun"
  display_name = "Cloud Run Service Account for GNN Demo"
  description  = "Service account used by Cloud Run services"
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "openai_key_access" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "neo4j_password_access" {
  secret_id = google_secret_manager_secret.neo4j_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Backend API Service
# Note: Full backend configuration with MLflow is in mlflow.tf
# This is a placeholder that gets replaced when mlflow.tf is applied
resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.project_name}-backend"
  location = var.region
  
  template {
    service_account = google_service_account.cloudrun_sa.email
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/backend:latest"
      
      ports {
        container_port = 8080
      }
      
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
      
      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }
      
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
      
      # MLflow configuration
      env {
        name  = "MLFLOW_TRACKING_URI"
        value = google_cloud_run_v2_service.mlflow.uri
      }
      
      env {
        name  = "MLFLOW_MODEL_RUN_ID"
        value = "latest"
      }
      
      env {
        name  = "MLFLOW_EXPERIMENT_NAME"
        value = var.mlflow_experiment_name
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
  ]
  
  lifecycle {
    ignore_changes = [
      template[0].containers[0].env,  # Ignore env changes (managed in mlflow.tf)
    ]
  }
}

# Frontend UI Service
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.project_name}-frontend"
  location = var.region
  
  template {
    service_account = google_service_account.cloudrun_sa.email
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/frontend:latest"
      
      ports {
        container_port = 8080
      }
      
      env {
        name  = "REACT_APP_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = var.max_instances
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_cloud_run_v2_service.backend,
  ]
}

# Allow public access to frontend
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow public access to backend (for demo purposes)
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow frontend to invoke backend
resource "google_cloud_run_v2_service_iam_member" "backend_frontend_invoker" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

