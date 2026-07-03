"""
Tests for vector store and retrieval system.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

import pytest

from vectorstore.vectorstore import VectorStore
from vectorstore.indexing import IndexingOrchestrator, IndexStatistics
from retriever.retriever import Retriever, SearchResult


class TestVectorStore:
    """Tests for vector store."""

    def test_creates_vectorstore(self, tmp_path):
        """Test creating vector store."""
        vs = VectorStore(
            collection_name="test_collection",
            persist_dir=tmp_path,
        )
        
        assert vs.collection is not None
        assert vs.collection_name == "test_collection"

    def test_adds_embeddings(self, tmp_path):
        """Test adding embeddings."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": "emb_1",
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Test text 1",
                "section": "admissions",
                "source_url": "https://example.com/1",
            },
            {
                "embedding_id": "emb_2",
                "chunk_id": "chunk_2",
                "document_id": "doc_1",
                "vector": [0.2] * 1536,
                "chunk_text": "Test text 2",
                "section": "placements",
                "source_url": "https://example.com/2",
            }
        ]
        
        stats = vs.add_embeddings(embeddings)
        
        assert stats["added"] >= 1
        assert stats["total"] == 2

    def test_query_embeddings(self, tmp_path):
        """Test querying embeddings."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        # Add embeddings
        embeddings = [
            {
                "embedding_id": f"emb_{i}",
                "chunk_id": f"chunk_{i}",
                "document_id": "doc_1",
                "vector": [0.1 + i*0.01] * 1536,
                "chunk_text": f"Text {i}",
                "section": "admissions",
                "source_url": "https://example.com/page",
            }
            for i in range(5)
        ]
        vs.add_embeddings(embeddings)
        
        # Query
        query_vec = [0.1] * 1536
        results = vs.query(query_embedding=query_vec, k=3)
        
        assert len(results) <= 3
        assert all("chunk_id" in r for r in results)

    def test_get_by_id(self, tmp_path):
        """Test retrieving by ID."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embedding = {
            "embedding_id": "test_emb",
            "chunk_id": "chunk_1",
            "document_id": "doc_1",
            "vector": [0.1] * 1536,
            "chunk_text": "Test content",
            "section": "admissions",
            "source_url": "https://example.com",
        }
        vs.add_embeddings([embedding])
        
        result = vs.get_by_id("test_emb")
        
        assert result is not None
        assert result["chunk_id"] == "chunk_1"

    def test_delete_embeddings(self, tmp_path):
        """Test deleting embeddings."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": f"emb_{i}",
                "chunk_id": f"chunk_{i}",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": f"Text {i}",
                "section": "admissions",
                "source_url": "https://example.com",
            }
            for i in range(3)
        ]
        vs.add_embeddings(embeddings)
        
        # Delete
        stats = vs.delete(["emb_0", "emb_1"])
        
        assert stats["deleted"] > 0

    def test_metadata_filtering(self, tmp_path):
        """Test metadata filtering."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": "emb_1",
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Admissions info",
                "section": "admissions",
                "source_url": "https://example.com/admissions",
            },
            {
                "embedding_id": "emb_2",
                "chunk_id": "chunk_2",
                "document_id": "doc_1",
                "vector": [0.2] * 1536,
                "chunk_text": "Placement info",
                "section": "placements",
                "source_url": "https://example.com/placements",
            }
        ]
        vs.add_embeddings(embeddings)
        
        # Filter by section
        results = vs.filter_by_metadata({"section": "admissions"})
        
        assert len(results) > 0

    def test_get_statistics(self, tmp_path):
        """Test getting statistics."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": "emb_1",
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Text",
                "section": "admissions",
                "source_url": "https://example.com",
            }
        ]
        vs.add_embeddings(embeddings)
        
        stats = vs.get_statistics()
        
        assert "total_embeddings" in stats
        assert "metadata_fields" in stats

    def test_update_embedding(self, tmp_path):
        """Test updating embedding."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embedding = {
            "embedding_id": "emb_1",
            "chunk_id": "chunk_1",
            "document_id": "doc_1",
            "vector": [0.1] * 1536,
            "chunk_text": "Original text",
            "section": "admissions",
            "source_url": "https://example.com",
        }
        vs.add_embeddings([embedding])
        
        # Update
        updated = {
            **embedding,
            "chunk_text": "Updated text",
            "vector": [0.2] * 1536,
        }
        success = vs.update(updated)
        
        assert success


