# CI/CD Pipeline Documentation

## Overview

This document outlines the comprehensive CI/CD pipeline for the GNN Attack Path Demo project. The pipeline is designed with modern DevOps practices, including automated testing, security scanning, performance validation, and reliable deployment strategies.

## Pipeline Architecture

### Workflow Structure

```
.github/workflows/
├── ci-frontend.yml      # Frontend CI
├── ci-backend.yml       # Backend CI  
├── ci-integration.yml   # Integration tests
├── security.yml         # Security scanning
├── performance.yml      # Performance testing
├── deploy-staging.yml   # Staging deployment
├── deploy-production.yml # Production deployment
├── cleanup.yml          # Cleanup workflows
└── feature-development.yml # Feature branch workflow
```

### Trigger Strategy

The pipeline uses **path-based triggers** to optimize resource usage and execution time:

| Workflow | Trigger Paths | Branches |
|----------|---------------|----------|
| `ci-frontend.yml` | `ui/**`, `package.json`, `package-lock.json` | `main`, `develop`, `feature/*` |
| `ci-backend.yml` | `api/**`, `agent/**`, `scorer/**`, `graph/**`, `data/**`, `tests/**`, `requirements.txt` | `main`, `develop`, `feature/*` |
| `ci-integration.yml` | `ui/**`, `api/**`, `agent/**`, `scorer/**`, `graph/**`, `tests/integration/**` | `main`, `develop` |
| `security.yml` | All files | `main`, `develop`, `feature/*` |
| `performance.yml` | `ui/**`, `api/**`, `agent/**`, `scorer/**`, `ops/k6/**` | `main`, `develop` |
| `deploy-staging.yml` | All files | `main`, `develop` |
| `deploy-production.yml` | All files | `v*` tags |
| `cleanup.yml` | All files | Weekly schedule |

## Detailed Workflow Descriptions

### 1. Frontend CI (`ci-frontend.yml`)

**Purpose**: Comprehensive frontend testing and validation

**Matrix Strategy**: Tests on Node.js 18 and 20

**Steps**:
1. **Dependency Installation**
   - Uses npm cache for faster builds
   - Installs dependencies with `npm ci`

2. **Code Quality Checks**
   - ESLint linting
   - TypeScript type checking
   - Code formatting validation

3. **Testing**
   - Unit tests with coverage
   - Test results uploaded as artifacts

4. **Build Process**
   - Production build creation
   - Build artifacts uploaded

5. **Accessibility Testing**
   - axe-core accessibility scanning
   - Lighthouse CI performance testing

6. **Security Scanning**
   - npm audit for vulnerability scanning
   - Snyk security analysis

**Artifacts**:
- `frontend-build-{node-version}.zip`
- `frontend-test-results-{node-version}.zip`

### 2. Backend CI (`ci-backend.yml`)

**Purpose**: Backend testing, security, and performance validation

**Matrix Strategy**: Tests on Python 3.11 and 3.12

**Steps**:
1. **Environment Setup**
   - Python version installation
   - System dependencies (build-essential)
   - Pip cache for faster installs

2. **Dependency Management**
   - PyTorch installation first (avoids build issues)
   - Requirements installation
   - Environment variables setup

3. **Code Quality**
   - flake8 linting
   - black code formatting
   - isort import sorting
   - mypy type checking

4. **Testing**
   - Unit tests with coverage
   - Integration tests
   - Coverage reports to Codecov

5. **Security Scanning**
   - Bandit security analysis
   - Safety vulnerability scanning

6. **Performance Testing**
   - Locust load testing
   - Performance metrics collection

**Artifacts**:
- `backend-test-results-{python-version}.zip`
- `backend-security-reports.zip`
- `backend-performance-results.zip`

### 3. Integration Tests (`ci-integration.yml`)

**Purpose**: End-to-end testing with real services

**Services**:
- Neo4j database with health checks
- Backend API service
- Frontend application

