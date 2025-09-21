#!/bin/bash

# Development Workflow Script
# Usage: ./scripts/dev-workflow.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in a git repository
check_git_repo() {
    if [ ! -d ".git" ]; then
        log_error "Not in a git repository!"
        exit 1
    fi
}

# Create a new feature branch
create_feature_branch() {
    local branch_name=$1
    if [ -z "$branch_name" ]; then
        log_error "Please provide a branch name"
        echo "Usage: $0 create-feature <branch-name>"
        exit 1
    fi
    
    check_git_repo
    log_info "Creating feature branch: feature/$branch_name"
    git checkout -b "feature/$branch_name"
    log_success "Feature branch 'feature/$branch_name' created and checked out"
}

# Commit changes with conventional commit message
commit_changes() {
    local message=$1
    if [ -z "$message" ]; then
        log_error "Please provide a commit message"
        echo "Usage: $0 commit '<message>'"
        exit 1
    fi
    
    check_git_repo
    log_info "Staging all changes..."
    git add .
    
    log_info "Committing changes: $message"
    git commit -m "$message"
    log_success "Changes committed successfully"
}

# Push feature branch
push_feature() {
    local branch_name=$(git branch --show-current)
    if [[ ! $branch_name == feature/* ]]; then
        log_error "Not on a feature branch! Current branch: $branch_name"
        exit 1
    fi
    
    check_git_repo
    log_info "Pushing feature branch: $branch_name"
    git push -u origin "$branch_name"
    log_success "Feature branch pushed successfully"
}

# Create pull request
create_pr() {
    local branch_name=$(git branch --show-current)
    if [[ ! $branch_name == feature/* ]]; then
        log_error "Not on a feature branch! Current branch: $branch_name"
        exit 1
    fi
    
    local pr_url="https://github.com/dgatlin/gnn_attack_path/pull/new/$branch_name"
    log_info "Creating pull request..."
    log_success "Pull request URL: $pr_url"
    
    # Try to open in browser (macOS)
    if command -v open &> /dev/null; then
        open "$pr_url"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$pr_url"
    else
        echo "Please open the URL above in your browser"
    fi
}

# Run frontend development server
start_frontend() {
    log_info "Starting frontend development server..."
    cd ui
    if [ ! -f "package.json" ]; then
        log_error "Frontend not found! Make sure you're in the project root"
        exit 1
    fi
    
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
    fi
    
    log_success "Starting React development server on http://localhost:3000"
    npm start
}

# Run backend development server
start_backend() {
    log_info "Starting backend development server..."
    if [ ! -f "requirements.txt" ]; then
        log_error "Backend not found! Make sure you're in the project root"
        exit 1
    fi
    
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    log_success "Starting FastAPI server on http://localhost:8000"
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
}

# Run all tests
run_tests() {
    log_info "Running all tests..."
    
    # Backend tests
    log_info "Running backend tests..."
    python -m pytest tests/ -v --cov=. --cov-report=term-missing
    
    # Frontend tests
    log_info "Running frontend tests..."
    cd ui
    npm test -- --watchAll=false --coverage
    cd ..
    
    log_success "All tests completed"
}

# Clean up
cleanup() {
    log_info "Cleaning up..."
    
    # Stop any running processes
    pkill -f "react-scripts start" || true
    pkill -f "uvicorn api.main:app" || true
    
    # Clean node modules
    if [ -d "ui/node_modules" ]; then
        log_info "Cleaning frontend dependencies..."
        rm -rf ui/node_modules
    fi
    
    # Clean Python cache
    log_info "Cleaning Python cache..."
    find . -type d -name "__pycache__" -exec rm -rf {} + || true
    find . -type f -name "*.pyc" -delete || true
    
    log_success "Cleanup completed"
}

# Show help
show_help() {
    echo "Development Workflow Script"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  create-feature <name>  Create a new feature branch"
    echo "  commit <message>       Commit changes with message"
    echo "  push                   Push current feature branch"
    echo "  create-pr              Create pull request for current branch"
    echo "  start-frontend         Start React development server"
    echo "  start-backend          Start FastAPI development server"
    echo "  test                   Run all tests"
    echo "  cleanup                Clean up dependencies and cache"
    echo "  help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 create-feature new-dashboard"
    echo "  $0 commit 'feat: Add new dashboard component'"
    echo "  $0 push"
    echo "  $0 create-pr"
}

# Main script logic
case "$1" in
    "create-feature")
        create_feature_branch "$2"
        ;;
    "commit")
        commit_changes "$2"
        ;;
    "push")
        push_feature
        ;;
    "create-pr")
        create_pr
        ;;
    "start-frontend")
        start_frontend
        ;;
    "start-backend")
        start_backend
        ;;
    "test")
        run_tests
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
