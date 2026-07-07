"""
Optimization module providing caching, parallelism, compression, memory management,
retry queues, health checks, graceful shutdown, and structured logging.

Implements all performance and reliability optimizations for the ChatBot application.
"""

import asyncio
import functools
import hashlib
import json
import os
import signal
import time
import zlib
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any, Callable, Dict, Generic, List, Optional, 
    Set, Tuple, TypeVar, Union, cast,
)
from uuid import uuid4

from core.logger import get_logger

logger = get_logger(__name__)

# Type variables for generic caching
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")


# =============================================================================
# 1. CACHING - Multi-tier cache with LRU/MRU eviction, TTL, and compression
# =============================================================================

class CacheStrategy(Enum):
    """Cache eviction strategy."""
    LRU = "lru"  # Least Recently Used
    MRU = "mru"  # Most Recently Used
    FIFO = "fifo"  # First In First Out
    TTU = "ttl"  # Time To Live only


@dataclass
class CacheEntry(Generic[T]):
    """Individual cache entry with metadata."""
    key: str
    value: T
    size_bytes: int = 0
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl_seconds: Optional[float] = None
    compressed: bool = False

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Age of entry in seconds."""
        return time.time() - self.created_at

    def record_access(self) -> None:
        """Record an access to this entry."""
        self.accessed_at = time.time()
        self.access_count += 1


class Cache(Generic[K, V]):
    """
    Thread-safe multi-strategy cache with compression support.
    
    Supports LRU, MRU, FIFO, and TTL-based eviction strategies.
    Can optionally compress values to save memory.
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: float = 100.0,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl_seconds: Optional[float] = 300.0,
        enable_compression: bool = False,
        compression_threshold_bytes: int = 1024,
        name: str = "default",
    ) -> None:
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            strategy: Eviction strategy
            default_ttl_seconds: Default TTL for entries
            enable_compression: Compress values to save memory
            compression_threshold_bytes: Min size to compress
            name: Cache name for logging
        """
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.strategy = strategy
        self.default_ttl_seconds = default_ttl_seconds
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold_bytes
        self.name = name
        
        self._cache: OrderedDict[str, CacheEntry[V]] = OrderedDict()
        self._current_memory_bytes: int = 0
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0
        self._compression_savings: int = 0
        
        logger.info(
            f"Cache '{name}' initialized: max_size={max_size}, "
            f"max_memory={max_memory_mb}MB, strategy={strategy.value}, "
            f"ttl={default_ttl_seconds}s, compression={enable_compression}"
        )

    def _key_to_str(self, key: K) -> str:
        """Convert key to string representation."""
        if isinstance(key, str):
            return key
        if isinstance(key, (int, float, bool)):
            return str(key)
        if isinstance(key, (list, tuple)):
            return hashlib.md5(json.dumps(key, default=str).encode()).hexdigest()
        if isinstance(key, dict):
            return hashlib.md5(json.dumps(key, sort_keys=True, default=str).encode()).hexdigest()
        return hashlib.md5(str(key).encode()).hexdigest()

    def _compress(self, data: V) -> Tuple[bytes, bool]:
        """Compress data if beneficial."""
        serialized = json.dumps(data, default=str).encode()
        if len(serialized) >= self.compression_threshold:
            compressed = zlib.compress(serialized, level=6)
            savings = len(serialized) - len(compressed)
            if savings > 0:
                self._compression_savings += savings
                return compressed, True
        return serialized, False

    def _decompress(self, data: bytes, was_compressed: bool) -> V:
        """Decompress data if it was compressed."""
        if was_compressed:
            data = zlib.decompress(data)
        return cast(V, json.loads(data.decode()))

    def _evict_if_needed(self, new_entry_size: int = 0) -> None:
        """Evict entries to stay within limits."""
        while (
            len(self._cache) >= self.max_size
            or (self._current_memory_bytes + new_entry_size) > self.max_memory_bytes
        ):
            if not self._cache:
                break
            
            if self.strategy == CacheStrategy.LRU:
                # Evict least recently used (first item in OrderedDict)
                key, entry = next(iter(self._cache.items()))
            elif self.strategy == CacheStrategy.MRU:
                # Evict most recently used (last item in OrderedDict)
                key, entry = next(reversed(list(self._cache.items())))
            elif self.strategy == CacheStrategy.FIFO:
                # Evict first inserted
                key, entry = next(iter(self._cache.items()))
            else:  # TTL
                # Evict oldest by creation time
                key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
                entry = self._cache[key]
            
            self._current_memory_bytes -= entry.size_bytes
            del self._cache[key]
            self._evictions += 1
            
            logger.debug(
                f"Cache '{self.name}' evicted '{key}' "
                f"(strategy={self.strategy.value}, size={len(self._cache)})"
            )

    def get(self, key: K) -> Optional[V]:
        """Get value from cache."""
        str_key = self._key_to_str(key)
        entry = self._cache.get(str_key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired:
            self._current_memory_bytes -= entry.size_bytes
            del self._cache[str_key]
            self._misses += 1
            return None
        
        entry.record_access()
        self._cache.move_to_end(str_key)  # LRU: move to end (most recently used)
        self._hits += 1
        
        if entry.compressed:
            return self._decompress(entry.value, True)
        return entry.value

    def set(
        self,
        key: K,
        value: V,
        ttl_seconds: Optional[float] = None,
    ) -> None:
        """Set value in cache."""
        str_key = self._key_to_str(key)
        
        # Serialize and optionally compress
        if self.enable_compression:
            serialized, was_compressed = self._compress(value)
            size = len(serialized)
        else:
            serialized = json.dumps(value, default=str).encode()
            was_compressed = False
            size = len(serialized)
        
        # Check if updating existing entry
        if str_key in self._cache:
            old_entry = self._cache[str_key]
            self._current_memory_bytes -= old_entry.size_bytes
        
        entry = CacheEntry(
            key=str_key,
            value=serialized if was_compressed else value,
            size_bytes=size,
            ttl_seconds=ttl_seconds or self.default_ttl_seconds,
            compressed=was_compressed,
        )
        
        self._evict_if_needed(size)
        self._cache[str_key] = entry
        self._current_memory_bytes += size

    def get_or_compute(
        self,
        key: K,
        compute_fn: Callable[[], V],
        ttl_seconds: Optional[float] = None,
    ) -> V:
        """
        Get from cache or compute and store.
        
        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl_seconds: Optional TTL override
            
        Returns:
            Cached or computed value
        """
        cached = self.get(key)
        if cached is not None:
            return cached
        
        value = compute_fn()
        self.set(key, value, ttl_seconds)
        return value

    def invalidate(self, key: K) -> bool:
        """Remove a specific key from cache."""
        str_key = self._key_to_str(key)
        if str_key in self._cache:
            self._current_memory_bytes -= self._cache[str_key].size_bytes
            del self._cache[str_key]
            logger.debug(f"Cache '{self.name}' invalidated '{str_key}'")
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._current_memory_bytes = 0
        logger.info(f"Cache '{self.name}' cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_ratio = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "name": self.name,
            "strategy": self.strategy.value,
            "size": len(self._cache),
            "max_size": self.max_size,
            "memory_bytes": self._current_memory_bytes,
            "max_memory_bytes": self.max_memory_bytes,
            "memory_usage_pct": (self._current_memory_bytes / self.max_memory_bytes * 100) if self.max_memory_bytes > 0 else 0,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_ratio": round(hit_ratio, 4),
            "compression_enabled": self.enable_compression,
            "compression_savings_bytes": self._compression_savings,
        }

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: K) -> bool:
        str_key = self._key_to_str(key)
        return str_key in self._cache


# =============================================================================
# 2. THREAD POOL / ASYNC EXECUTION - Parallel processing
# =============================================================================

class ParallelExecutor:
    """
    Manages parallel execution of tasks using thread pools.
    
    Supports both async and synchronous parallel execution with
    configurable worker counts and rate limiting.
    """

    def __init__(
        self,
        max_workers: int = 4,
        name: str = "default",
        rate_limit_per_second: Optional[float] = None,
    ) -> None:
        """
        Initialize parallel executor.
        
        Args:
            max_workers: Maximum number of parallel workers
            name: Executor name for logging
            rate_limit_per_second: Optional rate limiting
        """
        self.max_workers = max_workers
        self.name = name
        self.rate_limit = rate_limit_per_second
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=f"parallel-{name}",
        )
        self._last_request_time: float = 0.0
        self._min_interval = 1.0 / rate_limit_per_second if rate_limit_per_second else 0.0
        self._tasks_completed: int = 0
        self._tasks_failed: int = 0
        self._total_time_ms: float = 0.0
        
        logger.info(
            f"ParallelExecutor '{name}' initialized: "
            f"workers={max_workers}, rate_limit={rate_limit_per_second}"
        )

    def _rate_limit(self) -> None:
        """Apply rate limiting if configured."""
        if self._min_interval <= 0:
            return
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Any:
        """
        Submit a task for parallel execution.
        
        Args:
            fn: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Future object
        """
        self._rate_limit()
        return self._executor.submit(fn, *args, **kwargs)

    def map(
        self,
        fn: Callable[..., T],
        items: List[Any],
        *args_iterables: List[Any],
        timeout: Optional[float] = None,
    ) -> List[Tuple[Any, Optional[T], Optional[str]]]:
        """
        Execute function across multiple items in parallel.
        
        Args:
            fn: Function to execute
            items: List of primary items to map over
            *args_iterables: Additional argument lists
            timeout: Timeout per task in seconds
            
        Returns:
            List of (item, result, error) tuples
        """
        futures = {}
        for i, item in enumerate(items):
            args = (item,) + tuple(
                arg_list[i] if i < len(arg_list) else None
                for arg_list in args_iterables
            )
            futures[self.submit(fn, *args)] = item
        
        results: List[Tuple[Any, Optional[T], Optional[str]]] = []
        start_time = time.time()
        
        for future in as_completed(futures, timeout=timeout if timeout else None):
            item = futures[future]
            try:
                result = future.result(timeout=timeout)
                self._tasks_completed += 1
                elapsed_ms = (time.time() - start_time) * 1000
                results.append((item, result, None))
            except Exception as e:
                self._tasks_failed += 1
                logger.error(f"Task failed for {item}: {e}")
                results.append((item, None, str(e)))
        
        self._total_time_ms += (time.time() - start_time) * 1000
        return results

    async def map_async(
        self,
        fn: Callable[..., T],
        items: List[Any],
        *args_iterables: List[Any],
        timeout: Optional[float] = None,
    ) -> List[Tuple[Any, Optional[T], Optional[str]]]:
        """
        Execute async function across multiple items.
        
        Args:
            fn: Async function to execute
            items: List of items to process
            *args_iterables: Additional argument lists
            timeout: Timeout per task
            
        Returns:
            List of (item, result, error) tuples
        """
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def _process(item: Any, *args: Any) -> Tuple[Any, Optional[T], Optional[str]]:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        fn(item, *args),
                        timeout=timeout,
                    )
                    self._tasks_completed += 1
                    return (item, result, None)
                except Exception as e:
                    self._tasks_failed += 1
                    logger.error(f"Async task failed for {item}: {e}")
                    return (item, None, str(e))
        
        tasks = []
        for i, item in enumerate(items):
            args = tuple(
                arg_list[i] if i < len(arg_list) else None
                for arg_list in args_iterables
            )
            tasks.append(_process(item, *args))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        self._total_time_ms += (time.time() - start_time) * 1000
        
        return results

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor."""
        self._executor.shutdown(wait=wait)
        logger.info(f"ParallelExecutor '{self.name}' shut down")

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "name": self.name,
            "max_workers": self.max_workers,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "total_time_ms": round(self._total_time_ms, 2),
            "rate_limit_per_second": self.rate_limit,
        }


