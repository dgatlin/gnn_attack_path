# Variables for GCP Cloud Run deployment

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "gnn-demo"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "neo4j_uri" {
  description = "Neo4j connection URI (use Neo4j Aura or self-hosted)"
  type        = string
  default     = "neo4j+s://xxxxx.databases.neo4j.io"
}

variable "neo4j_username" {
  description = "Neo4j username"
  type        = string
  default     = "neo4j"
}

variable "enable_monitoring" {
  description = "Enable Cloud Monitoring and Logging"
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    environment = "demo"
    project     = "gnn-attack-path"
    managed_by  = "terraform"
  }
}

variable "mlflow_experiment_name" {
  description = "MLflow experiment name"
  type        = string
  default     = "gnn-attack-paths"
}

variable "mlflow_model_name" {
  description = "MLflow model name in registry"
  type        = string
  default     = "gnn-attack-path"
}

