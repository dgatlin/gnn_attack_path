#!/bin/bash
# Quick setup script for observability testing

echo "🔍 Starting GNN Attack Path Demo Observability Stack"
echo "=================================================="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Start the monitoring stack
echo "📊 Starting Prometheus and Grafana..."
cd ops/monitoring
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

# Test connections
echo ""
echo "🧪 Testing connections..."

# Test Prometheus
if curl -s http://localhost:9090/api/v1/query?query=up > /dev/null; then
    echo "✅ Prometheus is running at http://localhost:9090"
else
    echo "❌ Prometheus is not responding"
fi

# Test Grafana
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ Grafana is running at http://localhost:3001"
    echo "   Default credentials: admin/admin"
else
    echo "❌ Grafana is not responding"
fi

echo ""
echo "🚀 Observability stack started!"
echo ""
echo "Next steps:"
echo "1. Run the API: python api/main.py"
echo "2. Run the test: python test_observability.py"
echo "3. Open Grafana: http://localhost:3001"
echo "4. Open Prometheus: http://localhost:9090"
echo ""
echo "To stop the stack: cd ops/monitoring && docker-compose down"
