# Scripts

This directory contains utility scripts for managing and operating the GNN Attack Path system.

## Script Files

- `start_observability.sh` - Start Prometheus and Grafana monitoring stack

## Usage

```bash
# Start observability stack
./scripts/start_observability.sh

# Make script executable if needed
chmod +x scripts/start_observability.sh
```

## Prerequisites

- Docker and Docker Compose installed
- Prometheus and Grafana configuration files in `ops/monitoring/`
