"""
Tests for admin dashboard.
"""

import pytest
from admin.dashboard import AdminDashboard, AdminMetricsCollector, SystemMetrics


class TestSystemMetrics:
    """Tests for system metrics."""

    def test_creates_metrics(self):
        """Test metrics creation."""
        metrics = SystemMetrics()
        assert metrics is not None
        assert metrics.total_pages_crawled == 0

    def test_to_dict(self):
        """Test metrics to dict conversion."""
        metrics = SystemMetrics()
        metrics.total_pages_crawled = 100
        metrics.successful_crawls = 95
        metrics.failed_crawls = 5

        result = metrics.to_dict()
        
        assert result['crawling']['total_pages'] == 100
        assert result['crawling']['successful'] == 95
        assert result['crawling']['failed'] == 5
        assert result['crawling']['success_rate'] == 95.0


class TestAdminMetricsCollector:
    """Tests for metrics collector."""

    def test_creates_collector(self):
        """Test collector creation."""
        collector = AdminMetricsCollector()
        assert collector is not None

    def test_update_crawling_metrics(self):
        """Test updating crawling metrics."""
        collector = AdminMetricsCollector()
        
        collector.update_crawling_metrics(
            pages_crawled=100,
            successful=95,
            failed=5,
            by_domain={"example.com": 100},
            errors=[{"domain": "example.com", "error": "timeout"}],
        )
        
        assert collector.metrics.total_pages_crawled == 100
        assert collector.metrics.successful_crawls == 95
        assert collector.metrics.failed_crawls == 5

    def test_update_chunking_metrics(self):
        """Test updating chunking metrics."""
        collector = AdminMetricsCollector()
        
        collector.update_chunking_metrics(
            total_chunks=1000,
            sizes=[100, 200, 300],
            by_type={"text": 800, "json": 200},
        )
        
        assert collector.metrics.total_chunks == 1000
        assert collector.metrics.avg_chunk_size == 200.0
        assert collector.metrics.min_chunk_size == 100
        assert collector.metrics.max_chunk_size == 300

    def test_update_embedding_metrics(self):
        """Test updating embedding metrics."""
        collector = AdminMetricsCollector()
        
        collector.update_embedding_metrics(
            total=1000,
            successful=950,
            failed=50,
            latencies=[45.5, 50.2, 48.1],
        )
        
        assert collector.metrics.total_embeddings == 1000
        assert collector.metrics.successful_embeddings == 950
        assert collector.metrics.failed_embeddings == 50
        assert abs(collector.metrics.avg_embedding_latency_ms - 47.93) < 0.1

    def test_update_query_metrics(self):
        """Test updating query metrics."""
        collector = AdminMetricsCollector()
        
        collector.update_query_metrics(
            total=500,
            successful=475,
            failed=25,
            latencies=[350.0, 400.0, 300.0],
            by_category={"admission": 200, "fees": 300},
        )
        
        assert collector.metrics.total_queries == 500
        assert collector.metrics.successful_queries == 475
        assert collector.metrics.failed_queries == 25
        assert collector.metrics.queries_by_category == {"admission": 200, "fees": 300}

    def test_update_vector_db_metrics(self):
        """Test updating vector DB metrics."""
        collector = AdminMetricsCollector()
        
        collector.update_vector_db_metrics(
            size_mb=100.5,
            documents=5000,
            collections=8,
            status="healthy",
        )
        
        assert collector.metrics.vector_db_size_mb == 100.5
        assert collector.metrics.vector_db_documents == 5000
        assert collector.metrics.vector_db_collections == 8
        assert collector.metrics.vector_db_status == "healthy"

    def test_update_kb_metrics(self):
        """Test updating KB metrics."""
        collector = AdminMetricsCollector()
        
        collector.update_kb_metrics(
            total_documents=1000,
            total_size_mb=50.0,
            by_category={"admission": 250, "academics": 750},
        )
        
        assert collector.metrics.kb_total_documents == 1000
        assert collector.metrics.kb_total_size_mb == 50.0
        assert collector.metrics.kb_documents_by_category == {"admission": 250, "academics": 750}

    def test_record_error(self):
        """Test error recording."""
        collector = AdminMetricsCollector()
        
        collector.record_error("crawling", "Timeout error")
        collector.record_error("embedding", "API error")
        
        assert len(collector.metrics.system_errors) == 2
        assert collector.metrics.system_errors[0]['type'] == "crawling"
        assert collector.metrics.system_errors[1]['type'] == "embedding"

    def test_get_health_status(self):
        """Test health status calculation."""
        collector = AdminMetricsCollector()
        
        collector.update_crawling_metrics(100, 95, 5, {})
        collector.update_embedding_metrics(100, 96, 4, [])
        collector.update_query_metrics(100, 90, 10, [], {})
        collector.update_vector_db_metrics(100.0, 1000, 5, "healthy")
        
        health = collector.get_health_status()
        
        assert health["crawling"] == "healthy"
        assert health["embeddings"] == "healthy"
        assert health["queries"] == "warning"  # 90% success rate
        assert health["vector_db"] == "healthy"