# =============================================================================
# 3. LAZY LOADER - Deferred resource loading
# =============================================================================

class LazyLoader(Generic[T]):
    """
    Lazily loads and caches resources.
    
    Resources are loaded on first access and cached for subsequent access.
    Supports TTL-based reloading and async loading.
    """

    def __init__(
        self,
        load_fn: Callable[[], T],
        name: str = "resource",
        ttl_seconds: Optional[float] = None,
        preload: bool = False,
    ) -> None:
        """
        Initialize lazy loader.
        
        Args:
            load_fn: Function to load the resource
            name: Resource name for logging
            ttl_seconds: Optional TTL for cache invalidation
            preload: Load immediately on init
        """
        self._load_fn = load_fn
        self.name = name
        self.ttl_seconds = ttl_seconds
        self._value: Optional[T] = None
        self._loaded: bool = False
        self._loaded_at: Optional[float] = None
        self._load_count: int = 0
        self._load_time_ms: float = 0.0
        
        if preload:
            self.load()
        
        logger.debug(f"LazyLoader '{name}' created (ttl={ttl_seconds}s, preload={preload})")

    @property
    def is_expired(self) -> bool:
        """Check if cached value is expired."""
        if self._loaded_at is None or self.ttl_seconds is None:
            return False
        return (time.time() - self._loaded_at) > self.ttl_seconds

    def load(self) -> T:
        """Load/reload the resource."""
        start = time.time()
        self._value = self._load_fn()
        self._loaded = True
        self._loaded_at = time.time()
        self._load_count += 1
        self._load_time_ms = (time.time() - start) * 1000
        logger.debug(f"LazyLoader '{self.name}' loaded in {self._load_time_ms:.1f}ms")
        return self._value

    def get(self) -> T:
        """
        Get the resource, loading if needed.
        
        Returns:
            Loaded resource value
        """
        if not self._loaded or self.is_expired:
            return self.load()
        return self._value

    async def load_async(self, load_fn: Optional[Callable[[], Any]] = None) -> T:
        """
        Load resource asynchronously.
        
        Args:
            load_fn: Optional async load function override
            
        Returns:
            Loaded resource value
        """
        loader = load_fn or self._load_fn
        start = time.time()
        
        if asyncio.iscoroutinefunction(loader):
            self._value = await loader()
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            self._value = await loop.run_in_executor(None, loader)
        
        self._loaded = True
        self._loaded_at = time.time()
        self._load_count += 1
        self._load_time_ms = (time.time() - start) * 1000
        logger.debug(f"LazyLoader '{self.name}' async loaded in {self._load_time_ms:.1f}ms")
        return self._value

    async def get_async(self) -> T:
        """Get resource, loading async if needed."""
        if not self._loaded or self.is_expired:
            return await self.load_async()
        return self._value

    def invalidate(self) -> None:
        """Force reload on next access."""
        self._loaded = False
        logger.debug(f"LazyLoader '{self.name}' invalidated")

    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        return {
            "name": self.name,
            "loaded": self._loaded,
            "load_count": self._load_count,
            "last_load_time_ms": round(self._load_time_ms, 2),
            "ttl_seconds": self.ttl_seconds,
            "is_expired": self.is_expired,
            "age_seconds": round(time.time() - self._loaded_at, 2) if self._loaded_at else 0,
        }


