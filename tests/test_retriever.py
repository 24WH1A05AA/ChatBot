"""
Tests for advanced retriever and retrieval pipeline.
"""

import pytest
import numpy as np
from pathlib import Path
from typing import List

from retriever.retriever_advanced import AdvancedRetriever, SearchResult, RetrieverConfig
from retriever.query_encoder import QueryEncoder
from retriever.retrieval_pipeline import RetrievalPipeline, RetrievalResult, RetrievalEvaluator
from vectorstore.vectorstore import VectorStore


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_creates_search_result(self):
        """Test creating search result."""
        result = SearchResult(
            chunk_id="chunk_1",
            text="Sample text",
            metadata={"source_url": "https://example.com", "section": "admissions"},
            similarity_score=0.95,
            rank=1,
        )
        
        assert result.chunk_id == "chunk_1"
        assert result.similarity_score == 0.95
        assert result.rank == 1

    def test_search_result_to_dict(self):
        """Test converting to dict."""
        result = SearchResult(
            chunk_id="c1",
            text="Text",
            metadata={
                "source_url": "https://example.com",
                "section": "admissions",
                "department": "admissions",
                "chunk_title": "Title",
            },
            similarity_score=0.9,
            rank=1,
        )
        
        d = result.to_dict()
        assert d["chunk_id"] == "c1"
        assert d["similarity_score"] == 0.9


