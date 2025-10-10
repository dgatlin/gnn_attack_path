# GCP Cloud Run Deployment

This directory contains Terraform configuration for deploying the GNN Attack Path demo to Google Cloud Run.

## Architecture

```
┌─────────────────────────────────────┐
│   Cloud Load Balancer (HTTPS)       │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────────┐   ┌─────▼────────┐
│  Frontend  │   │   Backend    │
│ Cloud Run  │   │  Cloud Run   │
│ (React)    │   │  (FastAPI)   │
└───┬────────┘   └─────┬────────┘
    │                  │
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │   Neo4j Aura     │
    │  (Managed)       │
    └──────────────────┘
```

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Terraform** >= 1.0 installed
4. **Docker** installed
5. **Neo4j Aura** account (free tier available)

## Quick Start

### 1. Setup GCP Project

```bash
# Set your project ID
export GCP_PROJECT_ID="your-gcp-project-id"

# Login to GCP
gcloud auth login
gcloud auth application-default login

# Set the project
gcloud config set project $GCP_PROJECT_ID

# Enable billing (if not already enabled)
# Visit: https://console.cloud.google.com/billing
```

### 2. Setup Neo4j Aura (Free Tier)

1. Go to https://neo4j.com/cloud/aura-free/
2. Create a free database
3. Save the connection URI and password
4. Note: Connection URI format: `neo4j+s://xxxxx.databases.neo4j.io`

### 3. Configure Terraform

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Update these values:
```hcl
project_id     = "your-gcp-project-id"
neo4j_uri      = "neo4j+s://xxxxx.databases.neo4j.io"
neo4j_username = "neo4j"
```

### 4. Store Secrets

```bash
# Store Neo4j password
echo -n "your-neo4j-password" | gcloud secrets create neo4j-password \
  --data-file=- \
  --replication-policy="automatic"

# Store OpenAI API key
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key \
  --data-file=- \
  --replication-policy="automatic"
```

### 5. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply configuration
terraform apply
```

This will:
- Enable required GCP APIs
- Create Artifact Registry for Docker images
- Setup Secret Manager for credentials
- Create Cloud Run services (after you build images)
- Configure IAM permissions

### 6. Build and Deploy Application

Use the deployment script from the repo root:

```bash
# From repository root
./scripts/deploy-to-gcp.sh
```

Or manually:

```bash
# Set variables
export PROJECT_ID=$(terraform output -raw project_id)
export REGION=$(terraform output -raw region)
export REPO=$(terraform output -raw artifact_registry)

# Build and push backend
cd ../../../
docker build -f ops/Dockerfile.cloudrun.api -t $REPO/backend:latest .
docker push $REPO/backend:latest

# Build and push frontend
docker build -f ops/Dockerfile.cloudrun.ui -t $REPO/frontend:latest .
docker push $REPO/frontend:latest

# Update Cloud Run services
gcloud run services update gnn-demo-backend \
  --image=$REPO/backend:latest \
  --region=$REGION

gcloud run services update gnn-demo-frontend \
  --image=$REPO/frontend:latest \
  --region=$REGION
```

### 7. Access Your Demo

```bash
# Get URLs
terraform output frontend_url
terraform output backend_api_docs

# Open frontend
open $(terraform output -raw frontend_url)

# Open API docs
open $(terraform output -raw backend_api_docs)
```

## Cost Estimation

**Monthly costs for demo usage (~100K requests/month):**

| Service | Cost |
|---------|------|
| Cloud Run (Frontend) | $2-5 |
| Cloud Run (Backend) | $5-10 |
| Artifact Registry | $0.10 |
| Secret Manager | $0.06 |
| Cloud Logging | $0-5 |
| Neo4j Aura Free | $0 |
| **Total** | **$7-20/month** |

**Cost optimization tips:**
- Use minimum instances: 0 (scales to zero when idle)
- Set max instances: 3-5 for demo
- Use Neo4j Aura free tier
- Enable Cloud Run CPU allocation: "CPU is only allocated during request processing"

## Monitoring

### View Logs

```bash
# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gnn-demo-backend" \
  --limit 50 \
  --format json

# Frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gnn-demo-frontend" \
  --limit 50 \
  --format json

# Tail logs in real-time
gcloud alpha logging tail "resource.type=cloud_run_revision" --format json
```

### View Metrics

```bash
# Open Cloud Console
open "https://console.cloud.google.com/run?project=$PROJECT_ID"

# View metrics via gcloud
gcloud monitoring dashboards list
```

### Health Checks

```bash
# Check backend health
curl $(terraform output -raw backend_url)/health

# Check frontend
curl $(terraform output -raw frontend_url)
```

## Updating the Deployment

```bash
# Make code changes, then rebuild and redeploy
./scripts/deploy-to-gcp.sh

# Or use Terraform to update infrastructure
terraform plan
terraform apply
```

## Troubleshooting

### Service not starting

```bash
# Check service status
gcloud run services describe gnn-demo-backend --region=us-central1

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format json

# Check container image
gcloud artifacts docker images list $REPO
```

### Connection to Neo4j fails

```bash
# Test Neo4j connection
export NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io"
export NEO4J_PASSWORD="your-password"

python3 << EOF
from neo4j import GraphDatabase
driver = GraphDatabase.driver("$NEO4J_URI", auth=("neo4j", "$NEO4J_PASSWORD"))
driver.verify_connectivity()
print("✓ Connected successfully")
driver.close()
EOF
```

### Secret not found

```bash
# List secrets
gcloud secrets list

# Create missing secret
echo -n "your-secret-value" | gcloud secrets create secret-name \
  --data-file=- \
  --replication-policy="automatic"
```

## Cleanup

To avoid ongoing charges:

```bash
# Destroy all resources
terraform destroy

# Or use the cleanup script
cd ../../../
./scripts/teardown-gcp.sh
```

## Security Notes

**For production use, consider:**
- Remove public access to backend API
- Implement API authentication
- Use Cloud Armor for DDoS protection
- Enable VPC Service Controls
- Implement rate limiting
- Use Cloud CDN for frontend
- Enable Binary Authorization
- Regular security scanning

## Advanced Configuration

### Custom Domain

```bash
# Map custom domain to Cloud Run
gcloud run domain-mappings create \
  --service=gnn-demo-frontend \
  --domain=demo.yourdomain.com \
  --region=us-central1
```

### Autoscaling

Edit `main.tf`:

```hcl
scaling {
  min_instance_count = 0  # Scale to zero when idle
  max_instance_count = 20
}
```

### Environment-specific Deployments

```bash
# Create staging environment
terraform workspace new staging
terraform apply -var-file=staging.tfvars

# Switch to production
terraform workspace select production
terraform apply -var-file=production.tfvars
```

## Support

- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/google/latest/docs
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Neo4j Aura**: https://neo4j.com/docs/aura/
- **Project Issues**: https://github.com/yourusername/gnn_attack_path/issues

