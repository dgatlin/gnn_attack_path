# MLflow Integration on GCP Cloud Run

Complete guide for MLflow experiment tracking and model registry integration.

## Overview

MLflow is deployed as a separate Cloud Run service that provides:
- **Experiment Tracking**: Log parameters, metrics, and artifacts
- **Model Registry**: Version and manage production models
- **Artifact Storage**: Store models in Cloud Storage
- **UI Dashboard**: Web interface for viewing experiments

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                MLflow on Cloud Run                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  MLflow Server (Port 8080)                   │  │
│  │  - Tracking Server                           │  │
│  │  - Model Registry                            │  │
│  │  - Artifact Proxy                            │  │
│  └────────┬──────────────────┬──────────────────┘  │
│           │                  │                      │
│  ┌────────▼─────────┐  ┌────▼──────────────┐      │
│  │ Cloud Storage    │  │ Backend connects  │      │
│  │ Bucket           │  │ via URI           │      │
│  │                  │  │                   │      │
│  │ /mlflow-db/      │  │ MLFLOW_TRACKING_  │      │
│  │ /artifacts/      │  │ URI=https://...   │      │
│  └──────────────────┘  └───────────────────┘      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## What Was Created

### 1. Dockerfile (`ops/Dockerfile.mlflow`)
- Python 3.11 with MLflow 2.9.1
- Google Cloud Storage integration
- Health checks and monitoring
- Non-root user for security
- Port 8080 for Cloud Run

### 2. Terraform Configuration (`iac/terraform/gcp-cloud-run/mlflow.tf`)
- Cloud Storage bucket for MLflow data
- MLflow Cloud Run service
- IAM permissions for service account
- Backend integration (environment variables)
- Auto-scaling configuration (1-3 instances)

### 3. Updated Backend
- `MLFLOW_TRACKING_URI` environment variable
- Automatic connection to MLflow server
- Model loading from registry
- Experiment logging enabled

## Deployment

### Prerequisites
- GCP project with billing enabled
- Terraform and gcloud CLI installed
- Docker installed

### Deploy MLflow

MLflow is automatically deployed when you run:

```bash
./scripts/deploy-to-gcp.sh --full
```

This will:
1. Build the MLflow Docker image
2. Push to Artifact Registry
3. Create Cloud Storage bucket
4. Deploy MLflow service to Cloud Run
5. Configure backend to connect

### Manual Deployment

If you want to deploy only MLflow:

```bash
# Build MLflow image
docker build -f ops/Dockerfile.mlflow -t mlflow:latest .

# Get Artifact Registry URL
cd iac/terraform/gcp-cloud-run
REGISTRY=$(terraform output -raw artifact_registry)
cd ../../..

# Tag and push
docker tag mlflow:latest $REGISTRY/mlflow:latest
docker push $REGISTRY/mlflow:latest

# Apply Terraform (mlflow.tf will be included)
cd iac/terraform/gcp-cloud-run
terraform apply
cd ../../..
```

## Usage

### Access MLflow UI

After deployment, get the MLflow URL:

```bash
cd iac/terraform/gcp-cloud-run
terraform output mlflow_url
```

Visit the URL in your browser to see:
- Experiments dashboard
- Model registry
- Artifact browser

### Backend Connection

The backend automatically connects to MLflow using environment variables:

```bash
MLFLOW_TRACKING_URI=https://gnn-demo-mlflow-xxx.run.app
MLFLOW_EXPERIMENT_NAME=gnn-attack-paths
MODEL_NAME=gnn-attack-path
MODEL_STAGE=production
```

### Log Experiments

In your training code:

```python
import mlflow

# Set tracking URI (already set in backend via env var)
mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))

# Create or get experiment
experiment = mlflow.set_experiment("gnn-attack-paths")

# Start a run
with mlflow.start_run(run_name="graphsage_v1"):
    # Log parameters
    mlflow.log_param("hidden_dim", 128)
    mlflow.log_param("learning_rate", 0.001)
    
    # Train model
    # ...
    
    # Log metrics
    mlflow.log_metric("accuracy", 0.94)
    mlflow.log_metric("f1_score", 0.92)
    
    # Log model
    mlflow.pytorch.log_model(model, "model")
```

### Register Model

After training, register the best model:

```python
# Get the best run
client = mlflow.tracking.MlflowClient()
experiment = client.get_experiment_by_name("gnn-attack-paths")
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.accuracy DESC"],
    max_results=1
)

best_run = runs[0]

# Register model
model_uri = f"runs:/{best_run.info.run_id}/model"
model_details = mlflow.register_model(
    model_uri=model_uri,
    name="gnn-attack-path"
)

# Tag as production
client.set_registered_model_alias(
    name="gnn-attack-path",
    alias="production",
    version=model_details.version
)
```

### Load Model in Backend

The backend automatically loads the production model:

```python
# scorer/service.py
import mlflow.pytorch

def _load_model_from_mlflow(self):
    """Load production model from MLflow Registry."""
    model_uri = f"models:/{self.model_name}/production"
    model = mlflow.pytorch.load_model(model_uri)
    return model
```

## Populate Demo Data

To show ML Ops history in your demo:

```bash
# Generate demo experiment history
python scripts/generate-mlops-history.py

# Setup MLflow with demo data
./scripts/setup-mlflow-data.sh
```

This creates realistic:
- 50 Optuna trials
- Multiple model versions
- Training metrics over time
- Model evolution timeline

## Storage Structure

Your Cloud Storage bucket contains:

```
gs://your-project-mlflow/
├── mlflow-db/
│   └── (SQLite database with experiment metadata)
├── artifacts/
│   ├── 0/                    (experiment ID)
│   │   ├── abc123/           (run ID)
│   │   │   ├── artifacts/
│   │   │   │   └── model/
│   │   │   │       └── model.pth
│   │   │   └── metrics/
│   │   │       ├── accuracy
│   │   │       └── loss
│   └── models/
│       └── gnn-attack-path/  (registered model)
│           ├── version-1/
│           └── version-2/    (production)
```

## API Endpoints

MLflow provides REST API:

```bash
# Get experiments
curl https://your-mlflow-url.run.app/api/2.0/mlflow/experiments/list

# Get runs
curl https://your-mlflow-url.run.app/api/2.0/mlflow/runs/search \
  -d '{"experiment_ids": ["0"]}'

# Get registered models
curl https://your-mlflow-url.run.app/api/2.0/mlflow/registered-models/list
```

## Cost Optimization

**Monthly costs:**
- MLflow Cloud Run: $3-5/month (1-3 instances)
- Cloud Storage: $1-2/month (artifacts)
- **Total: $4-7/month**

**Optimization tips:**
1. Set `min_instances = 0` to scale to zero when idle
2. Enable lifecycle rules to delete old artifacts (already configured for 90 days)
3. Use versioning to track model history without duplicating storage

## Monitoring

### View Logs

```bash
# MLflow service logs
gcloud logging read \
  "resource.labels.service_name=gnn-demo-mlflow" \
  --limit 50 \
  --format json
```

### Health Check

```bash
# Check MLflow health
curl https://your-mlflow-url.run.app/health
```

### Metrics

MLflow automatically logs to Cloud Monitoring:
- Request rate
- Response latency
- Error rate
- Instance count

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
gcloud logging read \
  "resource.labels.service_name=gnn-demo-mlflow" \
  --limit 20
```

**Common issues:**
- Bucket permissions not set correctly
- Service account missing roles
- Environment variables not configured

### Backend Can't Connect

**Verify environment variable:**
```bash
gcloud run services describe gnn-demo-backend \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

Should include `MLFLOW_TRACKING_URI`

### Models Not Loading

**Check model registry:**
```bash
# Via Python
import mlflow
mlflow.set_tracking_uri("https://your-mlflow-url.run.app")
client = mlflow.tracking.MlflowClient()
models = client.search_registered_models()
print(models)
```

## Security

**For production use:**

1. **Remove public access:**
   ```hcl
   # In mlflow.tf, remove or comment out:
   resource "google_cloud_run_v2_service_iam_member" "mlflow_public" {
     # ...
   }
   ```

2. **Add authentication:**
   - Use Cloud Run authentication
   - Implement API key validation
   - Use Cloud IAM for service-to-service

3. **Encrypt artifacts:**
   - Enable encryption at rest (default in GCS)
   - Use customer-managed encryption keys

## Next Steps

1. **Run training:** `python examples/gnn_optimization_example.py`
2. **View experiments:** Visit MLflow UI
3. **Register model:** Tag best model as production
4. **Backend loads:** Automatically uses production model

## References

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)

