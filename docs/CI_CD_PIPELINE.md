# CI/CD Pipeline

## Workflows

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `ci-frontend.yml` | Frontend testing | `ui/**` changes | ✅ Working |
| `ci-backend.yml` | Backend testing | `api/**`, `agent/**` changes | ✅ Working |
| `ci-integration.yml` | E2E testing | `main`/`develop` | ✅ Working |
| `security.yml` | Security scanning | Weekly | ✅ Working |
| `performance.yml` | Performance testing | Weekly | ✅ Working |
| `deploy-staging.yml` | Staging deployment | `main`/`develop` | ⚠️ Needs AWS secrets |
| `deploy-production.yml` | Production deployment | Version tags | ⚠️ Needs AWS secrets |
| `cleanup.yml` | Resource cleanup | Weekly | ✅ Working |

## Current Status

**✅ Working (No secrets required):**
- Frontend CI: Tests, linting, building
- Backend CI: Tests, security scanning, performance
- Integration tests: E2E testing with mock data
- Security scanning: Vulnerability detection
- Performance testing: Load testing

**⚠️ Limited (Secrets required):**
- Staging deployment: Builds images, skips AWS deployment
- Production deployment: Requires manual intervention
- Notifications: Slack/Teams webhooks not configured

## Required Secrets

| Secret | Purpose | Required |
|--------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS deployment | Optional |
| `AWS_SECRET_ACCESS_KEY` | AWS deployment | Optional |
| `SLACK_WEBHOOK` | Notifications | Optional |
| `OPENAI_API_KEY` | AI features | Optional |

## Quick Commands

```bash
# Check workflow status
gh run list

# View logs
gh run view <run-id> --log

# Test locally
make test
make frontend-test
```

## Configuration

### Current Secret Status

**⚠️ Note**: Currently, no secrets are configured in this repository. The workflows are designed to run gracefully without secrets, but some features will be limited.

### Required Secrets (For Full Functionality)

| Secret | Purpose | Workflow | Status |
|--------|---------|----------|--------|
| `AWS_ACCESS_KEY_ID` | AWS authentication | Deploy, Cleanup | ❌ Not configured |
| `AWS_SECRET_ACCESS_KEY` | AWS authentication | Deploy, Cleanup | ❌ Not configured |
| `SLACK_WEBHOOK` | Notifications | Deploy, Cleanup | ❌ Not configured |
| `TEAMS_WEBHOOK` | Notifications | Deploy | ❌ Not configured |
| `SNYK_TOKEN` | Security scanning | Frontend, Security | ❌ Not configured |
| `WEBPAGETEST_API_KEY` | Performance testing | Performance | ❌ Not configured |

### Optional Secrets (For Enhanced Features)

| Secret | Purpose | Workflow | Impact if Missing |
|--------|---------|----------|-------------------|
| `OPENAI_API_KEY` | AI agent functionality | Backend, Agent | Mock responses only |
| `NEO4J_URI` | Database connection | Backend, Agent | Mock data only |
| `NEO4J_USERNAME` | Database authentication | Backend, Agent | Mock data only |
| `NEO4J_PASSWORD` | Database authentication | Backend, Agent | Mock data only |

### Environment Variables

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `NODE_ENV` | Node environment | `production` | No |
| `PYTHON_VERSION` | Python version | `3.11` | No |
| `NEO4J_URI` | Database connection | `bolt://localhost:7687` | No |
| `MLFLOW_TRACKING_URI` | MLflow tracking | `sqlite:///mlflow.db` | No |

### Setting Up Secrets

To enable full functionality, configure the following secrets in your GitHub repository:

1. **Go to Repository Settings** → **Secrets and variables** → **Actions**
2. **Click "New repository secret"** for each secret below:

#### For Deployment (Optional)
```bash
# AWS Credentials (for ECS deployment)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Notifications
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
TEAMS_WEBHOOK=https://your-org.webhook.office.com/webhookb2/YOUR/TEAMS/WEBHOOK
```

#### For Security Scanning (Optional)
```bash
# Snyk security scanning
SNYK_TOKEN=your_snyk_token

# Performance testing
WEBPAGETEST_API_KEY=your_webpagetest_api_key
```

#### For AI Features (Optional)
```bash
# OpenAI API for AI agent
OPENAI_API_KEY=sk-your_openai_api_key
```

### Current Workflow Behavior

**Without Secrets Configured:**
- ✅ **Frontend CI**: Runs tests, builds, linting
- ✅ **Backend CI**: Runs tests, security scans, performance tests
- ✅ **Integration Tests**: Runs with mock data
- ⚠️ **Staging Deployment**: Builds images but skips AWS deployment
- ⚠️ **Production Deployment**: Requires manual intervention
- ⚠️ **Notifications**: Skipped gracefully
- ⚠️ **AI Features**: Uses mock responses

## Maintenance

### Regular Tasks
1. **Weekly**: Review security reports
2. **Monthly**: Update dependencies
3. **Quarterly**: Performance optimization
4. **Annually**: Security audit

### Updates
1. **Workflow updates**: Regular GitHub Actions updates
2. **Dependency updates**: Security and feature updates
3. **Infrastructure updates**: AWS service updates
4. **Monitoring updates**: Alert and dashboard improvements

## Support

### Documentation
- **README.md**: Project overview and setup
- **DEVELOPMENT.md**: Development guidelines
- **API Documentation**: Endpoint documentation

### Contact
- **DevOps Team**: devops@company.com
- **Security Team**: security@company.com
- **Development Team**: dev@company.com

---

*Last updated: $(date)*
*Version: 1.0.0*