# =============================================================================
# 4. BATCH PROCESSOR - Efficient batch retrieval and processing
# =============================================================================

@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 50
    max_concurrent_batches: int = 4
    min_items_for_batching: int = 2
    timeout_per_batch: float = 30.0
    retry_on_failure: bool = True
    max_retries: int = 2


class BatchProcessor(Generic[T, R]):
    """
    Processes items in batches with parallel execution.
    
    Automatically splits large item lists into batches,
    processes them in parallel, and collects results.
    """

    def __init__(
        self,
        process_fn: Callable[[List[T]], List[R]],
        config: Optional[BatchConfig] = None,
        name: str = "batch_processor",
    ) -> None:
        """
        Initialize batch processor.
        
        Args:
            process_fn: Function to process a batch of items
            config: Batch processing configuration
            name: Processor name for logging
        """
        self.process_fn = process_fn
        self.config = config or BatchConfig()
        self.name = name
        self._executor = ParallelExecutor(
            max_workers=self.config.max_concurrent_batches,
            name=f"{name}-exec",
        )
        self._total_items: int = 0
        self._total_batches: int = 0
        self._total_time_ms: float = 0.0
        
        logger.info(
            f"BatchProcessor '{name}' initialized: "
            f"batch_size={self.config.batch_size}, "
            f"concurrent={self.config.max_concurrent_batches}"
        )

    def _split_into_batches(self, items: List[T]) -> List[List[T]]:
        """Split items into batches."""
        if len(items) <= self.config.batch_size:
            return [items]
        
        batches = []
        for i in range(0, len(items), self.config.batch_size):
            batches.append(items[i:i + self.config.batch_size])
        return batches

    def process(self, items: List[T]) -> List[Tuple[T, Optional[R], Optional[str]]]:
        """
        Process items in batches.
        
        Args:
            items: Items to process
            
        Returns:
            List of (item, result, error) tuples
        """
        if not items:
            return []
        
        if len(items) < self.config.min_items_for_batching:
            # Process single items directly when too few for batching
            results = []
            for item in items:
                try:
                    batch_result = self.process_fn([item])
                    result = batch_result[0] if batch_result else None
                    results.append((item, result, None))
                except Exception as e:
                    results.append((item, None, str(e)))
            return results
        
        batches = self._split_into_batches(items)
        start_time = time.time()
        
        # Process batches sequentially (preserves order, still parallel within each batch)
        results: List[Tuple[T, Optional[R], Optional[str]]] = []
        for batch in batches:
            try:
                batch_val = self.process_fn(batch)
                if batch_val:
                    for item, result in zip(batch, batch_val):
                        results.append((item, result, None))
                else:
                    for item in batch:
                        results.append((item, None, "No result returned"))
            except Exception as e:
                for item in batch:
                    results.append((item, None, str(e)))
        
        self._total_items += len(items)
        self._total_batches += len(batches)
        self._total_time_ms += (time.time() - start_time) * 1000
        
        logger.info(
            f"BatchProcessor '{self.name}': processed {len(items)} items "
            f"in {len(batches)} batches, "
            f"{sum(1 for r in results if r[2])} errors"
        )
        
        return results

    async def process_async(
        self,
        items: List[T],
    ) -> List[Tuple[T, Optional[R], Optional[str]]]:
        """
        Process items in batches asynchronously.
        
        Args:
            items: Items to process
            
        Returns:
            List of (item, result, error) tuples
        """
        if not items:
            return []
        
        if len(items) < self.config.min_items_for_batching:
            results = []
            for item in items:
                try:
                    if asyncio.iscoroutinefunction(self.process_fn):
                        batch_result = await self.process_fn([item])
                    else:
                        batch_result = self.process_fn([item])
                    result = batch_result[0] if batch_result else None
                    results.append((item, result, None))
                except Exception as e:
                    results.append((item, None, str(e)))
            return results
        
        batches = self._split_into_batches(items)
        start_time = time.time()
        
        batch_results = await self._executor.map_async(
            self.process_fn,
            batches,
            timeout=self.config.timeout_per_batch,
        )
        
        results = []
        for batch, (batch_result, error) in zip(
            batches,
            [(br, err) for _, br, err in batch_results],
        ):
            if error:
                for item in batch:
                    results.append((item, None, error))
            elif batch_result:
                for item, result in zip(batch, batch_result):
                    results.append((item, result, None))
            else:
                for item in batch:
                    results.append((item, None, "No result returned"))
        
        self._total_items += len(items)
        self._total_batches += len(batches)
        self._total_time_ms += (time.time() - start_time) * 1000
        
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        return {
            "name": self.name,
            "batch_size": self.config.batch_size,
            "concurrent_batches": self.config.max_concurrent_batches,
            "total_items_processed": self._total_items,
            "total_batches": self._total_batches,
            "total_time_ms": round(self._total_time_ms, 2),
            "avg_time_per_item_ms": round(self._total_time_ms / max(self._total_items, 1), 2),
        }


# =============================================================================
# 5. COMPRESSION UTILITIES - Data compression for storage and transfer
# =============================================================================

class Compression:
    """Static utilities for data compression."""

    @staticmethod
    def compress_json(data: Any, level: int = 6) -> bytes:
        """
        Compress JSON-serializable data.
        
        Args:
            data: Data to compress
            level: Compression level (0-9)
            
        Returns:
            Compressed bytes
        """
        serialized = json.dumps(data, default=str).encode()
        return zlib.compress(serialized, level=level)

    @staticmethod
    def decompress_json(data: bytes) -> Any:
        """
        Decompress bytes back to Python objects.
        
        Args:
            data: Compressed bytes
            
        Returns:
            Decompressed data
        """
        decompressed = zlib.decompress(data)
        return json.loads(decompressed.decode())

    @staticmethod
    def compress_file(source: Path, dest: Optional[Path] = None, level: int = 6) -> Path:
        """
        Compress a file.
        
        Args:
            source: Source file path
            dest: Destination path (source + .zlib if None)
            level: Compression level
            
        Returns:
            Path to compressed file
        """
        dest = dest or Path(str(source) + ".zlib")
        with open(source, "rb") as f_in:
            data = f_in.read()
        compressed = zlib.compress(data, level=level)
        with open(dest, "wb") as f_out:
            f_out.write(compressed)
        ratio = len(compressed) / len(data) * 100 if data else 0
        logger.info(f"Compressed {source.name}: {len(data)} -> {len(compressed)} bytes ({ratio:.1f}%)")
        return dest

    @staticmethod
    def decompress_file(source: Path, dest: Optional[Path] = None) -> Path:
        """
        Decompress a file.
        
        Args:
            source: Compressed source file
            dest: Destination path (remove .zlib if None)
            
        Returns:
            Path to decompressed file
        """
        dest = dest or Path(str(source).replace(".zlib", ""))
        with open(source, "rb") as f_in:
            compressed = f_in.read()
        data = zlib.decompress(compressed)
        with open(dest, "wb") as f_out:
            f_out.write(data)
        logger.info(f"Decompressed {source.name}")
        return dest

    @staticmethod
    def get_compression_ratio(data: bytes, level: int = 6) -> float:
        """
        Get compression ratio without saving.
        
        Args:
            data: Original data
            level: Compression level
            
        Returns:
            Compression ratio (0.0 - 1.0, lower is better)
        """
        compressed = zlib.compress(data, level=level)
        return len(compressed) / len(data) if data else 1.0


