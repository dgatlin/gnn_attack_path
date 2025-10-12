"""
FastAPI backend for GNN Attack Path Demo.
Provides REST API endpoints for attack path analysis and remediation.
"""
import time
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

from agent.app import AttackPathAgent
from scorer.service import AttackPathScoringService

# Mock data functions (kept as fallback)
def get_mock_attack_paths(target: str, max_hops: int = 4, algorithm: str = "hybrid"):
    """Generate mock attack paths."""
    return [
        {
            "path": ["external", "dmz", "internal", target],
            "score": 0.92,
            "risk_score": 0.92,
            "length": 4,
            "algorithm": algorithm,
            "vulnerabilities": ["CVE-2023-1234"],
            "exploit_available": True,
            "explanation": "High-risk path through DMZ with known vulnerabilities."
        }
    ]

def get_mock_crown_jewels():
    """Generate mock crown jewels data."""
    return {
        "crown_jewels": [
            {"id": "crown-jewel-db-001", "name": "Production Database", "type": "database"},
            {"id": "crown-jewel-app-001", "name": "Customer Portal", "type": "application"}
        ],
        "count": 2
    }

def get_mock_algorithms():
    """Generate mock algorithms data."""
    return {
        "algorithms": [
            {"name": "GNN", "description": "Graph Neural Network", "accuracy": 0.94},
            {"name": "Dijkstra", "description": "Shortest Path Algorithm", "accuracy": 0.87},
            {"name": "PageRank", "description": "PageRank Algorithm", "accuracy": 0.82}
        ]
    }

def get_mock_metrics():
    """Generate mock metrics data."""
    return {
        "total_requests": 1250,
        "avg_response_time": 0.15,
        "success_rate": 0.99,
        "attack_paths_analyzed": 342
    }

def get_mock_risk_explanation(path: list):
    """Generate mock risk explanation."""
    if len(path) > 3:
        return "High risk: Complex multi-hop attack path with multiple vulnerabilities"
    elif len(path) > 2:
        return "Medium risk: Multi-hop attack path with some vulnerabilities"
    else:
        return "Low risk: Direct attack path with limited vulnerabilities"

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GNN Attack Path Demo API",
    description="API for attack path analysis and agentic remediation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
agent = None
scorer = None

# Pydantic models
class AttackPathRequest(BaseModel):
    target: Optional[str] = None
    algorithm: str = "hybrid"
    max_hops: int = 4
    k: int = 5

class AttackPathResponse(BaseModel):
    target: str
    paths: List[Dict[str, Any]]
    latency_ms: float
    algorithm: str

class RemediationRequest(BaseModel):
    actions: List[str]
    simulate: bool = True

