"""
LLM Response Caching
===================

Intelligent caching system for LLM responses with:
- Hash-based caching
- TTL management
- Cache invalidation
- Performance optimization
- Memory management
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog
from collections import OrderedDict

logger = structlog.get_logger(__name__)

@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    value: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_accessed: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.last_accessed = self.timestamp
    
    @property
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        return time.time() - self.timestamp > self.ttl
    
    def touch(self):
        """Update access time and count."""
        self.last_accessed = time.time()
        self.access_count += 1

class LLMCache:
    """Intelligent LLM response caching system."""
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: float = 3600.0,  # 1 hour
                 cleanup_interval: float = 300.0,  # 5 minutes
                 enable_compression: bool = True):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.enable_compression = enable_compression
        
        # LRU cache using OrderedDict
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.last_cleanup = time.time()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.info("LLM Cache initialized", 
                   max_size=max_size,
                   default_ttl=default_ttl)
    
    def _generate_key(self, 
                     prompt: str, 
                     model: str, 
                     provider: str,
                     temperature: float = 0.0,
                     max_tokens: Optional[int] = None,
                     **kwargs) -> str:
        """Generate a cache key for the request."""
        # Create a deterministic key from request parameters
        key_data = {
            "prompt": prompt,
            "model": model,
            "provider": provider,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        # Sort keys for consistency
        key_str = json.dumps(key_data, sort_keys=True, separators=(',', ':'))
        
        # Hash the key string
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, 
            prompt: str,
            model: str,
            provider: str,
            temperature: float = 0.0,
            max_tokens: Optional[int] = None,
            **kwargs) -> Optional[Any]:
        """Get a cached response."""
        key = self._generate_key(prompt, model, provider, temperature, max_tokens, **kwargs)
        
        # Check if key exists and is not expired
        if key in self.cache:
            entry = self.cache[key]
            
            if entry.is_expired:
                # Remove expired entry
                del self.cache[key]
                self.misses += 1
                logger.debug("Cache miss - expired entry", key=key[:8])
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry.touch()
            self.hits += 1
            
            logger.debug("Cache hit", 
                        key=key[:8],
                        access_count=entry.access_count,
                        age_seconds=time.time() - entry.timestamp)
            
            return entry.value
        
        self.misses += 1
        logger.debug("Cache miss - not found", key=key[:8])
        return None
    
    def put(self, 
            prompt: str,
            model: str,
            provider: str,
            response: Any,
            temperature: float = 0.0,
            max_tokens: Optional[int] = None,
            ttl: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None,
            **kwargs) -> str:
        """Store a response in the cache."""
        key = self._generate_key(prompt, model, provider, temperature, max_tokens, **kwargs)
        
        # Use provided TTL or default
        cache_ttl = ttl if ttl is not None else self.default_ttl
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=response,
            timestamp=time.time(),
            ttl=cache_ttl,
            metadata=metadata or {}
        )
        
        # Check if we need to evict entries
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Store the entry
        self.cache[key] = entry
        
        # Periodic cleanup
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
        
        logger.debug("Cached response", 
                    key=key[:8],
                    ttl=cache_ttl,
                    cache_size=len(self.cache))
        
        return key
    
    def _evict_lru(self):
        """Evict the least recently used entry."""
        if not self.cache:
            return
        
        # Remove the first (oldest) entry
        key, entry = self.cache.popitem(last=False)
        self.evictions += 1
        
        logger.debug("Evicted LRU entry", 
                    key=key[:8],
                    access_count=entry.access_count,
                    age_seconds=time.time() - entry.timestamp)
    
    def _cleanup_expired(self):
        """Remove all expired entries."""
        self.last_cleanup = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if entry.is_expired:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug("Cleaned up expired entries", 
                        count=len(expired_keys),
                        remaining=len(self.cache))
    
    def invalidate(self, 
                   prompt: str = None,
                   model: str = None,
                   provider: str = None,
                   pattern: str = None) -> int:
        """Invalidate cache entries matching criteria."""
        invalidated = 0
        
        if pattern:
            # Pattern-based invalidation
            for key in list(self.cache.keys()):
                if pattern in key:
                    del self.cache[key]
                    invalidated += 1
        else:
            # Criteria-based invalidation
            for key, entry in list(self.cache.items()):
                should_invalidate = True
                
                if prompt and entry.metadata.get('prompt') != prompt:
                    should_invalidate = False
                if model and entry.metadata.get('model') != model:
                    should_invalidate = False
                if provider and entry.metadata.get('provider') != provider:
                    should_invalidate = False
                
                if should_invalidate:
                    del self.cache[key]
                    invalidated += 1
        
        logger.info("Invalidated cache entries", 
                   count=invalidated,
                   remaining=len(self.cache))
        
        return invalidated
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        
        logger.info("Cleared cache", entries_removed=count)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        # Calculate average age of entries
        now = time.time()
        avg_age = 0.0
        if self.cache:
            ages = [now - entry.timestamp for entry in self.cache.values()]
            avg_age = sum(ages) / len(ages)
        
        # Calculate average access count
        avg_access_count = 0.0
        if self.cache:
            access_counts = [entry.access_count for entry in self.cache.values()]
            avg_access_count = sum(access_counts) / len(access_counts)
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "avg_entry_age_seconds": avg_age,
            "avg_access_count": avg_access_count,
            "memory_usage_mb": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        total_size = 0
        
        for entry in self.cache.values():
            # Estimate size of key + value + metadata
            key_size = len(entry.key.encode())
            value_size = len(str(entry.value).encode())
            metadata_size = len(str(entry.metadata).encode())
            total_size += key_size + value_size + metadata_size
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def get_most_accessed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most accessed cache entries."""
        entries = sorted(self.cache.values(), 
                        key=lambda x: x.access_count, 
                        reverse=True)
        
        return [
            {
                "key": entry.key[:8],
                "access_count": entry.access_count,
                "age_seconds": time.time() - entry.timestamp,
                "metadata": entry.metadata
            }
            for entry in entries[:limit]
        ]
    
    def get_oldest_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the oldest cache entries."""
        entries = sorted(self.cache.values(), 
                        key=lambda x: x.timestamp)
        
        return [
            {
                "key": entry.key[:8],
                "age_seconds": time.time() - entry.timestamp,
                "access_count": entry.access_count,
                "metadata": entry.metadata
            }
            for entry in entries[:limit]
        ]
