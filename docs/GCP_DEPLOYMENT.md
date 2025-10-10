# GCP Cloud Run Deployment Guide

Complete guide for deploying the GNN Attack Path demo to Google Cloud Run.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Cost Management](#cost-management)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [CI/CD Setup](#cicd-setup)
- [Advanced Configuration](#advanced-configuration)

## Overview

This deployment uses Google Cloud Run for a serverless, auto-scaling demo with minimal operational overhead.

**Key Benefits:**
- ✅ **Serverless** - No infrastructure management
- ✅ **Cost-effective** - Pay only for actual usage (~$7-20/month for demo)
- ✅ **Auto-scaling** - Handles traffic spikes automatically
- ✅ **HTTPS built-in** - Automatic SSL certificates
- ✅ **Fast deployment** - Deploy in 10-15 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Google Cloud Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────┐        │
│  │     Cloud Load Balancer (HTTPS)            │        │
│  └───────────────┬────────────────────────────┘        │
│                  │                                       │
│        ┌─────────┴─────────┐                           │
│        │                   │                           │
│  ┌─────▼──────┐     ┌─────▼──────┐                    │
│  │  Frontend  │     │  Backend   │                    │
│  │ Cloud Run  │     │ Cloud Run  │                    │
│  │  (React)   │────▶│ (FastAPI)  │                    │
│  │  Port 8080 │     │ Port 8080  │                    │
│  └────────────┘     └─────┬──────┘                    │
│                           │                            │
│  ┌────────────────────────┴──────────────────────┐    │
│  │        Artifact Registry                       │    │
│  │        (Docker Images)                         │    │
│  └────────────────────────────────────────────────┘    │
│                           │                            │
│  ┌────────────────────────┴──────────────────────┐    │
│  │        Secret Manager                          │    │
│  │   (API Keys, Passwords)                        │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────┬───────────────────────────────┘
                           │
                  ┌────────▼─────────┐
                  │   Neo4j Aura     │
                  │  (Managed DB)    │
                  └──────────────────┘
```

## Prerequisites

### Required Tools

1. **gcloud CLI**
   ```bash
   # Install on macOS
   brew install --cask google-cloud-sdk
   
   # Or download from:
   # https://cloud.google.com/sdk/docs/install
   ```

2. **Terraform** (>= 1.0)
   ```bash
   # Install on macOS
   brew tap hashicorp/tap
   brew install hashicorp/tap/terraform
   ```

3. **Docker**
   ```bash
   # Download from: https://docs.docker.com/get-docker/
   ```

### Required Accounts

1. **GCP Account** with billing enabled
   - Sign up: https://cloud.google.com/free
   - $300 free credit for new users

2. **Neo4j Aura Free Account**
   - Sign up: https://neo4j.com/cloud/aura-free/
   - Free tier includes 50K nodes, 175K relationships

## Quick Start

### One-Command Setup

```bash
# 1. Clone the repository (if not already done)
git clone https://github.com/yourusername/gnn_attack_path.git
cd gnn_attack_path

# 2. Run the setup script
./scripts/setup-gcp.sh

# 3. Deploy everything
./scripts/deploy-to-gcp.sh --full

# 4. Access your live demo
# URLs will be displayed after deployment
```

That's it! Your demo should be live in 10-15 minutes.

## Detailed Setup

### Step 1: GCP Project Setup

```bash
# Login to GCP
gcloud auth login
gcloud auth application-default login

# Create a new project (or use existing)
export PROJECT_ID="gnn-demo-$(date +%s)"
gcloud projects create $PROJECT_ID --name="GNN Attack Path Demo"

# Set the project
gcloud config set project $PROJECT_ID

# Enable billing (required for Cloud Run)
# Visit: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID
```

### Step 2: Neo4j Aura Setup

1. **Create Free Database**
   - Go to: https://neo4j.com/cloud/aura-free/
   - Click "Start Free"
   - Create a new database
   - **Save the connection details!**
   
2. **Note Your Credentials**
   ```
   URI:      neo4j+s://xxxxx.databases.neo4j.io
   Username: neo4j
   Password: <generated-password>
   ```

### Step 3: Run Setup Script

```bash
./scripts/setup-gcp.sh
```

This interactive script will:
- ✅ Check prerequisites
- ✅ Configure GCP project and region
- ✅ Enable required APIs
- ✅ Setup Neo4j connection
- ✅ Store secrets securely
- ✅ Create Terraform configuration
- ✅ Initialize infrastructure
- ✅ Load synthetic data

### Step 4: Deploy Infrastructure

```bash
cd iac/terraform/gcp-cloud-run

# Review what will be created
terraform plan

# Create the infrastructure
terraform apply

cd ../../..
```

This creates:
- Artifact Registry for Docker images
- Secret Manager for credentials
- Cloud Run services (placeholder)
- IAM service accounts and permissions

### Step 5: Build and Deploy Application

```bash
./scripts/deploy-to-gcp.sh
```

This will:
- ✅ Build Docker images
- ✅ Push to Artifact Registry
- ✅ Deploy to Cloud Run
- ✅ Run health checks
- ✅ Display service URLs

### Step 6: Access Your Demo

```bash
# Get URLs from Terraform
cd iac/terraform/gcp-cloud-run
terraform output frontend_url
terraform output backend_api_docs

# Or use gcloud
gcloud run services list --platform managed
```

Open the frontend URL in your browser!

## Cost Management

### Monthly Cost Breakdown

**Typical demo usage (~100K requests/month):**

| Service | Cost | Notes |
|---------|------|-------|
| Cloud Run (Backend) | $5-10 | 2 vCPU, 2GB RAM |
| Cloud Run (Frontend) | $2-5 | 1 vCPU, 512MB RAM |
| Artifact Registry | $0.10 | <1GB storage |
| Secret Manager | $0.06 | 2 active secrets |
| Cloud Logging | $0-5 | First 50GB free |
| Neo4j Aura Free | $0 | Free tier |
| **Total** | **$7-20/month** | Can be lower with scale-to-zero |

### Cost Optimization Tips

1. **Scale to Zero**
   ```hcl
   # In main.tf
   scaling {
     min_instance_count = 0  # Scale to zero when idle
     max_instance_count = 10
   }
   ```

2. **Use CPU allocation efficiently**
   - Cloud Run only bills for CPU during request processing
   - This is already configured in our setup

3. **Monitor usage**
   ```bash
   # Check Cloud Run costs
   gcloud billing accounts list
   gcloud billing budgets list
   ```

4. **Set budget alerts**
   ```bash
   # Create a budget alert at $20
   gcloud billing budgets create \
     --billing-account=<BILLING_ACCOUNT_ID> \
     --display-name="GNN Demo Budget" \
     --budget-amount=20USD \
     --threshold-rule=percent=80
   ```

## Monitoring & Troubleshooting

### View Logs

```bash
# Backend logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=gnn-demo-backend" \
  --limit 50 \
  --format json

# Frontend logs  
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=gnn-demo-frontend" \
  --limit 50 \
  --format json

# Tail logs in real-time
gcloud alpha logging tail "resource.type=cloud_run_revision" --format json
```

### Check Service Health

```bash
# Backend health
BACKEND_URL=$(gcloud run services describe gnn-demo-backend \
  --region=us-central1 \
  --format="value(status.url)")
curl $BACKEND_URL/health

# Check service status
gcloud run services describe gnn-demo-backend --region=us-central1
gcloud run services describe gnn-demo-frontend --region=us-central1
```

### Common Issues

#### 1. Service not starting

**Symptoms:** Service shows "Container failed to start"

**Solution:**
```bash
# Check logs for error messages
gcloud logging read \
  "resource.labels.service_name=gnn-demo-backend" \
  --limit 20

# Common fixes:
# - Check environment variables
# - Verify secret access permissions
# - Ensure port 8080 is exposed
```

#### 2. Neo4j connection fails

**Symptoms:** Backend returns 500 errors, logs show connection timeout

**Solution:**
```bash
# Verify Neo4j credentials in Secret Manager
gcloud secrets versions access latest --secret="neo4j-password"

# Test connection locally
python3 << 'EOF'
from neo4j import GraphDatabase
uri = "neo4j+s://xxxxx.databases.neo4j.io"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
driver.verify_connectivity()
print("✓ Connected")
driver.close()
EOF

# Update secret if needed
echo -n "new-password" | gcloud secrets versions add neo4j-password --data-file=-
```

#### 3. Permission errors

**Symptoms:** "Permission denied" errors in logs

**Solution:**
```bash
# Grant Secret Manager access to service account
SA_EMAIL=$(gcloud iam service-accounts list \
  --filter="email:gnn-demo-cloudrun*" \
  --format="value(email)")

gcloud secrets add-iam-policy-binding neo4j-password \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Performance Monitoring

```bash
# View Cloud Run metrics in console
open "https://console.cloud.google.com/run?project=$PROJECT_ID"

# Get request metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"' \
  --format=json

# Get latency metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"' \
  --format=json
```

## CI/CD Setup

### GitHub Actions Workflow

The project includes a GitHub Actions workflow for automated deployment.

**Setup:**

1. **Create GCP Service Account**
   ```bash
   # Create service account
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions CI/CD"
   
   # Grant permissions
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/artifactregistry.writer"
   
   # Create key
   gcloud iam service-accounts keys create key.json \
     --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Add GitHub Secrets**
   
   Go to: Settings → Secrets and variables → Actions
   
   Add these secrets:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_SA_KEY`: Contents of `key.json` file
   
3. **Push to trigger deployment**
   ```bash
   git add .
   git commit -m "Setup GCP deployment"
   git push origin main
   ```

The workflow will automatically:
- Run tests
- Build Docker images
- Deploy to Cloud Run
- Run health checks

## Advanced Configuration

### Custom Domain

```bash
# Map custom domain to Cloud Run
gcloud run domain-mappings create \
  --service=gnn-demo-frontend \
  --domain=demo.yourdomain.com \
  --region=us-central1

# Follow DNS instructions provided
```

### Environment-Specific Deployments

```bash
# Create staging environment
cd iac/terraform/gcp-cloud-run
terraform workspace new staging
terraform apply -var-file=staging.tfvars

# Create production environment
terraform workspace new production
terraform apply -var-file=production.tfvars
```

### Enable Cloud CDN

```bash
# For better frontend performance
gcloud compute backend-services update gnn-demo-frontend \
  --enable-cdn \
  --region=us-central1
```

### Increase Security

```bash
# Remove public access (requires authentication)
gcloud run services remove-iam-policy-binding gnn-demo-backend \
  --region=us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"

# Implement API key authentication in your code
```

## Cleanup

To avoid ongoing charges:

```bash
# Option 1: Use teardown script
./scripts/teardown-gcp.sh

# Option 2: Manual Terraform destroy
cd iac/terraform/gcp-cloud-run
terraform destroy

# Option 3: Delete entire project
gcloud projects delete $PROJECT_ID
```

## Next Steps

- **Monitor Performance**: Set up Cloud Monitoring dashboards
- **Custom Domain**: Configure your own domain name
- **Scale Up**: Adjust instance limits for production
- **Implement Auth**: Add authentication for production use
- **Enable CDN**: Improve frontend performance globally
- **Backup Neo4j**: Set up automated database backups

## Support

- **Documentation**: See [README.md](../README.md) for project overview
- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/google/latest/docs
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Issues**: https://github.com/yourusername/gnn_attack_path/issues

---

**Questions?** Open an issue or check the troubleshooting section above.