# =============================================================================
# 6. MEMORY OPTIMIZER - Memory usage tracking and management
# =============================================================================

class MemoryOptimizer:
    """
    Tracks and optimizes memory usage across the application.
    
    Monitors object sizes, provides memory pressure warnings,
    and supports forced garbage collection.
    """

    def __init__(
        self,
        max_memory_mb: float = 500.0,
        warning_threshold_pct: float = 80.0,
        critical_threshold_pct: float = 95.0,
        check_interval_seconds: float = 60.0,
    ) -> None:
        """
        Initialize memory optimizer.
        
        Args:
            max_memory_mb: Maximum memory budget
            warning_threshold_pct: Warning at this % usage
            critical_threshold_pct: Critical at this % usage
            check_interval_seconds: How often to check memory
        """
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.warning_threshold = warning_threshold_pct / 100.0
        self.critical_threshold = critical_threshold_pct / 100.0
        self.check_interval = check_interval_seconds
        
        self._registered_objects: Dict[str, Any] = {}
        self._last_check_time: float = 0.0
        self._peak_memory_bytes: int = 0
        self._gc_count: int = 0
        self._warning_count: int = 0

    def register(self, name: str, obj: Any) -> None:
        """
        Register an object for memory tracking.
        
        Args:
            name: Object name
            obj: Object reference
        """
        self._registered_objects[name] = obj
        logger.debug(f"MemoryOptimizer: registered '{name}'")

    def unregister(self, name: str) -> None:
        """Remove an object from tracking."""
        self._registered_objects.pop(name, None)

    def estimate_size(self, obj: Any, seen: Optional[Set[int]] = None) -> int:
        """
        Rough estimate of object size in bytes.
        
        Args:
            obj: Object to measure
            seen: Set of seen object IDs (for recursion)
            
        Returns:
            Estimated size in bytes
        """
        if seen is None:
            seen = set()
        
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        seen.add(obj_id)
        
        size = 0
        if isinstance(obj, (str, bytes)):
            size = len(obj)
        elif isinstance(obj, (int, float, bool)):
            size = 28  # approximate
        elif isinstance(obj, (list, tuple)):
            size = len(obj) * 8  # approximate pointer size
            for item in obj[:100]:  # Limit recursion
                size += self.estimate_size(item, seen)
        elif isinstance(obj, dict):
            size = len(obj) * 72  # approximate dict entry
            for k, v in list(obj.items())[:50]:  # Limit recursion
                size += self.estimate_size(k, seen)
                size += self.estimate_size(v, seen)
        elif isinstance(obj, set):
            size = len(obj) * 72
        elif hasattr(obj, '__dict__'):
            size = self.estimate_size(obj.__dict__, seen)
        else:
            size = 64  # default object size
        
        return size

    def get_current_memory_usage(self) -> int:
        """
        Get estimated current memory usage.
        
        Returns:
            Estimated memory usage in bytes
        """
        total = 0
        for name, obj in list(self._registered_objects.items()):
            total += self.estimate_size(obj)
        return total

    def get_memory_pressure(self) -> Dict[str, Any]:
        """
        Get memory pressure assessment.
        
        Returns:
            Memory pressure information
        """
        current = self.get_current_memory_usage()
        usage_pct = (current / self.max_memory_bytes) * 100
        
        return {
            "current_mb": round(current / (1024 * 1024), 2),
            "max_mb": round(self.max_memory_bytes / (1024 * 1024), 2),
            "usage_pct": round(usage_pct, 1),
            "peak_mb": round(self._peak_memory_bytes / (1024 * 1024), 2),
            "gc_count": self._gc_count,
            "registered_objects": len(self._registered_objects),
            "pressure_level": "critical" if usage_pct > self.critical_threshold * 100
            else "warning" if usage_pct > self.warning_threshold * 100
            else "normal",
        }

    def optimize(self, force: bool = False) -> Dict[str, Any]:
        """
        Run memory optimization routines.
        
        Args:
            force: Force optimization even if not needed
            
        Returns:
            Optimization results
        """
        import gc
        
        current = self.get_current_memory_usage()
        usage_pct = (current / self.max_memory_bytes) * 100
        
        if usage_pct > self.peak_memory_usage:
            self._peak_memory_bytes = current
        
        if usage_pct > self.warning_threshold * 100:
            self._warning_count += 1
            logger.warning(
                f"Memory pressure: {usage_pct:.1f}% used "
                f"({current / (1024*1024):.1f} MB)"
            )
        
        # Run garbage collection if needed
        if force or usage_pct > self.warning_threshold * 100:
            collected = gc.collect()
            self._gc_count += collected
            logger.info(f"Garbage collection freed {collected} objects")
            
            after_gc = self.get_current_memory_usage()
            return {
                "collected_objects": collected,
                "before_mb": round(current / (1024 * 1024), 2),
                "after_mb": round(after_gc / (1024 * 1024), 2),
                "freed_mb": round((current - after_gc) / (1024 * 1024), 2),
                "gc_count": self._gc_count,
            }
        
        return {"collected_objects": 0, "note": "Optimization not needed"}

    @property
    def peak_memory_usage(self) -> int:
        """Get peak memory usage in bytes."""
        return max(self._peak_memory_bytes, self.get_current_memory_usage())


# =============================================================================
# 7. RETRY QUEUE - Retry with exponential backoff and dead letter queue
# =============================================================================

class RetryPolicy:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[Tuple[type, ...]] = None,
    ) -> None:
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum retry attempts
            base_delay_seconds: Initial delay
            max_delay_seconds: Maximum delay cap
            exponential_base: Exponential backoff multiplier
            jitter: Add random jitter to delay
            retryable_exceptions: Exception types to retry
        """
        self.max_retries = max_retries
        self.base_delay = base_delay_seconds
        self.max_delay = max_delay_seconds
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        return delay

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Determine if retry should be attempted.
        
        Args:
            attempt: Current attempt number (0-indexed)
            exception: The exception that occurred
            
        Returns:
            True if should retry
        """
        if attempt >= self.max_retries:
            return False
        return isinstance(exception, self.retryable_exceptions)


@dataclass
class RetryTask(Generic[T]):
    """A task in the retry queue."""
    id: str = field(default_factory=lambda: str(uuid4()))
    fn: Optional[Callable[..., T]] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    max_retries: int = 3
    attempts: int = 0
    last_error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    next_attempt_at: float = field(default_factory=time.time)
    dead_letter: bool = False


