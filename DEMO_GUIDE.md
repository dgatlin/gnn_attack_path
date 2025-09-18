# GNN Attack Path Demo - Quick Start Guide

## 🚀 One-Click Demo Setup

```bash
# Clone and setup
git clone <your-repo>
cd gnn-attack-demo

# Run the complete demo setup
./scripts/setup_demo.sh
```

## 📱 Demo Access Points

- **UI Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)

## 🎯 Demo Scenarios

### Scenario 1: Find Riskiest Attack Paths
1. Open the UI dashboard
2. Select "Attack Paths" tab
3. Choose a crown jewel target
4. Select "Hybrid" algorithm
5. Click "Analyze"
6. Review the top attack paths with risk scores and explanations

### Scenario 2: AI-Powered Query
1. Go to "AI Query" tab
2. Ask: "Where's my riskiest path to the crown jewel database?"
3. Watch the agent analyze and respond with detailed findings
4. Follow up: "What should I fix to reduce risk by 80%?"

### Scenario 3: Remediation Simulation
1. Navigate to "Remediation" tab
2. Review proposed fixes for high-risk paths
3. Click "Simulate" to see risk reduction
4. Generate Terraform diffs for implementation

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI       │    │   Neo4j         │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 7474)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   GNN Scorer    │
                       │   (PyTorch)     │
                       └─────────────────┘
```

## 🔧 Key Features Demonstrated

### Graph Neural Networks
- **GraphSAGE** and **GAT** models for attack path scoring
- Edge likelihood prediction using PyTorch Geometric
- Real-time path scoring with sub-2s response times

### Multi-Agent Orchestration
- **LangGraph** workflow for complex reasoning
- Planner → Retriever → Scorer → Explainer → Remediator
- Natural language query processing

### Advanced RAG
- Graph-aware retrieval from Neo4j
- Contextual explanations for attack paths
- Crown jewel identification and prioritization

### Workflow Automation
- Automated remediation plan generation
- IaC diff generation (Terraform)
- Risk simulation and validation

## 📊 Performance Targets

- **Latency**: <2s p95 for attack path queries
- **Throughput**: 100+ concurrent requests
- **Accuracy**: High precision on top-K attack paths
- **Scalability**: 10K+ asset graphs

## 🧪 Testing

```bash
# Run comprehensive test suite
python -m pytest tests/ -v

# Performance testing with K6
python ops/k6/performance_test.py

# Load testing
make perf-test
```

## 📈 Monitoring

- **Prometheus** metrics collection
- **Grafana** dashboards for visualization
- **Structured logging** with JSON format
- **Health checks** for all services

## 🔒 Security Features

- Demo-safe: No live credentials
- Simulation mode: All changes are dry-run
- Policy-based action validation
- Approval workflows for critical changes

## 🛠️ Development

```bash
# Development setup
make dev-setup

# Start development environment
make up

# View logs
make logs

# Stop services
make down
```

## 📚 API Examples

### Get Attack Paths
```bash
curl -X POST "http://localhost:8000/api/v1/paths" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "crown-jewel-db-001",
    "algorithm": "hybrid",
    "max_hops": 4,
    "k": 5
  }'
```

### Process Natural Language Query
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Where is my riskiest path to the crown jewel database?",
    "context": {}
  }'
```

### Simulate Remediation
```bash
curl -X POST "http://localhost:8000/api/v1/remediate" \
  -H "Content-Type: application/json" \
  -d '{
    "actions": [
      "remove_public_ingress:sg-web-001",
      "apply_patch:vm-app-001"
    ],
    "simulate": true
  }'
```

## 🎯 Demo Success Criteria

✅ **Sub-2s Response Times**: All queries respond within 2 seconds  
✅ **Graph Reasoning**: Sophisticated attack path analysis  
✅ **AI Agents**: Multi-agent orchestration with LangGraph  
✅ **Advanced RAG**: Contextual explanations and recommendations  
✅ **Workflow Automation**: Automated remediation with IaC generation  
✅ **Production Ready**: Monitoring, logging, and error handling  

## 🚀 Next Steps

1. **Customize Data**: Replace synthetic data with real asset inventory
2. **Train GNN**: Fine-tune models on your specific environment
3. **Integrate Sources**: Connect to real vulnerability scanners
4. **Scale Up**: Deploy to production with proper security controls
5. **Extend Agents**: Add more specialized remediation agents

## 📞 Support

For questions or issues:
- Check the logs: `docker-compose -f ops/docker-compose.yml logs -f`
- Review the API docs: http://localhost:8000/docs
- Run diagnostics: `curl http://localhost:8000/health`

Happy demoing! 🎉
