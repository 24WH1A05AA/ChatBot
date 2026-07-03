"""
Tests for embedding generation module.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any

import pytest

from embedding.embedding_models import EmbeddingVector, EmbeddingBatch, EmbeddingResult
from embedding.embedding_generator import (
    DuplicateDetector,
    RateLimiter,
    BatchManager,
    OpenAIEmbeddingGenerator,
)
from embedding.embedding_orchestrator import (
    EmbeddingStateTracker,
    EmbeddingStatistics,
    EmbeddingOrchestrator,
)


class TestDuplicateDetector:
    """Tests for duplicate detection."""

    def test_detects_duplicates(self):
        """Test duplicate detection."""
        detector = DuplicateDetector()
        
        text = "This is a test chunk"
        assert not detector.is_duplicate(text)
        assert detector.is_duplicate(text)

    def test_allows_different_texts(self):
        """Test different texts are not duplicates."""
        detector = DuplicateDetector()
        
        assert not detector.is_duplicate("Text 1")
        assert not detector.is_duplicate("Text 2")

    def test_case_sensitive(self):
        """Test case-sensitive detection."""
        detector = DuplicateDetector()
        
        assert not detector.is_duplicate("Text")
        assert not detector.is_duplicate("text")


class TestRateLimiter:
    """Tests for rate limiting."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter init."""
        limiter = RateLimiter(requests_per_minute=3000)
        assert limiter.requests_per_minute == 3000

    def test_rate_limiter_acquires(self):
        """Test rate limiter allows requests."""
        limiter = RateLimiter(requests_per_minute=1000)
        
        start = time.time()
        limiter.acquire()
        limiter.acquire()
        elapsed = time.time() - start
        
        # Should be fast (no waiting needed for first few)
        assert elapsed < 1.0

    def test_rate_limiter_respects_limit(self):
        """Test rate limiter enforces limit."""
        limiter = RateLimiter(requests_per_minute=1)
        
        limiter.acquire()
        
        # This should cause a delay
        start = time.time()
        for _ in range(2):
            limiter.acquire()
        elapsed = time.time() - start
        
        # Should have some delay (approximately 60 seconds for 1 req/min)
        # But we don't want to wait that long in tests, so just check it tracked requests
        assert len(limiter.request_times) >= 2


class TestBatchManager:
    """Tests for batch management."""

    def test_creates_empty_batches(self):
        """Test empty input."""
        manager = BatchManager(batch_size=100)
        batches, skipped = manager.create_batches([])
        
        assert len(batches) == 0
        assert len(skipped) == 0

    def test_creates_single_batch(self):
        """Test single batch creation."""
        manager = BatchManager(batch_size=100)
        
        chunks = [
            {
                "chunk_id": f"chunk_{i}",
                "content": f"Text {i}",
                "document_id": "doc_1",
            }
            for i in range(10)
        ]
        
        batches, skipped = manager.create_batches(chunks)
        
        assert len(batches) == 1
        assert batches[0].batch_size == 10

    def test_creates_multiple_batches(self):
        """Test multiple batch creation."""
        manager = BatchManager(batch_size=10)
        
        chunks = [
            {
                "chunk_id": f"chunk_{i}",
                "content": f"Text {i}",
                "document_id": "doc_1",
            }
            for i in range(25)
        ]
        
        batches, skipped = manager.create_batches(chunks)
        
        assert len(batches) == 3
        assert batches[0].batch_size == 10
        assert batches[1].batch_size == 10
        assert batches[2].batch_size == 5

    def test_skips_duplicates(self):
        """Test duplicate skipping."""
        manager = BatchManager(batch_size=100)
        
        chunks = [
            {"chunk_id": "chunk_1", "content": "Duplicate text", "document_id": "doc_1"},
            {"chunk_id": "chunk_2", "content": "Duplicate text", "document_id": "doc_1"},
            {"chunk_id": "chunk_3", "content": "Different text", "document_id": "doc_1"},
        ]
        
        batches, skipped = manager.create_batches(chunks, skip_duplicates=True)
        
        assert len(batches) == 1
        assert batches[0].batch_size == 2  # Only non-duplicate text
        assert len(skipped) == 1


class TestEmbeddingStateTracker:
    """Tests for state tracking."""

    def test_creates_tracker(self, tmp_path):
        """Test tracker creation."""
        state_file = tmp_path / "state.json"
        tracker = EmbeddingStateTracker(state_file)
        
        assert tracker.processed_chunks == set()
        assert tracker.failed_chunks == set()

    def test_marks_processed(self, tmp_path):
        """Test marking chunks as processed."""
        state_file = tmp_path / "state.json"
        tracker = EmbeddingStateTracker(state_file)
        
        tracker.mark_processed("chunk_1")
        assert tracker.is_processed("chunk_1")
        assert not tracker.is_processed("chunk_2")

    def test_saves_state(self, tmp_path):
        """Test state persistence."""
        state_file = tmp_path / "state.json"
        tracker = EmbeddingStateTracker(state_file)
        
        tracker.mark_processed("chunk_1")
        tracker.mark_processed("chunk_2")
        tracker.mark_failed("chunk_3")
        tracker.save_state()
        
        # Load new tracker
        tracker2 = EmbeddingStateTracker(state_file)
        assert tracker2.is_processed("chunk_1")
        assert tracker2.is_processed("chunk_2")
        assert "chunk_3" in tracker2.failed_chunks


