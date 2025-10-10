#!/bin/bash
# Deployment script for GCP Cloud Run
# Builds Docker images and deploys to Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Parse arguments
FULL_DEPLOY=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_DEPLOY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--full] [--skip-tests]"
            exit 1
            ;;
    esac
done

# Get configuration from Terraform
get_config() {
    print_header "Loading Configuration"
    
    cd iac/terraform/gcp-cloud-run
    
    if [ ! -f "terraform.tfvars" ]; then
        print_error "terraform.tfvars not found. Run ./scripts/setup-gcp.sh first"
        exit 1
    fi
    
    # Check if terraform is initialized
    if [ ! -d ".terraform" ]; then
        print_info "Initializing Terraform..."
        terraform init
    fi
    
    PROJECT_ID=$(terraform output -raw project_id 2>/dev/null || grep 'project_id' terraform.tfvars | cut -d'"' -f2)
    REGION=$(terraform output -raw region 2>/dev/null || grep 'region' terraform.tfvars | cut -d'"' -f2)
    
    cd ../../..
    
    print_success "Project: $PROJECT_ID"
    print_success "Region: $REGION"
    echo ""
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_info "Skipping tests (--skip-tests flag)"
        echo ""
        return
    fi
    
    print_header "Running Tests"
    
    print_info "Running unit tests..."
    python -m pytest tests/unit/ -v --tb=short || {
        print_error "Tests failed! Fix tests before deploying."
        read -p "Continue anyway? (y/n): " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    
    print_success "Tests passed"
    echo ""
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_header "Deploying Infrastructure"
    
    cd iac/terraform/gcp-cloud-run
    
    # Check if infrastructure exists
    if terraform state list 2>/dev/null | grep -q "google_cloud_run_v2_service"; then
        print_info "Infrastructure already exists. Checking for updates..."
        terraform plan -out=tfplan
        
        read -p "Apply these changes? (y/n): " APPLY
        if [[ "$APPLY" =~ ^[Yy]$ ]]; then
            terraform apply tfplan
            rm tfplan
        else
            print_info "Skipping infrastructure update"
            cd ../../..
            return
        fi
    else
        print_info "Creating infrastructure..."
        terraform plan -out=tfplan
        
        read -p "Create infrastructure? (y/n): " CREATE
        if [[ "$CREATE" =~ ^[Yy]$ ]]; then
            terraform apply tfplan
            rm tfplan
        else
            print_error "Infrastructure creation cancelled"
            cd ../../..
            exit 1
        fi
    fi
    
    # Get outputs
    ARTIFACT_REGISTRY=$(terraform output -raw artifact_registry)
    
    cd ../../..
    
    print_success "Infrastructure ready"
    echo ""
}

# Build and push Docker images
build_and_push_images() {
    print_header "Building Docker Images"
    
    # Backend
    print_info "Building backend image..."
    docker build \
        -f ops/Dockerfile.cloudrun.api \
        -t "$ARTIFACT_REGISTRY/backend:latest" \
        -t "$ARTIFACT_REGISTRY/backend:$(git rev-parse --short HEAD 2>/dev/null || echo 'local')" \
        .
    
    print_success "Backend image built"
    
    # Frontend
    print_info "Building frontend image..."
    docker build \
        -f ops/Dockerfile.cloudrun.ui \
        -t "$ARTIFACT_REGISTRY/frontend:latest" \
        -t "$ARTIFACT_REGISTRY/frontend:$(git rev-parse --short HEAD 2>/dev/null || echo 'local')" \
        .
    
    print_success "Frontend image built"
    
    # MLflow
    print_info "Building MLflow image..."
    docker build \
        -f ops/Dockerfile.mlflow \
        -t "$ARTIFACT_REGISTRY/mlflow:latest" \
        -t "$ARTIFACT_REGISTRY/mlflow:$(git rev-parse --short HEAD 2>/dev/null || echo 'local')" \
        .
    
    print_success "MLflow image built"
    echo ""
    
    print_header "Pushing Images to Artifact Registry"
    
    print_info "Pushing backend..."
    docker push "$ARTIFACT_REGISTRY/backend:latest"
    docker push "$ARTIFACT_REGISTRY/backend:$(git rev-parse --short HEAD 2>/dev/null || echo 'local')" || true
    
    print_info "Pushing frontend..."
    docker push "$ARTIFACT_REGISTRY/frontend:latest"
    docker push "$ARTIFACT_REGISTRY/frontend:$(git rev-parse --short HEAD 2>/dev/null || echo 'local')" || true
    
    print_info "Pushing MLflow..."
    docker push "$ARTIFACT_REGISTRY/mlflow:latest"
    docker push "$ARTIFACT_REGISTRY/mlflow:$(git rev-parse --short HEAD 2>/dev/null || echo 'local')" || true
    
    print_success "Images pushed successfully"
    echo ""
}

# Deploy to Cloud Run
deploy_services() {
    print_header "Deploying to Cloud Run"
    
    print_info "Deploying backend service..."
    gcloud run services update gnn-demo-backend \
        --image="$ARTIFACT_REGISTRY/backend:latest" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --quiet
    
    print_success "Backend deployed"
    
    print_info "Deploying frontend service..."
    gcloud run services update gnn-demo-frontend \
        --image="$ARTIFACT_REGISTRY/frontend:latest" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --quiet
    
    print_success "Frontend deployed"
    
    print_info "Deploying MLflow service..."
    gcloud run services update gnn-demo-mlflow \
        --image="$ARTIFACT_REGISTRY/mlflow:latest" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --quiet 2>/dev/null || print_info "MLflow service not found (skipping)"
    
    print_success "All services deployed"
    echo ""
}

# Get service URLs
get_urls() {
    print_header "Deployment Complete!"
    
    BACKEND_URL=$(gcloud run services describe gnn-demo-backend \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    FRONTEND_URL=$(gcloud run services describe gnn-demo-frontend \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    MLFLOW_URL=$(gcloud run services describe gnn-demo-mlflow \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)" 2>/dev/null || echo "Not deployed")
    
    echo ""
    echo -e "${GREEN}✓ Your demo is live!${NC}"
    echo ""
    echo "Frontend:  $FRONTEND_URL"
    echo "Backend:   $BACKEND_URL"
    echo "API Docs:  $BACKEND_URL/docs"
    echo "MLflow:    $MLFLOW_URL"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    gcloud logging read 'resource.type=cloud_run_revision' --limit 50"
    echo "  View metrics: gcloud monitoring dashboards list"
    echo "  Update app:   ./scripts/deploy-to-gcp.sh"
    echo "  Teardown:     ./scripts/teardown-gcp.sh"
    echo ""
}

# Health check
health_check() {
    print_header "Running Health Checks"
    
    print_info "Checking backend health..."
    sleep 10  # Give services time to start
    
    BACKEND_URL=$(gcloud run services describe gnn-demo-backend \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" | grep -q "200"; then
        print_success "Backend is healthy"
    else
        print_error "Backend health check failed"
        print_info "Check logs: gcloud logging read 'resource.labels.service_name=gnn-demo-backend' --limit 20"
    fi
    
    print_info "Checking frontend..."
    FRONTEND_URL=$(gcloud run services describe gnn-demo-frontend \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    if curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200"; then
        print_success "Frontend is healthy"
    else
        print_error "Frontend health check failed"
    fi
    
    echo ""
}

# Main execution
main() {
    echo ""
    print_header "GNN Attack Path Demo - Deployment"
    echo ""
    
    get_config
    
    if [ "$FULL_DEPLOY" = true ]; then
        run_tests
        deploy_infrastructure
    fi
    
    build_and_push_images
    deploy_services
    health_check
    get_urls
    
    # Open browser
    read -p "Open frontend in browser? (y/n): " OPEN_BROWSER
    if [[ "$OPEN_BROWSER" =~ ^[Yy]$ ]]; then
        FRONTEND_URL=$(gcloud run services describe gnn-demo-frontend \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)")
        open "$FRONTEND_URL" 2>/dev/null || xdg-open "$FRONTEND_URL" 2>/dev/null || echo "Please visit: $FRONTEND_URL"
    fi
}

# Run main function
main

