.PHONY: up down build test clean logs

# Start the complete demo stack
up:
	@echo "Starting GNN Attack Path Demo..."
	docker-compose -f ops/docker-compose.yml up -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Demo is ready!"
	@echo "UI: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "Neo4j: http://localhost:7474 (neo4j/password)"

# Stop all services
down:
	docker-compose -f ops/docker-compose.yml down

# Build all images
build:
	docker-compose -f ops/docker-compose.yml build

# Run tests
test:
	@echo "Running all tests..."
	python -m pytest tests/ -v --cov=. --cov-report=term-missing

test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/unit/ -v --cov=. --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v --cov=. --cov-report=term-missing

test-comprehensive:
	@echo "Running comprehensive test suite..."
	python -m pytest tests/test_comprehensive.py -v --cov=. --cov-report=term-missing

test-runner:
	@echo "Running organized test suite..."
	python tests/test_runner.py all

test-specific:
	@echo "Running specific module tests..."
	python tests/test_runner.py module --module $(MODULE)

# Clean up everything
clean:
	docker-compose -f ops/docker-compose.yml down -v
	docker system prune -f

# View logs
logs:
	docker-compose -f ops/docker-compose.yml logs -f

# Setup development environment
dev-setup:
	pip install -r requirements.txt
	python -m pip install -e .

# Generate synthetic data
data:
	python data/generate_synthetic_data.py

# Load data into Neo4j
load-data:
	python graph/load_data.py

# Run performance tests
perf-test:
	python ops/k6/performance_test.py