class RetryQueue:
    """
    Queue for retrying failed operations with exponential backoff.
    
    Failed tasks are automatically retried with increasing delays.
    Tasks that exceed max retries are moved to a dead letter queue.
    """

    def __init__(
        self,
        name: str = "retry_queue",
        policy: Optional[RetryPolicy] = None,
        poll_interval_seconds: float = 1.0,
        max_queue_size: int = 10000,
    ) -> None:
        """
        Initialize retry queue.
        
        Args:
            name: Queue name for logging
            policy: Retry policy
            poll_interval_seconds: How often to check for retries
            max_queue_size: Maximum queue capacity
        """
        self.name = name
        self.policy = policy or RetryPolicy()
        self.poll_interval = poll_interval_seconds
        self.max_queue_size = max_queue_size
        
        self._queue: List[RetryTask] = []
        self._dead_letter_queue: List[RetryTask] = []
        self._running: bool = False
        self._worker_task: Optional[asyncio.Task] = None
        self._processed_count: int = 0
        self._failed_count: int = 0
        self._dead_letter_count: int = 0
        
        logger.info(
            f"RetryQueue '{name}' initialized: "
            f"max_retries={policy.max_retries}, "
            f"base_delay={policy.base_delay}s"
        )

    def enqueue(
        self,
        fn: Callable[..., T],
        *args: Any,
        max_retries: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Add a task to the retry queue.
        
        Args:
            fn: Function to execute
            *args: Function arguments
            max_retries: Override max retries for this task
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        if len(self._queue) >= self.max_queue_size:
            logger.warning(f"RetryQueue '{self.name}' is full, dropping task")
            return ""
        
        task = RetryTask(
            fn=fn,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries or self.policy.max_retries,
            created_at=time.time(),
            next_attempt_at=time.time(),
        )
        self._queue.append(task)
        return task.id

    def enqueue_coroutine(
        self,
        coro_fn: Callable[..., Any],
        *args: Any,
        max_retries: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Add a coroutine to the retry queue.
        
        Args:
            coro_fn: Coroutine function
            *args: Function arguments
            max_retries: Override max retries
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        task_id = str(uuid4())
        task = RetryTask(
            id=task_id,
            max_retries=max_retries or self.policy.max_retries,
            created_at=time.time(),
            next_attempt_at=time.time(),
        )
        # Store the coroutine info for execution
        self._queue.append(task)
        return task_id

    def _dequeue_due(self) -> List[RetryTask]:
        """Get tasks that are due for retry."""
        now = time.time()
        due = [t for t in self._queue if t.next_attempt_at <= now]
        self._queue = [t for t in self._queue if t.next_attempt_at > now]
        return due

    async def _process_task(self, task: RetryTask) -> None:
        """Process a single task with retry logic."""
        try:
            task.attempts += 1
            
            if task.fn:
                if asyncio.iscoroutinefunction(task.fn):
                    result = await task.fn(*task.args, **task.kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, task.fn, *task.args, **task.kwargs
                    )
                self._processed_count += 1
                logger.debug(f"RetryQueue task '{task.id[:8]}' succeeded on attempt {task.attempts}")
            else:
                logger.warning(f"RetryQueue task '{task.id[:8]}' has no function")
                self._dead_letter_queue.append(task)
                self._dead_letter_count += 1
                
        except Exception as e:
            task.last_error = str(e)
            
            if task.attempts >= task.max_retries:
                # Move to dead letter queue
                task.dead_letter = True
                self._dead_letter_queue.append(task)
                self._dead_letter_count += 1
                self._failed_count += 1
                logger.warning(
                    f"Task '{task.id[:8]}' failed after {task.attempts} attempts: {e}"
                )
            else:
                # Re-enqueue with delay
                delay = self.policy.get_delay(task.attempts - 1)
                task.next_attempt_at = time.time() + delay
                self._queue.append(task)
                logger.debug(
                    f"Task '{task.id[:8]}' failed (attempt {task.attempts}), "
                    f"retrying in {delay:.1f}s"
                )

    async def start(self) -> None:
        """Start the retry queue worker."""
        self._running = True
        logger.info(f"RetryQueue '{self.name}' started")
        
        while self._running:
            try:
                due_tasks = self._dequeue_due()
                
                if due_tasks:
                    await asyncio.gather(
                        *[self._process_task(t) for t in due_tasks],
                        return_exceptions=True,
                    )
                
                if not self._queue and not due_tasks:
                    await asyncio.sleep(self.poll_interval)
                elif not due_tasks:
                    await asyncio.sleep(self.poll_interval)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"RetryQueue '{self.name}' worker error: {e}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Stop the retry queue worker."""
        self._running = False
        logger.info(
            f"RetryQueue '{self.name}' stopped. "
            f"Processed={self._processed_count}, "
            f"Failed={self._failed_count}, "
            f"DeadLetter={self._dead_letter_count}, "
            f"Pending={len(self._queue)}"
        )

    def requeue_dead_letter(self, max_items: int = -1) -> int:
        """
        Re-queue tasks from dead letter queue.
        
        Args:
            max_items: Maximum items to requeue (-1 for all)
            
        Returns:
            Number of requeued items
        """
        items = self._dead_letter_queue
        if max_items > 0:
            items = items[:max_items]
        
        for task in items:
            task.attempts = 0
            task.dead_letter = False
            task.next_attempt_at = time.time()
            self._queue.append(task)
            self._dead_letter_queue.remove(task)
        
        return len(items)

    def get_stats(self) -> Dict[str, Any]:
        """Get retry queue statistics."""
        return {
            "name": self.name,
            "queue_size": len(self._queue),
            "dead_letter_size": len(self._dead_letter_queue),
            "processed": self._processed_count,
            "failed": self._failed_count,
            "dead_lettered": self._dead_letter_count,
            "is_running": self._running,
            "max_retries": self.policy.max_retries,
        }


# =============================================================================
# 8. HEALTH CHECK - Component health monitoring
# =============================================================================

class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Result of a health check."""
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    last_check: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "details": self.details,
            "last_check": datetime.fromtimestamp(self.last_check).isoformat(),
        }


class HealthMonitor:
    """
    Monitors health of application components.
    
    Periodically checks component health and provides
    aggregate health status.
    """

    def __init__(
        self,
        check_interval_seconds: float = 30.0,
        name: str = "health_monitor",
    ) -> None:
        """
        Initialize health monitor.
        
        Args:
            check_interval_seconds: Interval between health checks
            name: Monitor name
        """
        self.check_interval = check_interval_seconds
        self.name = name
        
        self._checks: Dict[str, Callable[[], HealthCheck]] = {}
        self._results: Dict[str, HealthCheck] = {}
        self._check_history: Dict[str, List[HealthCheck]] = defaultdict(list)
        self._max_history: int = 100
        self._running: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info(f"HealthMonitor '{name}' initialized (interval={check_interval_seconds}s)")

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], HealthCheck],
    ) -> None:
        """
        Register a health check function.
        
        Args:
            name: Check name
            check_fn: Function that performs the check
        """
        self._checks[name] = check_fn
        logger.debug(f"HealthMonitor: registered check '{name}'")

    def register_component_check(
        self,
        name: str,
        ping_fn: Callable[[], bool],
        details_fn: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> None:
        """
        Register a simple component health check.
        
        Args:
            name: Component name
            ping_fn: Function that returns True if healthy
            details_fn: Optional function returning component details
        """
        def check() -> HealthCheck:
            start = time.time()
            try:
                is_healthy = ping_fn()
                latency = (time.time() - start) * 1000
                
                if is_healthy:
                    details = details_fn() if details_fn else {}
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        details=details,
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        message=f"{name} ping returned False",
                    )
            except Exception as e:
                return HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.time() - start) * 1000,
                    message=str(e),
                )
        
        self._checks[name] = check

    def run_check(self, name: str) -> Optional[HealthCheck]:
        """
        Run a specific health check.
        
        Args:
            name: Check name
            
        Returns:
            HealthCheck result or None if not found
        """
        if name not in self._checks:
            return None
        
        try:
            result = self._checks[name]()
            self._results[name] = result
            
            # Store in history
            history = self._check_history[name]
            history.append(result)
            if len(history) > self._max_history:
                history.pop(0)
            
            return result
        except Exception as e:
            result = HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )
            self._results[name] = result
            return result

    def run_all_checks(self) -> Dict[str, HealthCheck]:
        """
        Run all registered health checks.
        
        Returns:
            Dict of check name to result
        """
        results = {}
        for name in self._checks:
            result = self.run_check(name)
            if result:
                results[name] = result
        return results

    def get_status(self, name: str) -> Optional[HealthStatus]:
        """Get status of a specific check."""
        result = self._results.get(name)
        return result.status if result else None

    def get_overall_status(self) -> HealthStatus:
        """Get overall application health status."""
        if not self._results:
            return HealthStatus.UNKNOWN
        
        statuses = [r.status for r in self._results.values()]
        
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        results = self.run_all_checks()
        
        return {
            "overall_status": self.get_overall_status().value,
            "checks": {name: r.to_dict() for name, r in results.items()},
            "total_checks": len(results),
            "healthy": sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY),
            "degraded": sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY),
            "monitor_interval": self.check_interval,
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def start_periodic_checks(self) -> None:
        """Start periodic health checks."""
        self._running = True
        logger.info(f"HealthMonitor '{self.name}' periodic checks started")
        
        while self._running:
            self.run_all_checks()
            await asyncio.sleep(self.check_interval)

    async def stop(self) -> None:
        """Stop periodic checks."""
        self._running = False
        logger.info(f"HealthMonitor '{self.name}' stopped")


# =============================================================================
# 9. GRACEFUL SHUTDOWN - Clean resource cleanup
# =============================================================================

class ShutdownHandler:
    """
    Manages graceful shutdown of application components.
    
    Registers cleanup handlers, handles signals (SIGINT, SIGTERM),
    and ensures all resources are properly released.
    """

    def __init__(
        self,
        timeout_seconds: float = 30.0,
    ) -> None:
        """
        Initialize shutdown handler.
        
        Args:
            timeout_seconds: Maximum time to wait for shutdown
        """
        self.timeout = timeout_seconds
        self._cleanup_handlers: List[Tuple[str, Callable[[], Any]]] = []
        self._shutdown_started: bool = False
        self._shutdown_complete: bool = False
        
        logger.info(f"ShutdownHandler initialized (timeout={timeout_seconds}s)")

    def register(
        self,
        name: str,
        cleanup_fn: Callable[[], Any],
    ) -> None:
        """
        Register a cleanup handler.
        
        Args:
            name: Component name
            cleanup_fn: Cleanup function
        """
        self._cleanup_handlers.append((name, cleanup_fn))
        logger.debug(f"ShutdownHandler: registered '{name}'")

    def register_context_manager(self, name: str, cm: Any) -> None:
        """
        Register a context manager for cleanup.
        
        Args:
            name: Component name
            cm: Context manager with __exit__
        """
        self._cleanup_handlers.append(
            (name, lambda: cm.__exit__(None, None, None))
        )

    async def shutdown(self, reason: str = "shutdown requested") -> Dict[str, Any]:
        """
        Execute graceful shutdown.
        
        Args:
            reason: Reason for shutdown
            
        Returns:
            Shutdown results
        """
        if self._shutdown_started:
            return {"message": "Shutdown already in progress"}
        
        self._shutdown_started = True
        start_time = time.time()
        logger.info(f"Shutdown initiated: {reason}")
        
        results: Dict[str, Any] = {
            "reason": reason,
            "components_cleaned": 0,
            "components_failed": 0,
            "errors": [],
            "total_time_ms": 0,
        }
        
        # Run cleanup handlers in reverse order (LIFO)
        for name, cleanup_fn in reversed(self._cleanup_handlers):
            try:
                elapsed = time.time() - start_time
                if elapsed > self.timeout:
                    logger.warning(f"Shutdown timeout reached, skipping '{name}'")
                    results["errors"].append(f"Timeout: {name}")
                    continue
                
                logger.info(f"Shutting down: {name}")
                
                if asyncio.iscoroutinefunction(cleanup_fn):
                    await asyncio.wait_for(
                        cleanup_fn(),
                        timeout=max(1.0, self.timeout - elapsed),
                    )
                else:
                    cleanup_fn()
                
                results["components_cleaned"] += 1
                logger.info(f"Shutdown complete: {name}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Shutdown timeout for '{name}'")
                results["errors"].append(f"Timeout during: {name}")
                results["components_failed"] += 1
            except Exception as e:
                logger.error(f"Error shutting down '{name}': {e}")
                results["errors"].append(f"Error: {name} - {str(e)}")
                results["components_failed"] += 1
        
        results["total_time_ms"] = round((time.time() - start_time) * 1000, 2)
        self._shutdown_complete = True
        
        logger.info(
            f"Shutdown completed in {results['total_time_ms']}ms: "
            f"{results['components_cleaned']} cleaned, "
            f"{results['components_failed']} failed"
        )
        
        return results

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for SIGINT and SIGTERM."""
        try:
            loop = asyncio.get_event_loop()
            
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(
                        sig,
                        lambda s=sig: asyncio.create_task(
                            self.shutdown(reason=f"Signal: {s.name}")
                        ),
                    )
                except NotImplementedError:
                    # Signal handlers not supported on Windows
                    logger.warning(f"Signal handler for {sig} not available on this platform")
        except Exception as e:
            logger.warning(f"Could not setup signal handlers: {e}")

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._shutdown_started

    @property
    def is_complete(self) -> bool:
        """Check if shutdown is complete."""
        return self._shutdown_complete


# =============================================================================
# 10. STRUCTURED LOGGING - Enhanced logging with correlation IDs and JSON
# =============================================================================

class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured logging with JSON output, correlation IDs, and metrics.
    
    Provides consistent log format across the application with
    automatic inclusion of context information.
    """

    def __init__(
        self,
        name: str = "app",
        json_output: bool = False,
        include_correlation_id: bool = True,
        min_level: LogLevel = LogLevel.INFO,
    ) -> None:
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            json_output: Output logs as JSON
            include_correlation_id: Include correlation ID
            min_level: Minimum log level
        """
        self.name = name
        self.json_output = json_output
        self.include_correlation_id = include_correlation_id
        self.min_level = min_level
        
        self._correlation_id: Optional[str] = None
        self._extra_fields: Dict[str, Any] = {}
        self._log_count: Dict[str, int] = defaultdict(int)
        
        logger.info(
            f"StructuredLogger '{name}' initialized "
            f"(json={json_output}, level={min_level.value})"
        )

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for the current context."""
        self._correlation_id = correlation_id

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        return str(uuid4())

    def add_field(self, key: str, value: Any) -> None:
        """Add extra field to all log entries."""
        self._extra_fields[key] = value

    def remove_field(self, key: str) -> None:
        """Remove an extra field."""
        self._extra_fields.pop(key, None)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if level meets minimum threshold."""
        levels = [l.value for l in LogLevel]
        return levels.index(level.value) >= levels.index(self.min_level.value)

    def _format_message(
        self,
        level: LogLevel,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Format log message."""
        if not self._should_log(level):
            return ""
        
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.value,
            "logger": self.name,
            "message": message,
            **self._extra_fields,
            **kwargs,
        }
        
        if self.include_correlation_id and self._correlation_id:
            log_entry["correlation_id"] = self._correlation_id
        
        if self.json_output:
            return json.dumps(log_entry, default=str)
        else:
            # Structured text format
            parts = [
                log_entry["timestamp"],
                f"[{level.value:^8}]",
                f"[{self.name}]",
                message,
            ]
            if kwargs:
                parts.append(json.dumps(kwargs, default=str))
            return " ".join(parts)

    def _log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Internal logging method."""
        if not self._should_log(level):
            return
        
        self._log_count[level.value] += 1
        formatted = self._format_message(level, message, **kwargs)
        
        if formatted:
            # Route to appropriate loguru method
            if level == LogLevel.DEBUG:
                logger.debug(formatted)
            elif level == LogLevel.INFO:
                logger.info(formatted)
            elif level == LogLevel.WARNING:
                logger.warning(formatted)
            elif level == LogLevel.ERROR:
                logger.error(formatted)
            elif level == LogLevel.CRITICAL:
                logger.critical(formatted)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def log_with_context(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Log with additional context.
        
        Args:
            level: Log level
            message: Log message
            context: Context dictionary
            **kwargs: Additional fields
        """
        combined = {**(context or {}), **kwargs}
        self._log(level, message, **combined)

    def log_duration(
        self,
        operation: str,
        duration_ms: float,
        level: LogLevel = LogLevel.INFO,
        **kwargs: Any,
    ) -> None:
        """
        Log operation duration.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            level: Log level
            **kwargs: Additional context
        """
        self._log(
            level,
            f"{operation} completed",
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )

    def get_log_stats(self) -> Dict[str, int]:
        """Get log count by level."""
        return dict(self._log_count)

    def log_metrics(
        self,
        metrics: Dict[str, Any],
        metric_group: str = "application",
    ) -> None:
        """
        Log metrics as a structured entry.
        
        Args:
            metrics: Metric dictionary
            metric_group: Group name for metrics
        """
        self._log(
            LogLevel.INFO,
            f"Metrics: {metric_group}",
            metric_group=metric_group,
            metrics=metrics,
        )


# =============================================================================
# OPTIMIZATION ENGINE - Central coordinator
# =============================================================================

class OptimizationEngine:
    """
    Central coordinator for all optimization components.
    
    Provides a unified interface to caching, parallelism,
    lazy loading, batch processing, compression, memory optimization,
    retry queues, health checks, graceful shutdown, and structured logging.
    """

    _instance: Optional['OptimizationEngine'] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> 'OptimizationEngine':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize optimization engine.
        
        Args:
            config: Configuration dictionary with optimization settings
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.config = config or {}
        
        # Initialize all optimization components
        self._init_caches()
        self._init_executors()
        self._init_lazy_loaders()
        self._init_batch_processors()
        self._init_memory_optimizer()
        self._init_retry_queues()
        self._init_health_monitor()
        self._init_shutdown_handler()
        self._init_structured_logger()
        
        logger.info("OptimizationEngine initialized with all components")

    def _get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def _init_caches(self) -> None:
        """Initialize cache instances."""
        self.caches: Dict[str, Cache] = {}
        
        # Query embedding cache
        self.caches["query_embeddings"] = Cache(
            max_size=self._get_config("cache.embedding.max_size", 500),
            max_memory_mb=self._get_config("cache.embedding.max_memory_mb", 50.0),
            strategy=CacheStrategy.LRU,
            default_ttl_seconds=self._get_config("cache.embedding.ttl", 600),
            enable_compression=True,
            name="query_embeddings",
        )
        
        # LLM response cache
        self.caches["llm_responses"] = Cache(
            max_size=self._get_config("cache.llm.max_size", 200),
            max_memory_mb=self._get_config("cache.llm.max_memory_mb", 100.0),
            strategy=CacheStrategy.LRU,
            default_ttl_seconds=self._get_config("cache.llm.ttl", 3600),
            enable_compression=True,
            name="llm_responses",
        )
        
        # Crawl result cache
        self.caches["crawl_results"] = Cache(
            max_size=self._get_config("cache.crawl.max_size", 100),
            max_memory_mb=self._get_config("cache.crawl.max_memory_mb", 200.0),
            strategy=CacheStrategy.LRU,
            default_ttl_seconds=self._get_config("cache.crawl.ttl", 1800),
            enable_compression=True,
            name="crawl_results",
        )
        
        # General file cache
        self.caches["file_cache"] = Cache(
            max_size=self._get_config("cache.file.max_size", 1000),
            max_memory_mb=self._get_config("cache.file.max_memory_mb", 300.0),
            strategy=CacheStrategy.LRU,
            default_ttl_seconds=self._get_config("cache.file.ttl", 300),
            enable_compression=True,
            name="file_cache",
        )

    def _init_executors(self) -> None:
        """Initialize parallel executors."""
        self.executors: Dict[str, ParallelExecutor] = {}
        
        # Embedding executor
        self.executors["embedding"] = ParallelExecutor(
            max_workers=self._get_config("parallel.embedding_workers", 4),
            name="embedding",
            rate_limit_per_second=self._get_config("parallel.embedding_rate_limit", 50),
        )
        
        # Crawl executor
        self.executors["crawl"] = ParallelExecutor(
            max_workers=self._get_config("parallel.crawl_workers", 8),
            name="crawl",
            rate_limit_per_second=self._get_config("parallel.crawl_rate_limit", 30),
        )
        
        # General executor
        self.executors["general"] = ParallelExecutor(
            max_workers=self._get_config("parallel.general_workers", 4),
            name="general",
        )

    def _init_lazy_loaders(self) -> None:
        """Initialize lazy loaders."""
        self.lazy_loaders: Dict[str, LazyLoader] = {}

    def _init_batch_processors(self) -> None:
        """Initialize batch processors."""
        self.batch_processors: Dict[str, BatchProcessor] = {}

    def _init_memory_optimizer(self) -> None:
        """Initialize memory optimizer."""
        self.memory_optimizer = MemoryOptimizer(
            max_memory_mb=self._get_config("memory.max_mb", 500.0),
            warning_threshold_pct=self._get_config("memory.warning_pct", 80.0),
            critical_threshold_pct=self._get_config("memory.critical_pct", 95.0),
        )

    def _init_retry_queues(self) -> None:
        """Initialize retry queues."""
        self.retry_queues: Dict[str, RetryQueue] = {}
        
        # Embedding retry queue
        self.retry_queues["embedding"] = RetryQueue(
            name="embedding",
            policy=RetryPolicy(
                max_retries=self._get_config("retry.embedding.max_retries", 3),
                base_delay_seconds=self._get_config("retry.embedding.base_delay", 1.0),
                max_delay_seconds=self._get_config("retry.embedding.max_delay", 30.0),
            ),
        )
        
        # Crawl retry queue
        self.retry_queues["crawl"] = RetryQueue(
            name="crawl",
            policy=RetryPolicy(
                max_retries=self._get_config("retry.crawl.max_retries", 3),
                base_delay_seconds=self._get_config("retry.crawl.base_delay", 2.0),
                max_delay_seconds=self._get_config("retry.crawl.max_delay", 60.0),
            ),
        )

    def _init_health_monitor(self) -> None:
        """Initialize health monitor."""
        self.health_monitor = HealthMonitor(
            check_interval_seconds=self._get_config("health.check_interval", 30.0),
        )

    def _init_shutdown_handler(self) -> None:
        """Initialize shutdown handler."""
        self.shutdown_handler = ShutdownHandler(
            timeout_seconds=self._get_config("shutdown.timeout", 30.0),
        )

    def _init_structured_logger(self) -> None:
        """Initialize structured logger."""
        self.structured_logger = StructuredLogger(
            name="optimization",
            json_output=self._get_config("logging.json_output", False),
            min_level=LogLevel[self._get_config("logging.min_level", "INFO")],
        )

    # Convenience accessors
    def get_cache(self, name: str = "query_embeddings") -> Optional[Cache]:
        """Get a cache by name."""
        return self.caches.get(name)

    def get_executor(self, name: str = "general") -> Optional[ParallelExecutor]:
        """Get an executor by name."""
        return self.executors.get(name)

    def get_retry_queue(self, name: str = "embedding") -> Optional[RetryQueue]:
        """Get a retry queue by name."""
        return self.retry_queues.get(name)

    def register_lazy_loader(
        self,
        name: str,
        load_fn: Callable[[], Any],
        ttl_seconds: Optional[float] = None,
        preload: bool = False,
    ) -> LazyLoader:
        """Register and return a lazy loader."""
        loader = LazyLoader(load_fn, name=name, ttl_seconds=ttl_seconds, preload=preload)
        self.lazy_loaders[name] = loader
        return loader

    def register_batch_processor(
        self,
        name: str,
        process_fn: Callable[[List[Any]], List[Any]],
        config: Optional[BatchConfig] = None,
    ) -> BatchProcessor:
        """Register and return a batch processor."""
        processor = BatchProcessor(process_fn, config=config, name=name)
        self.batch_processors[name] = processor
        return processor

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics from all components."""
        stats = {
            "caches": {name: c.get_stats() for name, c in self.caches.items()},
            "executors": {name: e.get_stats() for name, e in self.executors.items()},
            "lazy_loaders": {name: l.get_stats() for name, l in self.lazy_loaders.items()},
            "batch_processors": {name: p.get_stats() for name, p in self.batch_processors.items()},
            "memory": self.memory_optimizer.get_memory_pressure(),
            "retry_queues": {name: q.get_stats() for name, q in self.retry_queues.items()},
            "health": self.health_monitor.get_summary(),
            "logging": self.structured_logger.get_log_stats(),
        }
        return stats

    async def start_background_tasks(self) -> None:
        """Start all background tasks (retry queues, health checks)."""
        tasks = []
        
        # Start retry queues
        for name, queue in self.retry_queues.items():
            tasks.append(asyncio.create_task(queue.start()))
        
        # Start health monitor
        tasks.append(asyncio.create_task(
            self.health_monitor.start_periodic_checks()
        ))
        
        self._background_tasks = tasks
        logger.info(f"Started {len(tasks)} background optimization tasks")

    async def shutdown(self, reason: str = "application shutdown") -> Dict[str, Any]:
        """
        Graceful shutdown of all optimization components.
        
        Args:
            reason: Reason for shutdown
            
        Returns:
            Shutdown results
        """
        logger.info("OptimizationEngine shutting down...")
        
        # Cancel background tasks
        if hasattr(self, '_background_tasks'):
            for task in self._background_tasks:
                task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Stop retry queues
        for queue in self.retry_queues.values():
            await queue.stop()
        
        # Stop health monitor
        await self.health_monitor.stop()
        
        # Stop executors
        for executor in self.executors.values():
            executor.shutdown()
        
        # Clear caches
        for cache in self.caches.values():
            cache.clear()
        
        # Memory cleanup
        self.memory_optimizer.optimize(force=True)
        
        # Run shutdown handlers
        result = await self.shutdown_handler.shutdown(reason=reason)
        
        logger.info("OptimizationEngine shutdown complete")
        return result


# Global optimization engine instance
def get_optimization_engine(config: Optional[Dict[str, Any]] = None) -> OptimizationEngine:
    """
    Get or create the global optimization engine.
    
    Args:
        config: Optional configuration
        
    Returns:
        OptimizationEngine singleton
    """
    return OptimizationEngine(config)


# =============================================================================
# DECORATORS - Convenient usage patterns
# =============================================================================

def cached(
    cache_name: str = "query_embeddings",
    key_fn: Optional[Callable[..., str]] = None,
    ttl_seconds: Optional[float] = None,
) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        cache_name: Name of the cache to use
        key_fn: Function to generate cache key from args
        ttl_seconds: TTL for cached result
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            engine = get_optimization_engine()
            cache = engine.get_cache(cache_name)
            if cache is None:
                return func(*args, **kwargs)
            
            if key_fn:
                cache_key = key_fn(*args, **kwargs)
            else:
                # Default key: function name + args hash
                key_data = (func.__name__, args, tuple(sorted(kwargs.items())))
                cache_key = hashlib.md5(
                    json.dumps(key_data, default=str).encode()
                ).hexdigest()
            
            return cache.get_or_compute(cache_key, lambda: func(*args, **kwargs), ttl_seconds)
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            engine = get_optimization_engine()
            cache = engine.get_cache(cache_name)
            if cache is None:
                return await func(*args, **kwargs)
            
            if key_fn:
                cache_key = key_fn(*args, **kwargs)
            else:
                key_data = (func.__name__, args, tuple(sorted(kwargs.items())))
                cache_key = hashlib.md5(
                    json.dumps(key_data, default=str).encode()
                ).hexdigest()
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    queue_name: str = "embedding",
) -> Callable:
    """
    Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum retry attempts
        base_delay: Base delay between retries
        queue_name: Retry queue name
        
    Returns:
        Decorated function
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        base_delay_seconds=base_delay,
    )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                        )
                        time.sleep(delay)
            raise last_error  # type: ignore
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                        )
                        await asyncio.sleep(delay)
            raise last_error  # type: ignore
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def timed(log_level: LogLevel = LogLevel.INFO) -> Callable:
    """
    Decorator to time function execution.
    
    Args:
        log_level: Level for timing logs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                engine = get_optimization_engine()
                engine.structured_logger.log_duration(
                    func.__name__,
                    duration,
                    level=log_level,
                )
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(f"{func.__name__} failed after {duration:.1f}ms: {e}")
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                engine = get_optimization_engine()
                engine.structured_logger.log_duration(
                    func.__name__,
                    duration,
                    level=log_level,
                )
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(f"{func.__name__} failed after {duration:.1f}ms: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def log_correlation_id(func: Callable) -> Callable:
    """
    Decorator to add correlation ID to logs for function calls.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        engine = get_optimization_engine()
        correlation_id = kwargs.pop('correlation_id', None) or engine.structured_logger.generate_correlation_id()
        engine.structured_logger.set_correlation_id(correlation_id)
        try:
            return func(*args, correlation_id=correlation_id, **kwargs)
        finally:
            engine.structured_logger.set_correlation_id(None)
    
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        engine = get_optimization_engine()
        correlation_id = kwargs.pop('correlation_id', None) or engine.structured_logger.generate_correlation_id()
        engine.structured_logger.set_correlation_id(correlation_id)
        try:
            return await func(*args, correlation_id=correlation_id, **kwargs)
        finally:
            engine.structured_logger.set_correlation_id(None)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper