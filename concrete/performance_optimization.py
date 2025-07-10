"""
Performance Optimization Module for Database Decommissioning Workflow.

This module provides caching mechanisms, async optimizations, connection pooling,
and other performance enhancements for production-scale database decommissioning.
"""

import asyncio
import time
import hashlib
import json
import pickle
import os
from typing import Dict, List, Any, Optional, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiohttp
import aiofiles
import logging
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheStrategy(Enum):
    """Cache strategy options."""
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"
    HYBRID = "hybrid"

@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    key: str
    value: T
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: datetime
    size_bytes: int

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics."""
    cache_hits: int = 0
    cache_misses: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    total_processing_time: float = 0.0
    parallel_operations: int = 0
    memory_saved_bytes: int = 0
    disk_saved_bytes: int = 0
    
    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property
    def efficiency_score(self) -> float:
        """Calculate overall efficiency score."""
        hit_ratio_score = self.cache_hit_ratio * 100
        speed_score = max(0, 100 - (self.avg_response_time * 10))
        return (hit_ratio_score + speed_score) / 2

class AsyncCache:
    """High-performance async cache with multiple storage backends."""
    
    def __init__(self, 
                 strategy: CacheStrategy = CacheStrategy.MEMORY,
                 max_size: int = 1000,
                 default_ttl: int = 3600,
                 cache_dir: str = "cache"):
        self.strategy = strategy
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory cache
        self._memory_cache: Dict[str, CacheEntry] = {}
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        
        # Cleanup task (will be created when needed)
        self._cleanup_task = None
        self._cleanup_started = False
    
    def _ensure_cleanup_task(self):
        """Ensure cleanup task is started (only when event loop is available)."""
        if not self._cleanup_started:
            try:
                async def cleanup_expired():
                    while True:
                        await asyncio.sleep(300)  # Every 5 minutes
                        await self._cleanup_expired_entries()
                
                self._cleanup_task = asyncio.create_task(cleanup_expired())
                self._cleanup_started = True
            except RuntimeError:
                # No event loop available yet, will try again later
                pass
    
    def _generate_key(self, key: str) -> str:
        """Generate cache key with hash for consistency."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Ensure cleanup task is running
        self._ensure_cleanup_task()
        
        cache_key = self._generate_key(key)
        self.metrics.total_requests += 1
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            
            # Check expiration
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                await self._remove_from_cache(cache_key)
                self.metrics.cache_misses += 1
                return None
            
            # Update access metadata
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            
            self.metrics.cache_hits += 1
            logger.debug(f"Cache hit for key: {key}")
            return entry.value
        
        # Check disk cache for DISK or HYBRID strategy
        if self.strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            disk_value = await self._get_from_disk(cache_key)
            if disk_value is not None:
                # Promote to memory cache if using HYBRID
                if self.strategy == CacheStrategy.HYBRID:
                    await self.set(key, disk_value, promote_to_memory=True)
                
                self.metrics.cache_hits += 1
                logger.debug(f"Disk cache hit for key: {key}")
                return disk_value
        
        self.metrics.cache_misses += 1
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: Optional[int] = None,
                  promote_to_memory: bool = False) -> None:
        """Set value in cache."""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
        
        # Calculate size
        size_bytes = len(pickle.dumps(value))
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            access_count=1,
            last_accessed=datetime.utcnow(),
            size_bytes=size_bytes
        )
        
        # Store based on strategy
        if self.strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID] or promote_to_memory:
            await self._set_in_memory(cache_key, entry)
        
        if self.strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            await self._set_on_disk(cache_key, entry)
        
        logger.debug(f"Cached value for key: {key} (size: {size_bytes} bytes)")
    
    async def _set_in_memory(self, cache_key: str, entry: CacheEntry) -> None:
        """Set entry in memory cache."""
        # Check if we need to evict entries
        if len(self._memory_cache) >= self.max_size:
            await self._evict_lru_entry()
        
        self._memory_cache[cache_key] = entry
        self.metrics.memory_saved_bytes += entry.size_bytes
    
    async def _set_on_disk(self, cache_key: str, entry: CacheEntry) -> None:
        """Set entry on disk cache."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            async with aiofiles.open(cache_file, 'wb') as f:
                await f.write(pickle.dumps(entry))
            
            self.metrics.disk_saved_bytes += entry.size_bytes
            logger.debug(f"Saved to disk cache: {cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to save to disk cache: {e}")
    
    async def _get_from_disk(self, cache_key: str) -> Optional[Any]:
        """Get entry from disk cache."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            async with aiofiles.open(cache_file, 'rb') as f:
                data = await f.read()
                entry = pickle.loads(data)
            
            # Check expiration
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                await self._remove_disk_entry(cache_key)
                return None
            
            return entry.value
            
        except Exception as e:
            logger.error(f"Failed to load from disk cache: {e}")
            await self._remove_disk_entry(cache_key)
            return None
    
    async def _evict_lru_entry(self) -> None:
        """Evict least recently used entry from memory."""
        if not self._memory_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k].last_accessed
        )
        
        # Remove from memory
        entry = self._memory_cache.pop(lru_key)
        self.metrics.memory_saved_bytes -= entry.size_bytes
        
        logger.debug(f"Evicted LRU entry: {lru_key}")
    
    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries."""
        now = datetime.utcnow()
        expired_keys = []
        
        # Check memory cache
        for key, entry in self._memory_cache.items():
            if entry.expires_at and now > entry.expires_at:
                expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            await self._remove_from_cache(key)
        
        # Clean up disk cache
        if self.strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            await self._cleanup_disk_cache()
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _cleanup_disk_cache(self) -> None:
        """Clean up expired disk cache files."""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        
        for cache_file in cache_files:
            try:
                async with aiofiles.open(cache_file, 'rb') as f:
                    data = await f.read()
                    entry = pickle.loads(data)
                
                if entry.expires_at and datetime.utcnow() > entry.expires_at:
                    cache_file.unlink()
                    logger.debug(f"Removed expired disk cache: {cache_file}")
                    
            except Exception as e:
                logger.warning(f"Error cleaning disk cache file {cache_file}: {e}")
                cache_file.unlink()  # Remove corrupted files
    
    async def _remove_from_cache(self, cache_key: str) -> None:
        """Remove entry from all cache levels."""
        if cache_key in self._memory_cache:
            entry = self._memory_cache.pop(cache_key)
            self.metrics.memory_saved_bytes -= entry.size_bytes
        
        await self._remove_disk_entry(cache_key)
    
    async def _remove_disk_entry(self, cache_key: str) -> None:
        """Remove entry from disk cache."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to remove disk cache file: {e}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()
        
        # Clear disk cache
        cache_files = list(self.cache_dir.glob("*.pkl"))
        for cache_file in cache_files:
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to remove cache file {cache_file}: {e}")
        
        # Reset metrics
        self.metrics = PerformanceMetrics()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "strategy": self.strategy.value,
            "memory_entries": len(self._memory_cache),
            "max_size": self.max_size,
            "metrics": asdict(self.metrics),
            "efficiency_score": self.metrics.efficiency_score,
            "cache_hit_ratio": self.metrics.cache_hit_ratio
        }