**Steps**:
1. **Service Setup**
   - Neo4j container startup
   - Health check validation
   - Test data loading

2. **Application Build**
   - Frontend build process
   - Backend API startup
   - Service orchestration

3. **Integration Testing**
   - API endpoint testing
   - Frontend-backend communication
   - Database integration

4. **Smoke Tests**
   - Critical path validation
   - Basic functionality checks

5. **Contract Testing**
   - API contract validation
   - Schema compliance testing

**Artifacts**:
- `integration-test-results.zip`
- `api-contract-test-results.zip`

### 4. Security Scanning (`security.yml`)

**Purpose**: Comprehensive security validation

**Scheduled**: Weekly on Mondays at 2 AM

**Scans**:
1. **Dependency Scanning**
   - npm audit
   - pip audit
   - Snyk analysis

2. **Code Security**
   - Bandit static analysis
   - Safety vulnerability check
   - Semgrep security patterns

3. **Secret Detection**
   - TruffleHog secret scanning
   - GitLeaks analysis
   - detect-secrets validation

4. **Container Security**
   - Trivy vulnerability scanning
   - Image security analysis

5. **Infrastructure Security**
   - Checkov IaC scanning
   - Terraform security validation

**Artifacts**:
- `dependency-security-reports.zip`
- `code-security-reports.zip`
- `security-summary.zip`

### 5. Performance Testing (`performance.yml`)

**Purpose**: Performance validation and regression testing

**Scheduled**: Weekly on Sundays at 3 AM

**Tests**:
1. **Load Testing**
   - K6 performance tests
   - Locust load simulation
   - Artillery stress testing

2. **Frontend Performance**
   - Lighthouse CI analysis
   - WebPageTest validation
   - Bundle size analysis

3. **API Performance**
   - wrk HTTP benchmarking
   - Response time validation
   - Throughput testing

4. **Regression Testing**
   - Performance comparison
   - Baseline validation

**Artifacts**:
- `performance-test-results.zip`
- `frontend-performance-results.zip`
- `api-performance-results.zip`

### 6. Staging Deployment (`deploy-staging.yml`)

**Purpose**: Automated staging environment deployment

**Triggers**: Push to `main` or `develop` branches

**Steps**:
1. **Build Process**
   - Docker image creation
   - Multi-stage builds
   - Image optimization

2. **Registry Push**
   - Amazon ECR authentication
   - Image tagging and pushing
   - Version management

3. **Deployment**
   - ECS service update
   - Blue-green deployment
   - Health check validation

4. **Validation**
   - Smoke test execution
   - Service health verification
   - Endpoint testing

5. **Notifications**
   - Slack deployment status
   - Success/failure alerts

6. **Rollback**
   - Automatic rollback on failure
   - Previous version restoration

### 7. Production Deployment (`deploy-production.yml`)

**Purpose**: Production environment deployment with safety checks

**Triggers**: Version tags (`v*.*.*`) or manual dispatch

**Pre-deployment**:
1. **Validation**
   - Tag format verification
   - Security scan execution
   - Staging smoke tests

2. **Safety Checks**
   - Pre-deployment validation
   - Risk assessment

**Deployment**:
1. **Build and Push**
   - Production image creation
   - ECR registry push
   - Version tagging

2. **Blue-Green Deployment**
   - Task definition updates
   - Service deployment
   - Health check validation

3. **Post-deployment**
   - Comprehensive testing
   - Performance validation
   - Monitoring setup

4. **Release Management**
   - GitHub release creation
   - Version documentation
   - Change tracking

5. **Rollback**
   - Automatic failure detection
   - Previous version restoration
   - Incident notification

### 8. Cleanup (`cleanup.yml`)

**Purpose**: Resource management and cost optimization

**Scheduled**: Weekly on Sundays at 2 AM

**Cleanup Tasks**:
1. **Artifact Cleanup**
   - 30+ day old artifacts
   - Storage optimization

2. **Image Cleanup**
   - ECR image pruning
   - Keep latest 10 versions
   - Local Docker cleanup

3. **Log Cleanup**
   - CloudWatch log groups
   - ECS task logs
   - Old task definitions

4. **Cache Cleanup**
   - GitHub Actions cache
   - Local build cache
   - Dependency cache

5. **Database Cleanup**
   - Neo4j old data removal
   - MLflow run cleanup
   - Database optimization

## Deployment Environments

### Staging Environment
- **Purpose**: Pre-production testing
- **Deployment**: Automatic on `main`/`develop` pushes
- **URL**: `https://staging.gnn-attack-demo.com`
- **Features**: Full functionality, test data

### Production Environment
- **Purpose**: Live production system
- **Deployment**: Manual via version tags
- **URL**: `https://gnn-attack-demo.com`
- **Features**: Production data, monitoring, alerts

## Monitoring and Observability

### Metrics Collection
- **Response Times**: API and frontend performance
- **Error Rates**: Application and infrastructure errors
- **Coverage**: Test coverage tracking
- **Security**: Vulnerability counts and trends

### Alerting
- **Slack**: Deployment status, failures, security issues
- **GitHub**: PR status, workflow failures
- **Email**: Critical alerts and summaries

### Dashboards
- **GitHub Actions**: Workflow execution status
- **Codecov**: Coverage trends and reports
- **Security**: Vulnerability tracking
- **Performance**: Response time monitoring

## Best Practices

### Development Workflow
1. **Feature Branches**: Use `feature/*` naming
2. **Small Commits**: Atomic, focused changes
3. **Pull Requests**: Required for main branch
4. **Testing**: All tests must pass before merge

### Security Practices
1. **Secret Management**: Use GitHub Secrets
2. **Dependency Updates**: Regular security updates
3. **Code Scanning**: Automated security validation
4. **Access Control**: Environment-based permissions

### Performance Practices
1. **Performance Budgets**: Set response time limits
2. **Load Testing**: Regular performance validation
3. **Monitoring**: Continuous performance tracking
4. **Optimization**: Regular performance improvements

## Troubleshooting

### Common Issues

#### Workflow Failures
1. **Check logs**: GitHub Actions tab
2. **Verify secrets**: Ensure all required secrets are set
3. **Test locally**: Run tests before pushing
4. **Check dependencies**: Verify all dependencies are available

#### Deployment Issues
1. **Health checks**: Verify service health
2. **Logs**: Check ECS task logs
3. **Rollback**: Use automatic rollback if needed
4. **Support**: Contact DevOps team

#### Performance Issues
1. **Baseline comparison**: Compare with previous runs
2. **Resource limits**: Check CPU/memory usage
3. **Database performance**: Monitor query performance
4. **Network latency**: Check connectivity

### Debug Commands

```bash
# Check workflow status
gh run list --workflow=ci-frontend.yml

# View workflow logs
gh run view <run-id> --log

# Download artifacts
gh run download <run-id>

# Check deployment status
aws ecs describe-services --cluster gnn-attack-staging
```

## Configuration

### Required Secrets

| Secret | Purpose | Workflow |
|--------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS authentication | Deploy, Cleanup |
| `AWS_SECRET_ACCESS_KEY` | AWS authentication | Deploy, Cleanup |
| `SLACK_WEBHOOK` | Notifications | Deploy, Cleanup |
| `TEAMS_WEBHOOK` | Notifications | Deploy |
| `SNYK_TOKEN` | Security scanning | Frontend, Security |
| `WEBPAGETEST_API_KEY` | Performance testing | Performance |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `NODE_ENV` | Node environment | `production` |
| `PYTHON_VERSION` | Python version | `3.11` |
| `NEO4J_URI` | Database connection | `bolt://localhost:7687` |
| `MLFLOW_TRACKING_URI` | MLflow tracking | `sqlite:///mlflow.db` |

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
