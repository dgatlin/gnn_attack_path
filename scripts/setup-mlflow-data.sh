#!/bin/bash
# Setup script to populate MLflow with demo data
# This creates realistic experiment history for demonstration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Main setup
main() {
    print_header "MLflow Demo Data Setup"
    
    # Check if MLflow URL is available
    cd iac/terraform/gcp-cloud-run
    
    if [ ! -f "terraform.tfstate" ]; then
        print_error "Terraform not applied yet. Please run ./scripts/deploy-to-gcp.sh first"
        exit 1
    fi
    
    MLFLOW_URL=$(terraform output -raw mlflow_url 2>/dev/null || echo "")
    
    if [ -z "$MLFLOW_URL" ]; then
        print_error "MLflow service not found. Make sure Terraform applied successfully"
        exit 1
    fi
    
    cd ../../..
    
    print_success "MLflow server: $MLFLOW_URL"
    
    # Generate demo data
    print_header "Generating ML Ops Demo Data"
    
    if [ ! -f "scripts/generate-mlops-history.py" ]; then
        print_error "generate-mlops-history.py not found"
        exit 1
    fi
    
    python scripts/generate-mlops-history.py
    
    print_success "Demo data generated"
    
    # Upload to MLflow (if running locally)
    print_header "Optional: Upload Experiments to MLflow"
    
    print_info "To upload demo experiments to your MLflow server:"
    echo ""
    echo "export MLFLOW_TRACKING_URI=$MLFLOW_URL"
    echo "python examples/gnn_optimization_example.py"
    echo ""
    print_info "This will run actual Optuna optimization and log to MLflow"
    
    # Summary
    print_header "Setup Complete"
    
    echo ""
    echo "MLflow UI: $MLFLOW_URL"
    echo "API Docs:  ${MLFLOW_URL}/api/2.0/mlflow/docs"
    echo ""
    echo "Demo data location: data/mlops_history/"
    echo ""
    print_info "Your backend is now configured to use this MLflow server"
    
}

main