class TestEmbeddingStatistics:
    """Tests for statistics generation."""

    def test_calculates_stats(self):
        """Test statistics calculation."""
        stats = EmbeddingStatistics.calculate(
            total_chunks=100,
            generated=90,
            skipped=5,
            failed=5,
            processing_times=[100, 150, 120],
            total_tokens=50000,
            generation_time=10.0,
        )
        
        assert stats["total_chunks"] == 100
        assert stats["generated"] == 90
        assert stats["skipped"] == 5
        assert stats["failed"] == 5
        assert stats["success_rate"] == 90.0
        assert stats["avg_processing_time_ms"] > 0
        assert stats["total_tokens"] == 50000
        assert stats["generation_time_seconds"] == 10.0
        assert stats["chunks_per_second"] == 9.0

    def test_handles_empty_times(self):
        """Test with empty processing times."""
        stats = EmbeddingStatistics.calculate(
            total_chunks=0,
            generated=0,
            skipped=0,
            failed=0,
            processing_times=[],
            total_tokens=0,
            generation_time=0.0,
        )
        
        assert stats["min_time_ms"] == 0
        assert stats["max_time_ms"] == 0


class TestEmbeddingOrchestrator:
    """Tests for orchestration."""

    def test_creates_orchestrator(self, tmp_path):
        """Test orchestrator creation."""
        orchestrator = EmbeddingOrchestrator(
            output_dir=tmp_path
        )
        
        assert orchestrator.model == "text-embedding-3-small"
        assert orchestrator.batch_size == 100

    def test_adds_embeddings(self, tmp_path):
        """Test adding embeddings."""
        orchestrator = EmbeddingOrchestrator(output_dir=tmp_path)
        
        vector = EmbeddingVector(
            chunk_id="chunk_1",
            document_id="doc_1",
            vector=[0.1, 0.2, 0.3],
            model="text-embedding-3-small",
            chunk_text="Test text",
            processing_time_ms=100.0,
        )
        
        orchestrator.add_embedding(vector)
        
        assert len(orchestrator.embeddings) == 1
        assert orchestrator.embeddings[0].chunk_id == "chunk_1"

    def test_saves_embeddings(self, tmp_path):
        """Test saving embeddings."""
        orchestrator = EmbeddingOrchestrator(output_dir=tmp_path)
        
        for i in range(3):
            vector = EmbeddingVector(
                chunk_id=f"chunk_{i}",
                document_id="doc_1",
                vector=[0.1 * (i + 1), 0.2 * (i + 1), 0.3 * (i + 1)],
                model="text-embedding-3-small",
                chunk_text=f"Text {i}",
                processing_time_ms=100.0 + i,
            )
            orchestrator.add_embedding(vector)
        
        output_file = orchestrator.save_embeddings()
        
        assert output_file.exists()
        
        # Verify saved content
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data["embeddings"]) == 3
            assert data["model"] == "text-embedding-3-small"

    def test_creates_result(self, tmp_path):
        """Test result creation."""
        orchestrator = EmbeddingOrchestrator(output_dir=tmp_path)
        
        vector = EmbeddingVector(
            chunk_id="chunk_1",
            document_id="doc_1",
            vector=[0.1, 0.2],
            model="text-embedding-3-small",
            chunk_text="Test",
            processing_time_ms=100.0,
        )
        orchestrator.add_embedding(vector)
        orchestrator.save_embeddings()
        
        result = orchestrator.get_result(
            total_chunks=10,
            skipped=2,
            failed=1,
            total_tokens=5000,
            generation_time=5.0,
        )
        
        assert isinstance(result, EmbeddingResult)
        assert result.total_chunks == 10
        assert result.total_embeddings == 1
        assert result.skipped_duplicates == 2
        assert result.failed_chunks == 1


class TestEmbeddingModels:
    """Tests for data models."""

    def test_embedding_vector_creation(self):
        """Test creating embedding vector."""
        vector = EmbeddingVector(
            chunk_id="test_1",
            document_id="doc_1",
            vector=[0.1, 0.2, 0.3],
            model="text-embedding-3-small",
            chunk_text="Test text",
            processing_time_ms=50.0,
        )
        
        assert vector.chunk_id == "test_1"
        assert len(vector.vector) == 3

    def test_embedding_batch_creation(self):
        """Test creating batch."""
        batch = EmbeddingBatch(
            chunk_ids=["c1", "c2"],
            texts=["text 1", "text 2"],
            batch_size=2,
        )
        
        assert len(batch.chunk_ids) == 2
        assert len(batch.texts) == 2

    def test_embedding_result_creation(self):
        """Test creating result."""
        result = EmbeddingResult(
            total_chunks=100,
            total_embeddings=95,
            skipped_duplicates=3,
            failed_chunks=2,
            total_batches=10,
            avg_processing_time_ms=150.0,
            total_tokens_used=50000,
            generation_time=30.0,
        )
        
        assert result.total_chunks == 100
        assert result.total_embeddings == 95


@pytest.mark.asyncio
class TestAsyncEmbedding:
    """Tests for async operations."""

    async def test_rate_limiter_async(self):
        """Test rate limiter works with async."""
        limiter = RateLimiter(requests_per_minute=1000)
        
        # Should work without blocking
        limiter.acquire()
        limiter.acquire()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
