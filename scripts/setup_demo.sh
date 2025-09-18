#!/bin/bash

# GNN Attack Path Demo Setup Script
# This script sets up the complete demo environment

set -e

echo "🚀 Setting up GNN Attack Path Demo..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data models logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your configuration before running the demo."
fi

# Generate synthetic data
echo "🎲 Generating synthetic data..."
python data/generate_synthetic_data.py

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose -f ops/docker-compose.yml build

# Start services
echo "🚀 Starting services..."
docker-compose -f ops/docker-compose.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check Neo4j
if curl -f http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Neo4j is running on http://localhost:7474"
else
    echo "❌ Neo4j is not responding"
fi

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running on http://localhost:8000"
else
    echo "❌ API is not responding"
fi

# Check UI
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ UI is running on http://localhost:3000"
else
    echo "❌ UI is not responding"
fi

# Load data into Neo4j
echo "📊 Loading data into Neo4j..."
docker-compose -f ops/docker-compose.yml run --rm data-loader

echo ""
echo "🎉 Demo setup complete!"
echo ""
echo "📱 Access the demo:"
echo "   UI: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   Neo4j: http://localhost:7474 (neo4j/password)"
echo ""
echo "🔧 Management commands:"
echo "   View logs: docker-compose -f ops/docker-compose.yml logs -f"
echo "   Stop demo: docker-compose -f ops/docker-compose.yml down"
echo "   Restart: docker-compose -f ops/docker-compose.yml restart"
echo ""
echo "🧪 Run tests:"
echo "   python -m pytest tests/ -v"
echo ""
echo "📈 Performance test:"
echo "   python ops/k6/performance_test.py"
echo ""
echo "Happy demoing! 🚀"
