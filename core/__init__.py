"""
Core package containing shared utilities, logging, exceptions, and base classes.

This package provides the foundational infrastructure for the entire application,
including the optimization engine for caching, parallel execution, batch processing,
compression, memory management, retry queues, health checks, and structured logging.
"""

from core.exceptions import *
from core.logger import get_logger
from core.optimization import (
    # Caching
    Cache,
    CacheStrategy,
    CacheEntry,
    # Parallel Execution
    ParallelExecutor,
    # Lazy Loading
    LazyLoader,
    # Batch Processing
    BatchProcessor,
    BatchConfig,
    # Compression
    Compression,
    # Memory Management
    MemoryOptimizer,
    # Retry
    RetryQueue,
    RetryPolicy,
    RetryTask,
    # Health Checks
    HealthMonitor,
    HealthCheck,
    HealthStatus,
    # Graceful Shutdown
    ShutdownHandler,
    # Structured Logging
    StructuredLogger,
    LogLevel,
    # Engine
    OptimizationEngine,
    get_optimization_engine,
    # Decorators
    cached,
    retry,
    timed,
    log_correlation_id,
)

__all__ = [
    "get_logger",
    "AppException",
    "ValidationError",
    "CrawlerError",
    "IngestionError",
    "RetrieverError",
    "ChatbotError",
    "EvaluationError",
    # Caching
    "Cache",
    "CacheStrategy",
    "CacheEntry",
    # Parallel Execution
    "ParallelExecutor",
    # Lazy Loading
    "LazyLoader",
    # Batch Processing
    "BatchProcessor",
    "BatchConfig",
    # Compression
    "Compression",
    # Memory Management
    "MemoryOptimizer",
    # Retry
    "RetryQueue",
    "RetryPolicy",
    "RetryTask",
    # Health Checks
    "HealthMonitor",
    "HealthCheck",
    "HealthStatus",
    # Graceful Shutdown
    "ShutdownHandler",
    # Structured Logging
    "StructuredLogger",
    "LogLevel",
    # Engine
    "OptimizationEngine",
    "get_optimization_engine",
    # Decorators
    "cached",
    "retry",
    "timed",
    "log_correlation_id",
]