class ConnectionPool:
    """High-performance connection pool for external services."""
    
    def __init__(self, 
                 max_connections: int = 100,
                 timeout: float = 30.0,
                 retry_attempts: int = 3):
        self.max_connections = max_connections
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # HTTP session pool
        self._http_connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=20,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        self._http_session = aiohttp.ClientSession(
            connector=self._http_connector,
            timeout=aiohttp.ClientTimeout(total=timeout)
        )
        
        # Connection metrics
        self.active_connections = 0
        self.total_requests = 0
        self.failed_requests = 0
    
    async def request(self, 
                      method: str, 
                      url: str, 
                      **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with connection pooling."""
        self.active_connections += 1
        self.total_requests += 1
        
        try:
            for attempt in range(self.retry_attempts):
                try:
                    async with self._http_session.request(method, url, **kwargs) as response:
                        return response
                        
                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        self.failed_requests += 1
                        logger.error(f"Request failed after {self.retry_attempts} attempts: {e}")
                        raise
                    
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
        
        finally:
            self.active_connections -= 1
    
    async def close(self):
        """Close connection pool."""
        await self._http_session.close()
        await self._http_connector.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "max_connections": self.max_connections,
            "active_connections": self.active_connections,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": ((self.total_requests - self.failed_requests) / 
                           self.total_requests if self.total_requests > 0 else 1.0)
        }

class ParallelProcessor:
    """High-performance parallel processing utility."""
    
    def __init__(self, 
                 max_workers: int = None,
                 use_process_pool: bool = False):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.use_process_pool = use_process_pool
        
        if use_process_pool:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    async def process_batch(self, 
                           func: Callable,
                           items: List[Any],
                           batch_size: int = 10,
                           **kwargs) -> List[Any]:
        """Process items in parallel batches."""
        results = []
        
        # Process in batches to avoid overwhelming the system
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Create tasks for batch
            tasks = []
            for item in batch:
                if asyncio.iscoroutinefunction(func):
                    task = func(item, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    task = loop.run_in_executor(self.executor, func, item, **kwargs)
                tasks.append(task)
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches to prevent overwhelming
            if i + batch_size < len(items):
                await asyncio.sleep(0.1)
        
        return results
    
    def close(self):
        """Close executor."""
        self.executor.shutdown(wait=True)

# Performance optimization decorators
def cached(ttl: int = 3600, 
          strategy: CacheStrategy = CacheStrategy.MEMORY,
          key_func: Optional[Callable] = None):
    """Decorator for caching function results."""
    def decorator(func):
        cache = AsyncCache(strategy=strategy, default_ttl=ttl)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            await cache.set(cache_key, result, ttl)
            
            logger.debug(f"Function {func.__name__} executed in {execution_time:.2f}s")
            return result
        
        wrapper._cache = cache
        return wrapper
    return decorator

def timed(func):
    """Decorator for timing function execution."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}s")
    return wrapper