class TestRetrieverConfig:
    """Tests for retriever configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = RetrieverConfig()
        
        assert config.similarity_threshold == 0.3
        assert config.top_k == 5
        assert config.enable_duplicate_removal is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = RetrieverConfig(
            similarity_threshold=0.5,
            top_k=10,
            diversity_penalty=0.3,
        )
        
        assert config.similarity_threshold == 0.5
        assert config.top_k == 10
        assert config.diversity_penalty == 0.3


class TestAdvancedRetriever:
    """Tests for advanced retriever."""

    def test_creates_retriever(self, tmp_path):
        """Test creating retriever."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = AdvancedRetriever(vectorstore=vs)
        
        assert retriever.vectorstore is not None
        assert retriever.config is not None

    def test_semantic_search(self, tmp_path):
        """Test semantic search."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        # Add test embeddings
        embeddings = [
            {
                "embedding_id": f"emb_{i}",
                "chunk_id": f"chunk_{i}",
                "document_id": "doc_1",
                "vector": [0.1 + i*0.01] * 1536,
                "chunk_text": f"Content {i}",
                "section": "admissions",
                "department": "admissions",
                "source_url": f"https://example.com/{i}",
            }
            for i in range(5)
        ]
        vs.add_embeddings(embeddings)
        
        retriever = AdvancedRetriever(vectorstore=vs)
        results = retriever.semantic_search([0.1] * 1536, k=3)
        
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)

    def test_top_k_search(self, tmp_path):
        """Test top-K search."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": f"emb_{i}",
                "chunk_id": f"chunk_{i}",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": f"Text {i}",
                "section": "admissions",
                "department": "admissions",
                "source_url": "https://example.com",
            }
            for i in range(10)
        ]
        vs.add_embeddings(embeddings)
        
        retriever = AdvancedRetriever(vectorstore=vs)
        results = retriever.top_k_search([0.1] * 1536, k=5)
        
        assert len(results) <= 5

    def test_filter_by_section(self, tmp_path):
        """Test filtering by section."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = AdvancedRetriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text 1", {"section": "admissions"}, 0.9, 1),
            SearchResult("c2", "Text 2", {"section": "placements"}, 0.8, 2),
            SearchResult("c3", "Text 3", {"section": "admissions"}, 0.7, 3),
        ]
        
        filtered = retriever.filter_by_section(results, "admissions")
        
        assert len(filtered) == 2
        assert all(r.metadata["section"] == "admissions" for r in filtered)

    def test_filter_by_department(self, tmp_path):
        """Test filtering by department."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = AdvancedRetriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text 1", {"department": "cs"}, 0.9, 1),
            SearchResult("c2", "Text 2", {"department": "ec"}, 0.8, 2),
        ]
        
        filtered = retriever.filter_by_department(results, "cs")
        
        assert len(filtered) == 1
        assert filtered[0].metadata["department"] == "cs"

    def test_remove_duplicates(self, tmp_path):
        """Test duplicate removal."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = AdvancedRetriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text 1", {"source_url": "url1"}, 0.9, 1),
            SearchResult("c2", "Text 2", {"source_url": "url1"}, 0.8, 2),
            SearchResult("c3", "Text 3", {"source_url": "url2"}, 0.7, 3),
        ]
        
        unique = retriever.remove_duplicates(results, by="url")
        
        assert len(unique) == 2

    def test_apply_score_threshold(self, tmp_path):
        """Test score threshold filtering."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = AdvancedRetriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text 1", {}, 0.9, 1),
            SearchResult("c2", "Text 2", {}, 0.5, 2),
            SearchResult("c3", "Text 3", {}, 0.2, 3),
        ]
        
        filtered = retriever.apply_score_threshold(results, 0.6)
        
        assert len(filtered) == 1
        assert filtered[0].similarity_score == 0.9

    def test_hybrid_search(self, tmp_path):
        """Test hybrid search."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": f"emb_{i}",
                "chunk_id": f"chunk_{i}",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": f"Text {i}",
                "section": "admissions" if i < 5 else "placements",
                "department": "admissions",
                "source_url": f"https://example.com/{i}",
            }
            for i in range(10)
        ]
        vs.add_embeddings(embeddings)
        
        retriever = AdvancedRetriever(vectorstore=vs)
        results = retriever.hybrid_search(
            [0.1] * 1536,
            k=3,
            section="admissions",
        )
        
        assert len(results) <= 3

    def test_rerank_by_diversity(self, tmp_path):
        """Test diversity reranking."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = AdvancedRetriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text 1", {"source_url": "url1"}, 0.9, 1),
            SearchResult("c2", "Text 2", {"source_url": "url1"}, 0.8, 2),
            SearchResult("c3", "Text 3", {"source_url": "url2"}, 0.7, 3),
        ]
        
        reranked = retriever.rerank_by_diversity(results)
        
        assert len(reranked) == 3

    def test_get_result_stats(self, tmp_path):
        """Test stats generation."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = AdvancedRetriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text 1", {"section": "admissions", "department": "cs"}, 0.9, 1),
            SearchResult("c2", "Text 2", {"section": "admissions", "department": "cs"}, 0.7, 2),
        ]
        
        stats = retriever.get_result_stats(results)
        
        assert stats["total_results"] == 2
        assert stats["avg_similarity"] > 0


class TestQueryEncoder:
    """Tests for query encoder."""

    def test_preprocesses_query(self):
        """Test query preprocessing."""
        encoder = QueryEncoder()
        
        processed = encoder.preprocess_query("  HELLO   WORLD  ")
        
        assert processed == "hello world"

    def test_preprocess_without_lowercase(self):
        """Test preprocessing without lowercase."""
        encoder = QueryEncoder()
        
        processed = encoder.preprocess_query("HELLO", lowercase=False)
        
        assert processed == "HELLO"


class TestRetrievalResult:
    """Tests for retrieval result."""

    def test_creates_retrieval_result(self):
        """Test creating retrieval result."""
        results = [
            SearchResult("c1", "Text", {"url": "url1"}, 0.9, 1),
        ]
        
        retrieval_result = RetrievalResult(
            query="test query",
            results=results,
            retrieval_time_ms=50.0,
        )
        
        assert retrieval_result.query == "test query"
        assert len(retrieval_result.results) == 1

    def test_retrieval_result_to_dict(self):
        """Test converting to dict."""
        results = [
            SearchResult("c1", "Text", {"url": "url1"}, 0.9, 1),
        ]
        
        retrieval_result = RetrievalResult(
            query="test",
            results=results,
            retrieval_time_ms=50.0,
        )
        
        d = retrieval_result.to_dict()
        
        assert d["query"] == "test"
        assert len(d["results"]) == 1


class TestRetrievalEvaluator:
    """Tests for retrieval evaluator."""

    def test_evaluates_result(self):
        """Test evaluating result."""
        results = [
            SearchResult("c1", "Text", {}, 0.9, 1),
            SearchResult("c2", "Text 2", {}, 0.7, 2),
        ]
        
        retrieval_result = RetrievalResult(
            query="test",
            results=results,
            retrieval_time_ms=50.0,
        )
        
        metrics = RetrievalEvaluator.evaluate_result(retrieval_result)
        
        assert metrics["total_results"] == 2
        assert "avg_similarity" in metrics

    def test_batch_evaluate(self):
        """Test batch evaluation."""
        retrieval_results = [
            RetrievalResult(
                query="q1",
                results=[SearchResult("c1", "Text", {}, 0.9, 1)],
                retrieval_time_ms=50.0,
            ),
            RetrievalResult(
                query="q2",
                results=[SearchResult("c2", "Text", {}, 0.8, 1)],
                retrieval_time_ms=60.0,
            ),
        ]
        
        metrics = RetrievalEvaluator.batch_evaluate(retrieval_results)
        
        assert metrics["total_queries"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