class TestIndexingOrchestrator:
    """Tests for indexing orchestrator."""

    def test_creates_orchestrator(self, tmp_path):
        """Test creating orchestrator."""
        orch = IndexingOrchestrator(
            collection_name="test",
            vectorstore_dir=tmp_path,
            embeddings_file=tmp_path / "embeddings.json",
        )
        
        assert orch.vectorstore is not None

    def test_incremental_indexing(self, tmp_path):
        """Test incremental indexing."""
        orch = IndexingOrchestrator(
            collection_name="test",
            vectorstore_dir=tmp_path,
            embeddings_file=tmp_path / "embeddings.json",
        )
        
        embeddings = [
            {
                "embedding_id": "emb_1",
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Text 1",
                "section": "admissions",
                "source_url": "https://example.com/1",
            }
        ]
        
        stats = orch.incremental_index(embeddings)
        
        assert stats["indexed"] > 0

    def test_delete_embeddings(self, tmp_path):
        """Test deleting embeddings."""
        orch = IndexingOrchestrator(
            collection_name="test",
            vectorstore_dir=tmp_path,
            embeddings_file=tmp_path / "embeddings.json",
        )
        
        embeddings = [
            {
                "embedding_id": "emb_1",
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Text",
                "section": "admissions",
                "source_url": "https://example.com",
            }
        ]
        orch.incremental_index(embeddings)
        
        # Delete
        stats = orch.delete_embeddings(["emb_1"])
        
        assert stats["total"] > 0

    def test_get_index_statistics(self, tmp_path):
        """Test getting index statistics."""
        orch = IndexingOrchestrator(
            collection_name="test",
            vectorstore_dir=tmp_path,
            embeddings_file=tmp_path / "embeddings.json",
        )
        
        stats = orch.get_index_statistics()
        
        assert "total_embeddings" in stats
        assert "metadata_fields" in stats

    def test_search_by_section(self, tmp_path):
        """Test searching by section."""
        orch = IndexingOrchestrator(
            collection_name="test",
            vectorstore_dir=tmp_path,
            embeddings_file=tmp_path / "embeddings.json",
        )
        
        embeddings = [
            {
                "embedding_id": "emb_1",
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Admissions text",
                "section": "admissions",
                "source_url": "https://example.com",
            }
        ]
        orch.incremental_index(embeddings)
        
        results = orch.filter_by_section("admissions")
        
        assert len(results) > 0


