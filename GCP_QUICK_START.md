# 🚀 GCP Cloud Run Deployment - Quick Start

Deploy your GNN Attack Path demo to Google Cloud in **10-15 minutes**.

## Prerequisites Checklist

- [ ] GCP account with billing enabled ([Sign up](https://cloud.google.com/free))
- [ ] gcloud CLI installed ([Download](https://cloud.google.com/sdk/docs/install))
- [ ] Terraform installed ([Download](https://www.terraform.io/downloads))
- [ ] Docker installed ([Download](https://docs.docker.com/get-docker/))
- [ ] Neo4j Aura free account ([Sign up](https://neo4j.com/cloud/aura-free/))

## 3-Step Deployment

### Step 1: Setup (5 minutes)

```bash
# Clone repository (if not already done)
git clone https://github.com/yourusername/gnn_attack_path.git
cd gnn_attack_path

# Run interactive setup
./scripts/setup-gcp.sh
```

The script will guide you through:
- ✅ GCP project configuration
- ✅ Neo4j Aura connection
- ✅ OpenAI API key
- ✅ Secret storage
- ✅ Data loading

### Step 2: Deploy (5-10 minutes)

```bash
# Deploy infrastructure and application
./scripts/deploy-to-gcp.sh --full
```

This will:
- ✅ Create Cloud Run services
- ✅ Build and push Docker images
- ✅ Deploy frontend and backend
- ✅ Run health checks

### Step 3: Access (Instant)

```bash
# Get URLs
cd iac/terraform/gcp-cloud-run
terraform output frontend_url
terraform output backend_api_docs

# Or open directly
open $(terraform output -raw frontend_url)
```

## Your Demo is Live! 🎉

**Frontend**: https://gnn-demo-frontend-xxx.run.app  
**Backend**: https://gnn-demo-backend-xxx.run.app  
**API Docs**: https://gnn-demo-backend-xxx.run.app/docs

## What You Get

- ✅ **Live demo** accessible from anywhere
- ✅ **Auto-scaling** infrastructure
- ✅ **HTTPS** with automatic SSL
- ✅ **Monitoring** with Cloud Logging
- ✅ **Cost-effective** ~$7-20/month
- ✅ **Professional** architecture you can showcase

## Update Your Demo

Made code changes? Redeploy in minutes:

```bash
./scripts/deploy-to-gcp.sh
```

## Cleanup (When Done)

```bash
./scripts/teardown-gcp.sh
```

## Troubleshooting

### Service won't start?
```bash
# Check logs
gcloud logging read "resource.labels.service_name=gnn-demo-backend" --limit 20
```

### Connection to Neo4j fails?
```bash
# Verify credentials
gcloud secrets versions access latest --secret="neo4j-password"
```

### Need help?
- 📖 Full docs: [docs/GCP_DEPLOYMENT.md](docs/GCP_DEPLOYMENT.md)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/gnn_attack_path/issues)

## Cost Estimate

**Monthly costs for demo usage:**
- Cloud Run: $7-15
- Neo4j Aura Free: $0
- Total: ~$7-20/month

Can be reduced to <$5/month by scaling to zero when idle.

## Next Steps

1. **Share your demo** with the interview team
2. **Monitor performance** in Cloud Console
3. **Customize** for your needs
4. **Add features** and redeploy instantly

---

**Questions?** Check [docs/GCP_DEPLOYMENT.md](docs/GCP_DEPLOYMENT.md) for detailed documentation.

