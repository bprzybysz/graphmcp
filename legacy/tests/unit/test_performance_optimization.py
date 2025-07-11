"""
Comprehensive Unit Tests for the Performance Optimization Module

This test suite covers:
- AsyncCache: memory, disk, and hybrid caching strategies, including TTL, eviction, and metrics.
- ConnectionPool: HTTP connection management, requests, and retry logic.
- ParallelProcessor: batch processing with thread and process pools.
- Decorators: @cached, @timed, and @rate_limited.
- PerformanceManager: orchestration of all optimization components.
"""

import pytest
import asyncio
import time
import os
import io
from unittest.mock import MagicMock, AsyncMock, patch, call
from pathlib import Path
from datetime import datetime, timedelta
import logging
import aiohttp
import pickle

# Import the module and components under test
from concrete.performance_optimization import (
    AsyncCache, CacheStrategy, CacheEntry,
    ConnectionPool,
    ParallelProcessor,
    PerformanceManager,
    cached,
    timed,
    rate_limited,
    get_performance_manager,
    cleanup_performance_manager
)

# --- Test Fixtures ---

@pytest.fixture
def cache_dir(tmp_path):
    """Create a temporary cache directory for tests."""
    return tmp_path / "cache"

# --- Test AsyncCache ---

@pytest.mark.asyncio
class TestAsyncCache:
    """Tests for the AsyncCache component."""

    async def test_init(self, cache_dir):
        """Test cache initialization."""
        cache = AsyncCache(strategy=CacheStrategy.DISK, cache_dir=str(cache_dir))
        assert cache.strategy == CacheStrategy.DISK
        assert cache.cache_dir == cache_dir
        assert cache_dir.exists()

    async def test_memory_cache_set_get(self):
        """Test set and get operations for memory cache."""
        cache = AsyncCache(strategy=CacheStrategy.MEMORY)
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        assert cache.metrics.cache_hits == 1
        assert cache.metrics.cache_misses == 0

    async def test_disk_cache_set_get(self, cache_dir):
        """Test set and get operations for disk cache."""
        cache = AsyncCache(strategy=CacheStrategy.DISK, cache_dir=str(cache_dir))
        await cache.set("key1", {"data": "value1"})
        result = await cache.get("key1")
        assert result == {"data": "value1"}
        
        # Verify it was a disk hit
        assert cache.metrics.cache_hits == 1

    async def test_cache_miss(self):
        """Test cache miss scenario."""
        cache = AsyncCache()
        result = await cache.get("nonexistent_key")
        assert result is None
        assert cache.metrics.cache_misses == 1

    async def test_cache_expiration(self):
        """Test that cache entries expire correctly."""
        cache = AsyncCache(default_ttl=1)
        await cache.set("key1", "value1")
        await asyncio.sleep(1.1)
        result = await cache.get("key1")
        assert result is None
        assert cache.metrics.cache_misses == 1

    async def test_lru_eviction(self):
        """Test Least Recently Used (LRU) eviction policy."""
        cache = AsyncCache(max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        # Access key1 to make it most recently used
        await cache.get("key1")
        
        # Add a new key, which should evict key2
        await cache.set("key3", "value3")
        
        assert await cache.get("key1") == "value1"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key2") is None # Should be evicted

    async def test_hybrid_cache_promotion(self, cache_dir):
        """Test that disk entries are promoted to memory in hybrid mode."""
        cache = AsyncCache(strategy=CacheStrategy.HYBRID, cache_dir=str(cache_dir))
        
        # Manually create a disk entry to simulate a previous session
        disk_key = cache._generate_key("key1")
        disk_file = cache.cache_dir / f"{disk_key}.pkl"
        with open(disk_file, 'wb') as f:
            pickle.dump(CacheEntry("key1", "value1", datetime.utcnow(), None, 0, datetime.utcnow(), 10), f)
        
        # Get should promote it to memory
        assert await cache.get("key1") == "value1"
        assert disk_key in cache._memory_cache

    async def test_clear_cache(self, cache_dir):
        """Test clearing the cache."""
        cache = AsyncCache(strategy=CacheStrategy.HYBRID, cache_dir=str(cache_dir))
        await cache.set("key1", "value1")
        await cache.clear()
        assert await cache.get("key1") is None
        assert not any(cache_dir.iterdir())


# --- Test ConnectionPool ---

@pytest.mark.asyncio
class TestConnectionPool:
    """Tests for the ConnectionPool component."""

    @patch('aiohttp.ClientSession')
    async def test_request_success(self, mock_session_class):
        """Test successful HTTP request."""
        mock_session = mock_session_class.return_value
        mock_response = mock_session.request.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_session.close = AsyncMock() # Ensure close is an AsyncMock

        pool = ConnectionPool()
        result = await pool.request("GET", "http://example.com")

        assert result.status == 200
        mock_session.request.assert_called_once()
        await pool.close()

    @patch('aiohttp.ClientSession')
    async def test_request_retry(self, mock_session_class):
        """Test that requests are retried on failure."""
        mock_session = mock_session_class.return_value
        
        response_ok = AsyncMock()
        response_ok.status = 200
        successful_call = AsyncMock()
        successful_call.__aenter__.return_value = response_ok
        
        mock_session.request.side_effect = [aiohttp.ClientError("Connection failed"), successful_call]
        mock_session.close = AsyncMock() # Ensure close is an AsyncMock
        
        pool = ConnectionPool(retry_attempts=2)
        response = await pool.request("GET", "http://example.com")
        
        assert response.status == 200
        assert mock_session.request.call_count == 2
        await pool.close()

# --- Test ParallelProcessor ---

@pytest.mark.asyncio
class TestParallelProcessor:
    """Tests for the ParallelProcessor component."""

    async def test_process_batch_thread_pool(self):
        """Test batch processing with a thread pool."""
        
        def simple_task(item):
            return item * 2

        items = [1, 2, 3, 4, 5]
        processor = ParallelProcessor()
        results = await processor.process_batch(simple_task, items, batch_size=2)
        
        assert sorted(results) == [2, 4, 6, 8, 10]

# --- Test Decorators ---

@pytest.mark.asyncio
class TestDecorators:
    """Tests for performance optimization decorators."""

    @patch('concrete.performance_optimization.logger.info')
    async def test_timed_decorator(self, mock_log_info):
        """Test the @timed decorator."""
        
        @timed
        async def sample_func():
            await asyncio.sleep(0.01)
            return "done"

        result = await sample_func()
        
        assert result == "done"
        mock_log_info.assert_called_once()
        assert "sample_func executed in" in mock_log_info.call_args[0][0]

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('time.monotonic')
    async def test_rate_limited_decorator(self, mock_monotonic, mock_sleep):
        """Test the @rate_limited decorator."""
        # Use a callable side_effect for monotonic to provide infinite increasing values
        current_time = 0.0
        def monotonic_side_effect():
            nonlocal current_time
            val = current_time
            current_time += 0.01 # Small increment for each call
            return val

        mock_monotonic.side_effect = monotonic_side_effect
        mock_sleep.side_effect = lambda x: None # Don't actually sleep
        
        @rate_limited(calls_per_second=10) # Adjust calls_per_second for a reasonable test
        async def limited_func():
            return time.monotonic()
            
        tasks = [limited_func() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        # With mocked sleep and monotonic, we can expect specific sleep calls
        # 5 calls at 10/sec means 1 every 0.1 sec. First is free, then 4 sleeps.
        assert mock_sleep.call_count >= 4 # At least 4 sleeps for 5 calls at 10/sec

    @patch('concrete.performance_optimization.AsyncCache', new_callable=MagicMock)
    @patch('time.monotonic') # Patch monotonic for cached decorator too
    async def test_cached_decorator(self, mock_monotonic, MockAsyncCache):
        """Test the @cached decorator."""
        # Use a callable side_effect for monotonic to provide infinite increasing values
        current_time = 0.0
        def monotonic_side_effect():
            nonlocal current_time
            val = current_time
            current_time += 0.01 # Small increment for each call
            return val
        mock_monotonic.side_effect = monotonic_side_effect

        mock_cache_instance = MockAsyncCache.return_value
        mock_cache_instance.get = AsyncMock(side_effect=[None, "cached_value"])
        mock_cache_instance.set = AsyncMock()

        @cached(ttl=60)
        async def expensive_func(x, y):
            return x + y
        
        # First call, should be a miss
        result1 = await expensive_func(2, 3)
        assert result1 == 5
        mock_cache_instance.get.assert_called_once()
        mock_cache_instance.set.assert_called_once()
        
        # Second call, should be a hit
        result2 = await expensive_func(2, 3)
        assert result2 == "cached_value"
        assert mock_cache_instance.get.call_count == 2
        assert mock_cache_instance.set.call_count == 1 # Not called again


# --- Test PerformanceManager ---

@pytest.mark.asyncio
class TestPerformanceManager:
    """Tests for the PerformanceManager class."""
    
    @patch('concrete.performance_optimization.AsyncCache')
    @patch('concrete.performance_optimization.ConnectionPool')
    @patch('concrete.performance_optimization.ParallelProcessor')
    def setup_method(self, method, mock_processor, mock_pool, mock_cache):
        from concrete import performance_optimization
        performance_optimization._performance_manager = None
        
        self.manager = PerformanceManager()
        self.manager.cache = mock_cache.return_value
        self.manager.connection_pool = mock_pool.return_value
        self.manager.parallel_processor = mock_processor.return_value

    @patch('time.monotonic') # Patch monotonic for test_cached_api_call_success
    async def test_cached_api_call_success(self, mock_monotonic):
        """Test a successful cached API call."""
        current_time = 0.0
        def monotonic_side_effect():
            nonlocal current_time
            val = current_time
            current_time += 0.01 # Small increment for each call
            return val
        mock_monotonic.side_effect = monotonic_side_effect

        mock_api_func = AsyncMock(return_value="api_result")
        self.manager.cache.get.return_value = None
        self.manager.cache.set.return_value = None

        result = await self.manager.cached_api_call("test_key", mock_api_func, "arg1", kwarg="value")

        assert result == "api_result"
        self.manager.cache.get.assert_called_once_with("test_key")
        self.manager.cache.set.assert_called_once()
        
    async def test_optimize_repository_processing(self):
        """Test repository processing optimization."""
        
        async def fake_processor(repo):
            await asyncio.sleep(0.01)
            return f"processed_{repo}"

        self.manager.parallel_processor.process_batch = AsyncMock(
            return_value=[f"processed_repo_{i}" for i in range(10)]
        )

        repos = [f"repo_{i}" for i in range(10)]
        results = await self.manager.optimize_repository_processing(
            repos, fake_processor
        )

        assert len(results) == 10
        self.manager.parallel_processor.process_batch.assert_called_once()
        
    async def test_pooled_http_request(self):
        """Test making an HTTP request via the manager's pool."""
        self.manager.connection_pool.request = AsyncMock(return_value="response")
        
        result = await self.manager.pooled_http_request("GET", "http://example.com")
        
        assert result == "response"
        self.manager.connection_pool.request.assert_called_once_with(
            "GET", "http://example.com"
        )
        
    async def tear_down(self):
        # This method is for pytest-asyncio, not a standard pytest fixture
        pass

# --- Test Module-level Functions ---

@patch('concrete.performance_optimization.PerformanceManager')
def test_get_performance_manager(mock_manager):
    """Test the singleton getter for PerformanceManager."""
    # Prevent singleton issues by resetting the global manager
    from concrete import performance_optimization
    performance_optimization._performance_manager = None
    
    manager1 = get_performance_manager()
    manager2 = get_performance_manager()
    assert manager1 is manager2
    assert mock_manager.call_count == 1

@pytest.mark.asyncio
async def test_cleanup_performance_manager():
    """Test the cleanup function."""
    manager = get_performance_manager()
    manager.close = AsyncMock()
    await cleanup_performance_manager()
    manager.close.assert_called_once() 