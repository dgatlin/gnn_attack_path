#!/bin/bash
# Setup script for GCP Cloud Run deployment
# This script initializes your GCP project and prepares for deployment

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

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    print_success "gcloud CLI installed"
    
    # Check terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Install from: https://www.terraform.io/downloads"
        exit 1
    fi
    print_success "Terraform installed"
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker installed"
    
    echo ""
}

# Get GCP project info
get_project_info() {
    print_header "GCP Project Configuration"
    
    # Get current project
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_PROJECT" ]; then
        print_info "No GCP project currently set"
        read -p "Enter your GCP Project ID: " PROJECT_ID
    else
        print_info "Current project: $CURRENT_PROJECT"
        read -p "Use this project? (y/n, default: y): " USE_CURRENT
        USE_CURRENT=${USE_CURRENT:-y}
        
        if [[ "$USE_CURRENT" =~ ^[Yy]$ ]]; then
            PROJECT_ID=$CURRENT_PROJECT
        else
            read -p "Enter your GCP Project ID: " PROJECT_ID
        fi
    fi
    
    # Set project
    print_info "Setting GCP project to: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
    
    # Get region
    CURRENT_REGION=$(gcloud config get-value compute/region 2>/dev/null || echo "us-central1")
    read -p "Enter GCP region (default: $CURRENT_REGION): " REGION
    REGION=${REGION:-$CURRENT_REGION}
    
    print_success "Project: $PROJECT_ID"
    print_success "Region: $REGION"
    
    echo ""
}

# Setup Neo4j Aura
setup_neo4j() {
    print_header "Neo4j Configuration"
    
    print_info "You need a Neo4j database. Options:"
    echo "  1. Neo4j Aura Free (recommended for demo)"
    echo "  2. Neo4j Aura Pro"
    echo "  3. Self-hosted Neo4j"
    echo ""
    
    read -p "Choose option (1-3, default: 1): " NEO4J_OPTION
    NEO4J_OPTION=${NEO4J_OPTION:-1}
    
    if [ "$NEO4J_OPTION" == "1" ]; then
        print_info "Setting up Neo4j Aura Free..."
        echo ""
        echo "1. Go to: https://neo4j.com/cloud/aura-free/"
        echo "2. Create a free database"
        echo "3. Save the connection details"
        echo ""
        read -p "Press Enter when ready to continue..."
    fi
    
    read -p "Enter Neo4j URI (e.g., neo4j+s://xxxxx.databases.neo4j.io): " NEO4J_URI
    read -p "Enter Neo4j username (default: neo4j): " NEO4J_USERNAME
    NEO4J_USERNAME=${NEO4J_USERNAME:-neo4j}
    read -s -p "Enter Neo4j password: " NEO4J_PASSWORD
    echo ""
    
    print_success "Neo4j configuration saved"
    echo ""
}

# Setup OpenAI
setup_openai() {
    print_header "OpenAI Configuration"
    
    print_info "OpenAI API key is required for AI agent functionality"
    echo "Get your API key from: https://platform.openai.com/api-keys"
    echo ""
    
    read -s -p "Enter OpenAI API key: " OPENAI_API_KEY
    echo ""
    
    print_success "OpenAI API key saved"
    echo ""
}

# Enable GCP APIs
enable_apis() {
    print_header "Enabling Required GCP APIs"
    
    APIS=(
        "run.googleapis.com"
        "artifactregistry.googleapis.com"
        "secretmanager.googleapis.com"
        "cloudresourcemanager.googleapis.com"
        "compute.googleapis.com"
        "logging.googleapis.com"
        "monitoring.googleapis.com"
        "cloudbuild.googleapis.com"
    )
    
    for API in "${APIS[@]}"; do
        print_info "Enabling $API..."
        gcloud services enable "$API" --project="$PROJECT_ID" 2>/dev/null || true
    done
    
    print_success "APIs enabled"
    echo ""
}