class TestRetriever:
    """Tests for retriever."""

    def test_creates_retriever(self, tmp_path):
        """Test creating retriever."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = Retriever(vectorstore=vs)
        
        assert retriever.vectorstore is not None

    def test_search_results(self, tmp_path):
        """Test search results."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": f"emb_{i}",
                "chunk_id": f"chunk_{i}",
                "document_id": "doc_1",
                "vector": [0.1 + i*0.01] * 1536,
                "chunk_text": f"Content {i}",
                "section": "admissions",
                "source_url": f"https://example.com/{i}",
            }
            for i in range(5)
        ]
        vs.add_embeddings(embeddings)
        
        retriever = Retriever(vectorstore=vs)
        query_vec = [0.1] * 1536
        results = retriever.search(query_vec, k=3)
        
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_with_section_filter(self, tmp_path):
        """Test search with section filter."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": "emb_1",
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Admissions",
                "section": "admissions",
                "source_url": "https://example.com/admissions",
            },
            {
                "embedding_id": "emb_2",
                "chunk_id": "chunk_2",
                "document_id": "doc_1",
                "vector": [0.1] * 1536,
                "chunk_text": "Placements",
                "section": "placements",
                "source_url": "https://example.com/placements",
            }
        ]
        vs.add_embeddings(embeddings)
        
        retriever = Retriever(vectorstore=vs)
        results = retriever.search_by_section([0.1] * 1536, "admissions", k=5)
        
        assert len(results) > 0

    def test_rerank_results(self, tmp_path):
        """Test reranking results."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = Retriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text 1", {"url": "url1"}, 0.9, 1),
            SearchResult("c2", "Text 2", {"url": "url2"}, 0.8, 2),
            SearchResult("c3", "Text 3", {"url": "url1"}, 0.7, 3),
        ]
        
        reranked = retriever.rerank_results(results)
        
        assert len(reranked) == 3
        assert reranked[0].rank >= 1

    def test_get_context(self, tmp_path):
        """Test context generation."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = Retriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Context text", {"source_url": "url1"}, 0.9, 1),
            SearchResult("c2", "More context", {"source_url": "url2"}, 0.8, 2),
        ]
        
        context = retriever.get_context(results)
        
        assert "Context text" in context
        assert "More context" in context

    def test_get_citations(self, tmp_path):
        """Test citation generation."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        retriever = Retriever(vectorstore=vs)
        
        results = [
            SearchResult("c1", "Text", {
                "source_url": "https://example.com/1",
                "section": "admissions",
                "chunk_title": "About Admissions"
            }, 0.9, 1),
        ]
        
        citations = retriever.get_citations(results)
        
        assert len(citations) > 0
        assert citations[0]["url"] == "https://example.com/1"

    def test_batch_search(self, tmp_path):
        """Test batch search."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        
        embeddings = [
            {
                "embedding_id": f"emb_{i}",
                "chunk_id": f"chunk_{i}",
                "document_id": "doc_1",
                "vector": [0.1 + i*0.01] * 1536,
                "chunk_text": f"Text {i}",
                "section": "admissions",
                "source_url": "https://example.com",
            }
            for i in range(5)
        ]
        vs.add_embeddings(embeddings)
        
        retriever = Retriever(vectorstore=vs)
        queries = [[0.1 + i*0.01] * 1536 for i in range(3)]
        
        batch_results = retriever.batch_search(queries, k=2)
        
        assert len(batch_results) == 3


class TestIndexStatistics:
    """Tests for index statistics."""

    def test_calculate_statistics(self):
        """Test statistics calculation."""
        stats = IndexStatistics.calculate(
            total_embeddings=1000,
            indexed=950,
            duplicates=30,
            failed=20,
            indexing_time=100.0,
            file_size_mb=50.0,
            metadata_fields=["section", "source_url", "chunk_title"],
        )
        
        assert stats["total_embeddings"] == 1000
        assert stats["indexed"] == 950
        assert stats["success_rate"] == 95.0
        assert stats["embeddings_per_second"] > 0


class TestSearchResult:
    """Tests for search result model."""

    def test_creates_search_result(self):
        """Test creating search result."""
        result = SearchResult(
            chunk_id="c1",
            text="Sample text",
            metadata={"url": "https://example.com"},
            similarity_score=0.95,
            rank=1,
        )
        
        assert result.chunk_id == "c1"
        assert result.similarity_score == 0.95

    def test_search_result_to_dict(self):
        """Test converting to dict."""
        result = SearchResult(
            chunk_id="c1",
            text="Text",
            metadata={
                "source_url": "https://example.com",
                "section": "admissions",
                "chunk_title": "Title",
            },
            similarity_score=0.9,
            rank=1,
        )
        
        d = result.to_dict()
        
        assert d["chunk_id"] == "c1"
        assert d["source_url"] == "https://example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
