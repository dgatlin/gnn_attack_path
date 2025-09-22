# Observability Tests

This directory contains tests for the observability and monitoring features of the GNN Attack Path system.

## Test Files

- `test_observability_simple.py` - Simple observability tests without Docker dependencies
- `test_observability.py` - Full observability tests with Prometheus and Grafana

## Running Tests

```bash
# Run simple observability tests
python tests/observability/test_observability_simple.py

# Run full observability tests (requires Docker)
python tests/observability/test_observability.py
```

## Test Coverage

- **API Metrics Tests**: Prometheus metrics endpoint validation
- **Health Check Tests**: System health monitoring
- **Dashboard Tests**: Web-based dashboard functionality
- **Logging Tests**: Structured logging validation
- **Performance Tests**: Response time and throughput validation

## Dependencies

- Simple tests: No external dependencies
- Full tests: Docker, Prometheus, Grafana