# Store secrets
store_secrets() {
    print_header "Storing Secrets in Secret Manager"
    
    # Store Neo4j password
    print_info "Storing Neo4j password..."
    echo -n "$NEO4J_PASSWORD" | gcloud secrets create neo4j-password \
        --data-file=- \
        --replication-policy="automatic" \
        --project="$PROJECT_ID" 2>/dev/null || \
    echo -n "$NEO4J_PASSWORD" | gcloud secrets versions add neo4j-password \
        --data-file=- \
        --project="$PROJECT_ID"
    
    # Store OpenAI API key
    print_info "Storing OpenAI API key..."
    echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key \
        --data-file=- \
        --replication-policy="automatic" \
        --project="$PROJECT_ID" 2>/dev/null || \
    echo -n "$OPENAI_API_KEY" | gcloud secrets versions add openai-api-key \
        --data-file=- \
        --project="$PROJECT_ID"
    
    print_success "Secrets stored securely"
    echo ""
}

# Create terraform.tfvars
create_terraform_config() {
    print_header "Creating Terraform Configuration"
    
    cd iac/terraform/gcp-cloud-run
    
    cat > terraform.tfvars <<EOF
# GCP Configuration
project_id = "$PROJECT_ID"
region     = "$REGION"

# Project naming
project_name = "gnn-demo"

# Neo4j Configuration
neo4j_uri      = "$NEO4J_URI"
neo4j_username = "$NEO4J_USERNAME"

# Scaling configuration
max_instances = 10

# Labels
labels = {
  environment = "demo"
  project     = "gnn-attack-path"
  managed_by  = "terraform"
}
EOF
    
    print_success "Terraform configuration created: iac/terraform/gcp-cloud-run/terraform.tfvars"
    
    cd ../../..
    echo ""
}

# Initialize Terraform
init_terraform() {
    print_header "Initializing Terraform"
    
    cd iac/terraform/gcp-cloud-run
    
    terraform init
    
    print_success "Terraform initialized"
    
    cd ../../..
    echo ""
}

# Configure Docker authentication
configure_docker() {
    print_header "Configuring Docker Authentication"
    
    print_info "Configuring Docker to authenticate with Artifact Registry..."
    gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
    
    print_success "Docker authentication configured"
    echo ""
}

# Load data into Neo4j
load_data_to_neo4j() {
    print_header "Loading Synthetic Data"
    
    print_info "Would you like to generate and load synthetic data into Neo4j?"
    read -p "Load data now? (y/n, default: y): " LOAD_DATA
    LOAD_DATA=${LOAD_DATA:-y}
    
    if [[ "$LOAD_DATA" =~ ^[Yy]$ ]]; then
        print_info "Generating synthetic data..."
        python3 data/generate_synthetic_data.py
        
        print_info "Loading data into Neo4j..."
        export NEO4J_URI="$NEO4J_URI"
        export NEO4J_USERNAME="$NEO4J_USERNAME"
        export NEO4J_PASSWORD="$NEO4J_PASSWORD"
        python3 graph/load_data.py
        
        print_success "Data loaded successfully"
    else
        print_info "Skipping data load. You can run it later with:"
        echo "  python3 data/generate_synthetic_data.py"
        echo "  python3 graph/load_data.py"
    fi
    
    echo ""
}

# Summary
print_summary() {
    print_header "Setup Complete!"
    
    echo -e "${GREEN}Your GCP environment is ready for deployment${NC}"
    echo ""
    echo "Configuration:"
    echo "  Project: $PROJECT_ID"
    echo "  Region: $REGION"
    echo "  Neo4j: $NEO4J_URI"
    echo ""
    echo "Next steps:"
    echo "  1. Review Terraform plan:"
    echo "     cd iac/terraform/gcp-cloud-run"
    echo "     terraform plan"
    echo ""
    echo "  2. Deploy infrastructure:"
    echo "     terraform apply"
    echo ""
    echo "  3. Build and deploy application:"
    echo "     cd ../../.."
    echo "     ./scripts/deploy-to-gcp.sh"
    echo ""
    echo "  Or run everything in one command:"
    echo "     ./scripts/deploy-to-gcp.sh --full"
    echo ""
}

# Main execution
main() {
    echo ""
    print_header "GNN Attack Path Demo - GCP Setup"
    echo ""
    
    check_prerequisites
    get_project_info
    setup_neo4j
    setup_openai
    enable_apis
    store_secrets
    create_terraform_config
    init_terraform
    configure_docker
    load_data_to_neo4j
    print_summary
}

# Run main function
main

