#!/bin/bash
# Teardown script for GCP Cloud Run deployment
# Destroys all infrastructure to avoid ongoing charges

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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Warning
print_warning_message() {
    print_header "WARNING: This will delete all resources!"
    echo ""
    print_warning "This script will permanently delete:"
    echo "  - Cloud Run services (frontend and backend)"
    echo "  - Artifact Registry repository and images"
    echo "  - Secret Manager secrets"
    echo "  - IAM service accounts"
    echo "  - All related infrastructure"
    echo ""
    print_info "Neo4j Aura database will NOT be deleted (manual deletion required)"
    echo ""
    
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Teardown cancelled"
        exit 0
    fi
    echo ""
}

# Get configuration
get_config() {
    print_header "Loading Configuration"
    
    cd iac/terraform/gcp-cloud-run
    
    if [ ! -f "terraform.tfvars" ]; then
        print_error "terraform.tfvars not found. Nothing to teardown."
        exit 1
    fi
    
    PROJECT_ID=$(terraform output -raw project_id 2>/dev/null || grep 'project_id' terraform.tfvars | cut -d'"' -f2)
    REGION=$(terraform output -raw region 2>/dev/null || grep 'region' terraform.tfvars | cut -d'"' -f2)
    
    cd ../../..
    
    print_success "Project: $PROJECT_ID"
    print_success "Region: $REGION"
    echo ""
}

# Destroy with Terraform
destroy_infrastructure() {
    print_header "Destroying Infrastructure"
    
    cd iac/terraform/gcp-cloud-run
    
    print_info "Running Terraform destroy..."
    terraform destroy -auto-approve
    
    print_success "Infrastructure destroyed"
    
    cd ../../..
    echo ""
}

# Clean up local files
cleanup_local() {
    print_header "Cleaning Up Local Files"
    
    print_info "Removing Terraform state and config..."
    rm -rf iac/terraform/gcp-cloud-run/.terraform
    rm -f iac/terraform/gcp-cloud-run/.terraform.lock.hcl
    rm -f iac/terraform/gcp-cloud-run/terraform.tfstate*
    rm -f iac/terraform/gcp-cloud-run/terraform.tfvars
    
    print_success "Local files cleaned"
    echo ""
}

# Summary
print_summary() {
    print_header "Teardown Complete"
    
    echo -e "${GREEN}All GCP resources have been deleted${NC}"
    echo ""
    print_info "Manual cleanup required:"
    echo "  1. Delete Neo4j Aura database at: https://console.neo4j.io/"
    echo "  2. Review billing at: https://console.cloud.google.com/billing"
    echo ""
    print_info "To redeploy:"
    echo "  ./scripts/setup-gcp.sh"
    echo "  ./scripts/deploy-to-gcp.sh --full"
    echo ""
}

# Main execution
main() {
    echo ""
    print_header "GNN Attack Path Demo - Teardown"
    echo ""
    
    print_warning_message
    get_config
    destroy_infrastructure
    cleanup_local
    print_summary
}

# Run main function
main