def rate_limited(calls_per_second: float):
    """Decorator for rate limiting function calls."""
    def decorator(func):
        last_called = [0.0]
        min_interval = 1.0 / calls_per_second
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            time_since_last = now - last_called[0]
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
            
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Global performance manager
class PerformanceManager:
    """Global performance optimization manager."""
    
    def __init__(self):
        self.cache = AsyncCache(strategy=CacheStrategy.HYBRID)
        self.connection_pool = ConnectionPool()
        self.parallel_processor = ParallelProcessor()
        self.metrics = PerformanceMetrics()
        
        # Performance settings
        self.enable_caching = True
        self.enable_parallel_processing = True
        self.enable_connection_pooling = True
    
    async def optimize_repository_processing(self, 
                                           repositories: List[str],
                                           processor_func: Callable) -> List[Any]:
        """Optimize repository processing with parallel execution and caching."""
        if not self.enable_parallel_processing:
            results = []
            for repo in repositories:
                result = await processor_func(repo)
                results.append(result)
            return results
        
        # Process repositories in parallel
        return await self.parallel_processor.process_batch(
            processor_func,
            repositories,
            batch_size=5  # Process 5 repositories at a time
        )
    
    async def cached_api_call(self, 
                             cache_key: str,
                             api_func: Callable,
                             *args,
                             ttl: int = 1800,
                             **kwargs) -> Any:
        """Make cached API call."""
        if not self.enable_caching:
            return await api_func(*args, **kwargs)
        
        # Try cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Make API call
        result = await api_func(*args, **kwargs)
        
        # Cache result
        await self.cache.set(cache_key, result, ttl)
        
        return result
    
    async def pooled_http_request(self, 
                                 method: str, 
                                 url: str, 
                                 **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request using connection pool."""
        if not self.enable_connection_pooling:
            async with aiohttp.ClientSession() as session:
                return await session.request(method, url, **kwargs)
        
        return await self.connection_pool.request(method, url, **kwargs)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            "cache_stats": self.cache.get_stats(),
            "connection_pool_stats": self.connection_pool.get_stats(),
            "optimization_settings": {
                "caching_enabled": self.enable_caching,
                "parallel_processing_enabled": self.enable_parallel_processing,
                "connection_pooling_enabled": self.enable_connection_pooling
            },
            "performance_score": self.cache.metrics.efficiency_score
        }
    
    async def close(self):
        """Clean up resources."""
        await self.connection_pool.close()
        self.parallel_processor.close()

# Global performance manager instance
_performance_manager = None

def get_performance_manager() -> PerformanceManager:
    """Get or create global performance manager."""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager()
    return _performance_manager

async def cleanup_performance_manager():
    """Clean up global performance manager."""
    global _performance_manager
    if _performance_manager is not None:
        await _performance_manager.close()
        _performance_manager = None 