"""
Comprehensive Admin Dashboard

Displays system statistics, metrics, and logs for monitoring
the College FAQ Chatbot system health and performance.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict
import statistics


@dataclass
class SystemMetrics:
    """System performance metrics."""
    
    # Crawling metrics
    total_pages_crawled: int = 0
    successful_crawls: int = 0
    failed_crawls: int = 0
    pages_by_domain: Dict[str, int] = field(default_factory=dict)
    crawl_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Chunking metrics
    total_chunks: int = 0
    avg_chunk_size: float = 0.0
    min_chunk_size: int = 0
    max_chunk_size: int = 0
    chunks_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Embedding metrics
    total_embeddings: int = 0
    successful_embeddings: int = 0
    failed_embeddings: int = 0
    embedding_errors: List[Dict[str, Any]] = field(default_factory=list)
    avg_embedding_latency_ms: float = 0.0
    
    # Query metrics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_query_latency_ms: float = 0.0
    queries_by_category: Dict[str, int] = field(default_factory=dict)
    query_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Vector DB metrics
    vector_db_size_mb: float = 0.0
    vector_db_documents: int = 0
    vector_db_collections: int = 0
    vector_db_status: str = "unknown"
    
    # Knowledge base metrics
    kb_total_documents: int = 0
    kb_total_size_mb: float = 0.0
    kb_documents_by_category: Dict[str, int] = field(default_factory=dict)
    kb_last_update: Optional[str] = None
    
    # System metrics
    system_uptime_hours: float = 0.0
    system_errors: List[Dict[str, Any]] = field(default_factory=list)
    last_backup_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "crawling": {
                "total_pages": self.total_pages_crawled,
                "successful": self.successful_crawls,
                "failed": self.failed_crawls,
                "success_rate": (
                    self.successful_crawls / self.total_pages_crawled * 100
                    if self.total_pages_crawled > 0 else 0
                ),
                "by_domain": self.pages_by_domain,
                "errors": self.crawl_errors,
            },
            "chunking": {
                "total_chunks": self.total_chunks,
                "avg_size_bytes": self.avg_chunk_size,
                "min_size": self.min_chunk_size,
                "max_size": self.max_chunk_size,
                "by_type": self.chunks_by_type,
            },
            "embeddings": {
                "total": self.total_embeddings,
                "successful": self.successful_embeddings,
                "failed": self.failed_embeddings,
                "success_rate": (
                    self.successful_embeddings / self.total_embeddings * 100
                    if self.total_embeddings > 0 else 0
                ),
                "avg_latency_ms": self.avg_embedding_latency_ms,
                "errors": self.embedding_errors,
            },
            "queries": {
                "total": self.total_queries,
                "successful": self.successful_queries,
                "failed": self.failed_queries,
                "success_rate": (
                    self.successful_queries / self.total_queries * 100
                    if self.total_queries > 0 else 0
                ),
                "avg_latency_ms": self.avg_query_latency_ms,
                "by_category": self.queries_by_category,
                "errors": self.query_errors,
            },
            "vector_db": {
                "size_mb": self.vector_db_size_mb,
                "documents": self.vector_db_documents,
                "collections": self.vector_db_collections,
                "status": self.vector_db_status,
            },
            "knowledge_base": {
                "total_documents": self.kb_total_documents,
                "total_size_mb": self.kb_total_size_mb,
                "by_category": self.kb_documents_by_category,
                "last_update": self.kb_last_update,
            },
            "system": {
                "uptime_hours": self.system_uptime_hours,
                "errors": self.system_errors,
                "last_backup": self.last_backup_time,
            },
        }


class AdminMetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self) -> None:
        """Initialize collector."""
        self.metrics = SystemMetrics()
        self.metrics_history: List[tuple] = []  # (timestamp, metrics)
        self.start_time = datetime.utcnow()

    def update_crawling_metrics(
        self,
        pages_crawled: int,
        successful: int,
        failed: int,
        by_domain: Dict[str, int],
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update crawling metrics."""
        self.metrics.total_pages_crawled = pages_crawled
        self.metrics.successful_crawls = successful
        self.metrics.failed_crawls = failed
        self.metrics.pages_by_domain = by_domain
        if errors:
            self.metrics.crawl_errors = errors[-10:]  # Keep last 10 errors

    def update_chunking_metrics(
        self,
        total_chunks: int,
        sizes: List[int],
        by_type: Dict[str, int],
    ) -> None:
        """Update chunking metrics."""
        self.metrics.total_chunks = total_chunks
        if sizes:
            self.metrics.avg_chunk_size = statistics.mean(sizes)
            self.metrics.min_chunk_size = min(sizes)
            self.metrics.max_chunk_size = max(sizes)
        self.metrics.chunks_by_type = by_type

    def update_embedding_metrics(
        self,
        total: int,
        successful: int,
        failed: int,
        latencies: List[float],
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update embedding metrics."""
        self.metrics.total_embeddings = total
        self.metrics.successful_embeddings = successful
        self.metrics.failed_embeddings = failed
        if latencies:
            self.metrics.avg_embedding_latency_ms = statistics.mean(latencies)
        if errors:
            self.metrics.embedding_errors = errors[-10:]

    def update_query_metrics(
        self,
        total: int,
        successful: int,
        failed: int,
        latencies: List[float],
        by_category: Dict[str, int],
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update query metrics."""
        self.metrics.total_queries = total
        self.metrics.successful_queries = successful
        self.metrics.failed_queries = failed
        if latencies:
            self.metrics.avg_query_latency_ms = statistics.mean(latencies)
        self.metrics.queries_by_category = by_category
        if errors:
            self.metrics.query_errors = errors[-10:]

    def update_vector_db_metrics(
        self,
        size_mb: float,
        documents: int,
        collections: int,
        status: str,
    ) -> None:
        """Update vector database metrics."""
        self.metrics.vector_db_size_mb = size_mb
        self.metrics.vector_db_documents = documents
        self.metrics.vector_db_collections = collections
        self.metrics.vector_db_status = status

    def update_kb_metrics(
        self,
        total_documents: int,
        total_size_mb: float,
        by_category: Dict[str, int],
        last_update: Optional[str] = None,
    ) -> None:
        """Update knowledge base metrics."""
        self.metrics.kb_total_documents = total_documents
        self.metrics.kb_total_size_mb = total_size_mb
        self.metrics.kb_documents_by_category = by_category
        self.metrics.kb_last_update = last_update or datetime.utcnow().isoformat()

    def update_system_metrics(self) -> None:
        """Update system metrics."""
        uptime = datetime.utcnow() - self.start_time
        self.metrics.system_uptime_hours = uptime.total_seconds() / 3600

    def record_error(self, error_type: str, message: str) -> None:
        """Record system error."""
        error = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.metrics.system_errors.append(error)
        # Keep last 20 errors
        if len(self.metrics.system_errors) > 20:
            self.metrics.system_errors = self.metrics.system_errors[-20:]

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return self.metrics.to_dict()

    def get_health_status(self) -> Dict[str, str]:
        """Get system health status."""
        status = {}

        # Crawling health
        crawl_success_rate = (
            self.metrics.successful_crawls / self.metrics.total_pages_crawled * 100
            if self.metrics.total_pages_crawled > 0
            else 0
        )
        status["crawling"] = (
            "healthy" if crawl_success_rate >= 95 else
            "warning" if crawl_success_rate >= 80 else
            "error"
        )

        # Embedding health
        embed_success_rate = (
            self.metrics.successful_embeddings / self.metrics.total_embeddings * 100
            if self.metrics.total_embeddings > 0
            else 0
        )
        status["embeddings"] = (
            "healthy" if embed_success_rate >= 95 else
            "warning" if embed_success_rate >= 80 else
            "error"
        )

        # Query health
        query_success_rate = (
            self.metrics.successful_queries / self.metrics.total_queries * 100
            if self.metrics.total_queries > 0
            else 0
        )
        status["queries"] = (
            "healthy" if query_success_rate >= 95 else
            "warning" if query_success_rate >= 80 else
            "error"
        )

        # Vector DB health
        status["vector_db"] = self.metrics.vector_db_status

        return status

    def export_metrics(self, filepath: str) -> None:
        """Export metrics to JSON."""
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics.to_dict(),
            "health": self.get_health_status(),
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


class AdminDashboard:
    """Admin dashboard for system monitoring."""

    def __init__(self) -> None:
        """Initialize dashboard."""
        self.collector = AdminMetricsCollector()
        self.logs: List[Dict[str, Any]] = []

    def log_event(
        self,
        event_type: str,
        component: str,
        message: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log system event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "component": component,
            "message": message,
            "level": level,
            "data": data or {},
        }

        self.logs.append(event)

        # Keep last 1000 logs
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all dashboard data."""
        return {
            "metrics": self.collector.get_summary(),
            "health": self.collector.get_health_status(),
            "logs": self.logs[-50:],  # Last 50 logs
        }

    def get_crawl_stats(self) -> Dict[str, Any]:
        """Get crawling statistics."""
        return {
            "total": self.collector.metrics.total_pages_crawled,
            "successful": self.collector.metrics.successful_crawls,
            "failed": self.collector.metrics.failed_crawls,
            "success_rate": (
                self.collector.metrics.successful_crawls / 
                self.collector.metrics.total_pages_crawled * 100
                if self.collector.metrics.total_pages_crawled > 0 else 0
            ),
            "by_domain": self.collector.metrics.pages_by_domain,
            "recent_errors": self.collector.metrics.crawl_errors[-5:],
        }

    def get_chunk_stats(self) -> Dict[str, Any]:
        """Get chunking statistics."""
        return {
            "total": self.collector.metrics.total_chunks,
            "avg_size_bytes": self.collector.metrics.avg_chunk_size,
            "min_size": self.collector.metrics.min_chunk_size,
            "max_size": self.collector.metrics.max_chunk_size,
            "by_type": self.collector.metrics.chunks_by_type,
        }

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        return {
            "total": self.collector.metrics.total_embeddings,
            "successful": self.collector.metrics.successful_embeddings,
            "failed": self.collector.metrics.failed_embeddings,
            "success_rate": (
                self.collector.metrics.successful_embeddings / 
                self.collector.metrics.total_embeddings * 100
                if self.collector.metrics.total_embeddings > 0 else 0
            ),
            "avg_latency_ms": self.collector.metrics.avg_embedding_latency_ms,
            "recent_errors": self.collector.metrics.embedding_errors[-5:],
        }

    def get_query_stats(self) -> Dict[str, Any]:
        """Get query statistics."""
        return {
            "total": self.collector.metrics.total_queries,
            "successful": self.collector.metrics.successful_queries,
            "failed": self.collector.metrics.failed_queries,
            "success_rate": (
                self.collector.metrics.successful_queries / 
                self.collector.metrics.total_queries * 100
                if self.collector.metrics.total_queries > 0 else 0
            ),
            "avg_latency_ms": self.collector.metrics.avg_query_latency_ms,
            "by_category": self.collector.metrics.queries_by_category,
            "recent_errors": self.collector.metrics.query_errors[-5:],
        }

    def get_vector_db_stats(self) -> Dict[str, Any]:
        """Get vector database statistics."""
        return {
            "size_mb": self.collector.metrics.vector_db_size_mb,
            "documents": self.collector.metrics.vector_db_documents,
            "collections": self.collector.metrics.vector_db_collections,
            "status": self.collector.metrics.vector_db_status,
        }

    def get_kb_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "total_documents": self.collector.metrics.kb_total_documents,
            "total_size_mb": self.collector.metrics.kb_total_size_mb,
            "by_category": self.collector.metrics.kb_documents_by_category,
            "last_update": self.collector.metrics.kb_last_update,
        }

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        error_types = defaultdict(int)
        for error in self.collector.metrics.system_errors:
            error_types[error['type']] += 1

        return {
            "total_errors": len(self.collector.metrics.system_errors),
            "by_type": dict(error_types),
            "recent": self.collector.metrics.system_errors[-10:],
        }

    def export_dashboard(self, filepath: str) -> None:
        """Export dashboard data to JSON."""
        data = self.get_dashboard_data()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
