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
        # Initialize scoring service
        scorer = AttackPathScoringService()
        scorer.load_graph_data()
        
        # Initialize agent
        agent = AttackPathAgent()
        
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise

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
        # Check if services are initialized
        if agent is None or scorer is None:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Check Neo4j connection
        info = scorer.conn.get_database_info()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "agent": agent is not None,
                "scorer": scorer is not None,
                "neo4j": len(info.get("nodes", [])) > 0
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Get service metrics."""
    try:
        metrics = {
            "api": {
                "uptime": time.time(),
                "version": "1.0.0"
            }
        }
        
        if agent:
            metrics["agent"] = agent.get_metrics()
        
        if scorer:
            metrics["scorer"] = scorer.get_metrics()
        
        return metrics
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/paths", response_model=AttackPathResponse)
async def get_attack_paths(request: AttackPathRequest):
    """Get attack paths to a target."""
    start_time = time.time()
    
    try:
        if not scorer:
            raise HTTPException(status_code=503, detail="Scoring service not available")
        
        # Get attack paths
        paths = scorer.get_attack_paths(
            target=request.target or "crown-jewel-db-001",
            algorithm=request.algorithm,
            max_hops=request.max_hops,
            k=request.k
        )
        
        # Add explanations
        for path in paths:
            path["explanation"] = scorer.get_risk_explanation(path.get("path", []))
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info("Attack paths retrieved", 
                   target=request.target,
                   algorithm=request.algorithm,
                   count=len(paths),
                   latency_ms=latency_ms)
        
        return AttackPathResponse(
            target=request.target or "crown-jewel-db-001",
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
        if not scorer:
            raise HTTPException(status_code=503, detail="Scoring service not available")
        
        crown_jewels = scorer.get_crown_jewels()
        
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
        if not scorer:
            raise HTTPException(status_code=503, detail="Scoring service not available")
        
        metrics = scorer.get_metrics()
        algorithms = metrics.get("algorithms_available", [])
        
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
