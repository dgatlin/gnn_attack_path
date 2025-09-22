# Dashboards

This directory contains web-based dashboards for monitoring and visualizing the GNN Attack Path system.

## Dashboard Files

- `simple_dashboard.html` - Dark-themed observability dashboard with real-time metrics

## Features

- **Real-time Metrics**: Live updates of API performance and attack path analysis
- **Dark Theme**: Professional cybersecurity-focused UI design
- **Interactive Charts**: Dynamic visualization of threat analysis data
- **Responsive Design**: Works on desktop and mobile devices

## Usage

```bash
# Open the dashboard in your browser
open dashboards/simple_dashboard.html

# Or serve it with a local web server
python -m http.server 8001
```

## Data Sources

The dashboard connects to the GNN Attack Path API running on port 8000 to fetch real-time metrics and data.
