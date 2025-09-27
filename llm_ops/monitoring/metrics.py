"""
LLM Metrics Collection and Tracking
===================================

Tracks comprehensive metrics for LLM operations including:
- Token usage (input/output/total)
- Cost tracking (per request, per model, per user)
- Performance metrics (latency, throughput, error rates)
- Quality metrics (response quality, user satisfaction)
- Model performance drift detection
"""

import time
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog
from prometheus_client import Counter, Histogram, Gauge, Summary

logger = structlog.get_logger(__name__)

# Prometheus metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'provider', 'endpoint', 'status']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens used',
    ['model', 'provider', 'token_type']  # token_type: input, output, total
)

llm_cost_total = Counter(
    'llm_cost_total',
    'Total cost in USD',
    ['model', 'provider', 'cost_type']  # cost_type: input, output, total
)

llm_response_time = Histogram(
    'llm_response_time_seconds',
    'LLM response time in seconds',
    ['model', 'provider', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

llm_error_rate = Gauge(
    'llm_error_rate',
    'LLM error rate',
    ['model', 'provider', 'error_type']
)

llm_quality_score = Gauge(
    'llm_quality_score',
    'LLM response quality score',
    ['model', 'provider', 'quality_type']
)

llm_active_connections = Gauge(
    'llm_active_connections',
    'Active LLM connections',
    ['model', 'provider']
)

@dataclass
class LLMRequestMetrics:
    """Metrics for a single LLM request."""
    request_id: str
    model: str
    provider: str
    endpoint: str
    timestamp: datetime
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    response_time_ms: float = 0.0
    status: str = "success"
    error_type: Optional[str] = None
    quality_score: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    prompt_hash: Optional[str] = None
    response_hash: Optional[str] = None

@dataclass
class LLMModelMetrics:
    """Aggregated metrics for a specific model."""
    model: str
    provider: str
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_response_time_ms: float = 0.0
    error_rate: float = 0.0
    quality_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    time_window: timedelta = field(default_factory=lambda: timedelta(hours=1))

class LLMMetrics:
    """Comprehensive LLM metrics collection and tracking."""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.request_metrics: List[LLMRequestMetrics] = []
        self.model_metrics: Dict[str, LLMModelMetrics] = {}
        self.cleanup_interval = timedelta(hours=1)
        self.last_cleanup = datetime.now()
    
    def track_request(self, metrics: LLMRequestMetrics) -> None:
        """Track a single LLM request."""
        logger.info("Tracking LLM request", 
                   request_id=metrics.request_id,
                   model=metrics.model,
                   provider=metrics.provider,
                   tokens=metrics.total_tokens,
                   cost=metrics.cost_usd,
                   response_time=metrics.response_time_ms)
        
        # Store metrics
        self.request_metrics.append(metrics)
        
        # Update Prometheus metrics
        self._update_prometheus_metrics(metrics)
        
        # Update model metrics
        self._update_model_metrics(metrics)
        
        # Cleanup old metrics
        self._cleanup_old_metrics()
    
    def _update_prometheus_metrics(self, metrics: LLMRequestMetrics) -> None:
        """Update Prometheus metrics."""
        # Request count
        llm_requests_total.labels(
            model=metrics.model,
            provider=metrics.provider,
            endpoint=metrics.endpoint,
            status=metrics.status
        ).inc()
        
        # Token usage
        llm_tokens_total.labels(
            model=metrics.model,
            provider=metrics.provider,
            token_type='input'
        ).inc(metrics.input_tokens)
        
        llm_tokens_total.labels(
            model=metrics.model,
            provider=metrics.provider,
            token_type='output'
        ).inc(metrics.output_tokens)
        
        llm_tokens_total.labels(
            model=metrics.model,
            provider=metrics.provider,
            token_type='total'
        ).inc(metrics.total_tokens)
        
        # Cost tracking
        llm_cost_total.labels(
            model=metrics.model,
            provider=metrics.provider,
            cost_type='total'
        ).inc(metrics.cost_usd)
        
        # Response time
        llm_response_time.labels(
            model=metrics.model,
            provider=metrics.provider,
            endpoint=metrics.endpoint
        ).observe(metrics.response_time_ms / 1000.0)
        
        # Error rate
        if metrics.status != "success":
            llm_error_rate.labels(
                model=metrics.model,
                provider=metrics.provider,
                error_type=metrics.error_type or "unknown"
            ).set(1.0)
        
        # Quality score
        if metrics.quality_score is not None:
            llm_quality_score.labels(
                model=metrics.model,
                provider=metrics.provider,
                quality_type='overall'
            ).set(metrics.quality_score)
    
    def _update_model_metrics(self, metrics: LLMRequestMetrics) -> None:
        """Update aggregated model metrics."""
        model_key = f"{metrics.provider}:{metrics.model}"
        
        if model_key not in self.model_metrics:
            self.model_metrics[model_key] = LLMModelMetrics(
                model=metrics.model,
                provider=metrics.provider
            )
        
        model_metrics = self.model_metrics[model_key]
        
        # Update counters
        model_metrics.total_requests += 1
        model_metrics.total_tokens += metrics.total_tokens
        model_metrics.total_cost_usd += metrics.cost_usd
        
        # Update averages
        if model_metrics.total_requests > 0:
            model_metrics.avg_response_time_ms = (
                (model_metrics.avg_response_time_ms * (model_metrics.total_requests - 1) + 
                 metrics.response_time_ms) / model_metrics.total_requests
            )
        
        # Update error rate
        if metrics.status != "success":
            error_count = sum(1 for m in self.request_metrics 
                            if m.model == metrics.model and m.provider == metrics.provider 
                            and m.status != "success")
            model_metrics.error_rate = error_count / model_metrics.total_requests
        
        # Update quality score
        if metrics.quality_score is not None:
            quality_scores = [m.quality_score for m in self.request_metrics 
                            if m.model == metrics.model and m.provider == metrics.provider 
                            and m.quality_score is not None]
            if quality_scores:
                model_metrics.quality_score = sum(quality_scores) / len(quality_scores)
        
        model_metrics.last_updated = datetime.now()
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory leaks."""
        if datetime.now() - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        self.request_metrics = [m for m in self.request_metrics if m.timestamp > cutoff_time]
        self.last_cleanup = datetime.now()
        
        logger.info("Cleaned up old metrics", 
                   remaining_requests=len(self.request_metrics))
    
    def get_model_metrics(self, model: str, provider: str) -> Optional[LLMModelMetrics]:
        """Get aggregated metrics for a specific model."""
        model_key = f"{provider}:{model}"
        return self.model_metrics.get(model_key)
    
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.request_metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_response_time_ms": 0.0,
                "error_rate": 0.0,
                "models": {}
            }
        
        # Calculate totals
        total_requests = len(recent_metrics)
        total_tokens = sum(m.total_tokens for m in recent_metrics)
        total_cost = sum(m.cost_usd for m in recent_metrics)
        avg_response_time = sum(m.response_time_ms for m in recent_metrics) / total_requests
        error_rate = sum(1 for m in recent_metrics if m.status != "success") / total_requests
        
        # Group by model
        models = {}
        for metrics in recent_metrics:
            model_key = f"{metrics.provider}:{metrics.model}"
            if model_key not in models:
                models[model_key] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost_usd": 0.0,
                    "avg_response_time_ms": 0.0,
                    "error_rate": 0.0
                }
            
            models[model_key]["requests"] += 1
            models[model_key]["tokens"] += metrics.total_tokens
            models[model_key]["cost_usd"] += metrics.cost_usd
        
        # Calculate model averages
        for model_key, stats in models.items():
            if stats["requests"] > 0:
                stats["avg_response_time_ms"] = (
                    sum(m.response_time_ms for m in recent_metrics 
                        if f"{m.provider}:{m.model}" == model_key) / stats["requests"]
                )
                stats["error_rate"] = (
                    sum(1 for m in recent_metrics 
                        if f"{m.provider}:{m.model}" == model_key and m.status != "success") 
                    / stats["requests"]
                )
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "avg_response_time_ms": avg_response_time,
            "error_rate": error_rate,
            "models": models,
            "time_window_hours": hours
        }
    
    def detect_performance_drift(self, model: str, provider: str, 
                               threshold: float = 0.1) -> Dict[str, Any]:
        """Detect performance drift for a specific model."""
        model_key = f"{provider}:{model}"
        if model_key not in self.model_metrics:
            return {"drift_detected": False, "reason": "No data available"}
        
        model_metrics = self.model_metrics[model_key]
        
        # Get recent vs historical metrics
        now = datetime.now()
        recent_cutoff = now - timedelta(hours=1)
        historical_cutoff = now - timedelta(hours=24)
        
        recent_metrics = [m for m in self.request_metrics 
                         if m.model == model and m.provider == provider 
                         and m.timestamp > recent_cutoff]
        
        historical_metrics = [m for m in self.request_metrics 
                            if m.model == model and m.provider == provider 
                            and historical_cutoff < m.timestamp < recent_cutoff]
        
        if not recent_metrics or not historical_metrics:
            return {"drift_detected": False, "reason": "Insufficient data"}
        
        # Calculate drift indicators
        recent_avg_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
        historical_avg_time = sum(m.response_time_ms for m in historical_metrics) / len(historical_metrics)
        
        recent_error_rate = sum(1 for m in recent_metrics if m.status != "success") / len(recent_metrics)
        historical_error_rate = sum(1 for m in historical_metrics if m.status != "success") / len(historical_metrics)
        
        # Check for significant changes
        time_drift = abs(recent_avg_time - historical_avg_time) / historical_avg_time
        error_drift = abs(recent_error_rate - historical_error_rate)
        
        drift_detected = time_drift > threshold or error_drift > threshold
        
        return {
            "drift_detected": drift_detected,
            "time_drift": time_drift,
            "error_drift": error_drift,
            "recent_avg_time_ms": recent_avg_time,
            "historical_avg_time_ms": historical_avg_time,
            "recent_error_rate": recent_error_rate,
            "historical_error_rate": historical_error_rate,
            "threshold": threshold
        }