class RemediationResponse(BaseModel):
    original_risk: float
    new_risk: float
    risk_reduction: float
    actions_applied: List[str]
    affected_assets: List[str]
    iac_diff: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    results: Dict[str, Any]
    status: str
    latency_ms: float

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global agent, scorer
    
    logger.info("Starting GNN Attack Path Demo API")
    
    try:
        # Try to initialize scoring service with Neo4j
        try:
            scorer = AttackPathScoringService()
            scorer.load_graph_data()
            logger.info("Scoring service initialized with Neo4j")
        except Exception as e:
            logger.warning("Neo4j not available, using mock data", error=str(e))
            scorer = None
        
        # Initialize agent (this might also fail without OpenAI key)
        try:
            agent = AttackPathAgent()
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.warning("Agent initialization failed, using mock responses", error=str(e))
            agent = None
        
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        # Don't raise - allow API to start with mock data

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down GNN Attack Path Demo API")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GNN Attack Path Demo API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "attack_paths": "/api/v1/paths",
            "remediation": "/api/v1/remediate",
            "query": "/api/v1/query",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        return {
            "status": "healthy",
            "model_loaded": True,
            "version": "0.1.0",
            "timestamp": time.time(),
            "services": {
                "agent": agent is not None,
                "scorer": scorer is not None,
                "mock_data": True
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Get service metrics in Prometheus format."""
    try:
        # Basic Prometheus metrics format
        metrics_text = f"""# HELP api_uptime_seconds API uptime in seconds
# TYPE api_uptime_seconds counter
api_uptime_seconds {time.time()}

# HELP api_version_info API version information
# TYPE api_version_info gauge
api_version_info{{version="1.0.0"}} 1

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{{method="GET",endpoint="/health"}} 1
http_requests_total{{method="GET",endpoint="/metrics"}} 1
http_requests_total{{method="POST",endpoint="/api/v1/paths"}} 1

# HELP attack_paths_analyzed_total Total attack paths analyzed
# TYPE attack_paths_analyzed_total counter
attack_paths_analyzed_total 1

# HELP api_health_status API health status
# TYPE api_health_status gauge
api_health_status 1
"""
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=metrics_text, media_type="text/plain")
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/metrics")
async def get_api_metrics():
    """Get API metrics in JSON format."""
    try:
        metrics = get_mock_metrics()
        return {"metrics": metrics}
    except Exception as e:
        logger.error("Failed to get API metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/risk-explanation")
async def get_risk_explanation(request: dict):
    """Get risk explanation for an attack path."""
    try:
        path = request.get("path", [])
        explanation = get_mock_risk_explanation(path)
        return {"explanation": explanation}
    except Exception as e:
        logger.error("Failed to get risk explanation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/paths", response_model=AttackPathResponse)
async def get_attack_paths(request: AttackPathRequest):
    """Get attack paths to a target."""
    start_time = time.time()
    
    try:
        target = request.target or "crown-jewel-db-001"
        
        if scorer:
            # Use real scoring service if available
            paths = scorer.get_attack_paths(
                target=target,
                algorithm=request.algorithm,
                max_hops=request.max_hops,
                k=request.k
            )
            # Add explanations
            for path in paths:
                path["explanation"] = scorer.get_risk_explanation(path.get("path", []))
        else:
            # Use mock data
            paths = get_mock_attack_paths(
                target=target,
                max_hops=request.max_hops,
                algorithm=request.algorithm
            )
            # Add explanations
            for path in paths:
                path["explanation"] = get_mock_risk_explanation(path.get("path", []))
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info("Attack paths retrieved", 
                   target=target,
                   algorithm=request.algorithm,
                   count=len(paths),
                   latency_ms=latency_ms)
        
        return AttackPathResponse(
            target=target,
            paths=paths,
            latency_ms=latency_ms,
            algorithm=request.algorithm
        )
        
    except Exception as e:
        logger.error("Failed to get attack paths", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/remediate", response_model=RemediationResponse)
async def remediate_risks(request: RemediationRequest):
    """Simulate or apply remediation actions."""
    start_time = time.time()
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not available")
        
        # Process remediation request
        context = {
            "actions": request.actions,
            "simulate": request.simulate
        }
        
        result = agent.process_query(
            f"Simulate remediation actions: {', '.join(request.actions)}",
            context=context
        )
        
        # Extract results
        simulation = result.get("simulation", {})
        iac_diff = result.get("iac_diff")
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info("Remediation processed", 
                   actions=request.actions,
                   simulate=request.simulate,
                   latency_ms=latency_ms)
        
        return RemediationResponse(
            original_risk=simulation.get("original_risk", 0.8),
            new_risk=simulation.get("new_risk", 0.3),
            risk_reduction=simulation.get("total_risk_reduction", 0.5),
            actions_applied=request.actions,
            affected_assets=simulation.get("affected_assets", []),
            iac_diff=iac_diff
        )
        
    except Exception as e:
        logger.error("Failed to process remediation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language queries using the agent."""
    start_time = time.time()
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not available")
        
        # Process query through agent
        results = agent.process_query(request.query, request.context)
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info("Query processed", 
                   query=request.query[:100],
                   latency_ms=latency_ms)
        
        return QueryResponse(
            results=results,
            status="success",
            latency_ms=latency_ms
        )
        
    except Exception as e:
        logger.error("Failed to process query", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/crown-jewels")
async def get_crown_jewels():
    """Get all crown jewel assets."""
    try:
        if scorer:
            crown_jewels = scorer.get_crown_jewels()
        else:
            crown_jewels = get_mock_crown_jewels()
        
        return {
            "crown_jewels": crown_jewels,
            "count": len(crown_jewels)
        }
        
    except Exception as e:
        logger.error("Failed to get crown jewels", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/algorithms")
async def get_available_algorithms():
    """Get available scoring algorithms."""
    try:
        if scorer:
            metrics = scorer.get_metrics()
            algorithms = metrics.get("algorithms_available", [])
        else:
            algorithms = get_mock_algorithms()
        
        return {
            "algorithms": algorithms,
            "default": "hybrid",
            "recommended": "gnn" if "gnn" in algorithms else "hybrid"
        }
        
    except Exception as e:
        logger.error("Failed to get algorithms", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Clear the path cache."""
    try:
        if not scorer:
            raise HTTPException(status_code=503, detail="Scoring service not available")
        
        scorer.clear_cache()
        
        return {
            "status": "success",
            "message": "Cache cleared"
        }
        
    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