class TestAdminDashboard:
    """Tests for admin dashboard."""

    def test_creates_dashboard(self):
        """Test dashboard creation."""
        dashboard = AdminDashboard()
        assert dashboard is not None

    def test_log_event(self):
        """Test event logging."""
        dashboard = AdminDashboard()
        
        dashboard.log_event(
            event_type="crawl_started",
            component="crawler",
            message="Started crawling",
            level="info",
        )
        
        assert len(dashboard.logs) == 1
        assert dashboard.logs[0]['type'] == "crawl_started"
        assert dashboard.logs[0]['component'] == "crawler"

    def test_get_crawl_stats(self):
        """Test crawl stats retrieval."""
        dashboard = AdminDashboard()
        
        dashboard.collector.update_crawling_metrics(
            pages_crawled=100,
            successful=95,
            failed=5,
            by_domain={"example.com": 100},
        )
        
        stats = dashboard.get_crawl_stats()
        
        assert stats['total'] == 100
        assert stats['successful'] == 95
        assert stats['failed'] == 5
        assert stats['success_rate'] == 95.0

    def test_get_chunk_stats(self):
        """Test chunk stats retrieval."""
        dashboard = AdminDashboard()
        
        dashboard.collector.update_chunking_metrics(
            total_chunks=1000,
            sizes=[100, 200, 300],
            by_type={"text": 800, "json": 200},
        )
        
        stats = dashboard.get_chunk_stats()
        
        assert stats['total'] == 1000
        assert stats['avg_size_bytes'] == 200.0

    def test_get_embedding_stats(self):
        """Test embedding stats retrieval."""
        dashboard = AdminDashboard()
        
        dashboard.collector.update_embedding_metrics(
            total=1000,
            successful=950,
            failed=50,
            latencies=[45.5],
        )
        
        stats = dashboard.get_embedding_stats()
        
        assert stats['total'] == 1000
        assert stats['successful'] == 950
        assert stats['failed'] == 50
        assert stats['success_rate'] == 95.0

    def test_get_query_stats(self):
        """Test query stats retrieval."""
        dashboard = AdminDashboard()
        
        dashboard.collector.update_query_metrics(
            total=500,
            successful=475,
            failed=25,
            latencies=[350.0],
            by_category={"admission": 200, "fees": 300},
        )
        
        stats = dashboard.get_query_stats()
        
        assert stats['total'] == 500
        assert stats['successful'] == 475
        assert stats['failed'] == 25

    def test_get_vector_db_stats(self):
        """Test vector DB stats retrieval."""
        dashboard = AdminDashboard()
        
        dashboard.collector.update_vector_db_metrics(
            size_mb=100.5,
            documents=5000,
            collections=8,
            status="healthy",
        )
        
        stats = dashboard.get_vector_db_stats()
        
        assert stats['size_mb'] == 100.5
        assert stats['documents'] == 5000
        assert stats['collections'] == 8
        assert stats['status'] == "healthy"

    def test_get_kb_stats(self):
        """Test KB stats retrieval."""
        dashboard = AdminDashboard()
        
        dashboard.collector.update_kb_metrics(
            total_documents=1000,
            total_size_mb=50.0,
            by_category={"admission": 250, "academics": 750},
        )
        
        stats = dashboard.get_kb_stats()
        
        assert stats['total_documents'] == 1000
        assert stats['total_size_mb'] == 50.0

    def test_get_dashboard_data(self):
        """Test dashboard data retrieval."""
        dashboard = AdminDashboard()
        
        dashboard.log_event("test", "test", "test message")
        dashboard.collector.update_crawling_metrics(100, 95, 5, {})
        
        data = dashboard.get_dashboard_data()
        
        assert 'metrics' in data
        assert 'health' in data
        assert 'logs' in data

    def test_export_dashboard(self, tmp_path):
        """Test dashboard export."""
        dashboard = AdminDashboard()
        
        export_file = tmp_path / "dashboard.json"
        dashboard.export_dashboard(str(export_file))
        
        assert export_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
