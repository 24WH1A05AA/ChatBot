"""
Tests for knowledge base generation.
"""

import pytest
from pathlib import Path
from datetime import datetime

from ingestion.kb_metadata import UniqueIDGenerator, MetadataExtractor
from ingestion.kb_models import KnowledgeBaseDocument


class TestUniqueIDGenerator:
    """Tests for unique ID generation."""

    def test_generate_unique_ids(self):
        """Test ID generation."""
        gen = UniqueIDGenerator(prefix="doc")
        
        id1 = gen.generate()
        id2 = gen.generate()
        
        assert id1.startswith("doc-")
        assert id2.startswith("doc-")
        assert id1 != id2

    def test_no_duplicate_ids(self):
        """Test that no duplicates are generated."""
        gen = UniqueIDGenerator()
        ids = set()
        
        for _ in range(100):
            new_id = gen.generate()
            assert new_id not in ids
            ids.add(new_id)

    def test_get_stats(self):
        """Test statistics."""
        gen = UniqueIDGenerator()
        gen.generate()
        gen.generate()
        
        stats = gen.get_stats()
        assert stats["total_ids"] == 2


class TestMetadataExtractor:
    """Tests for metadata extraction."""

    def test_extract_basic_metadata(self):
        """Test basic metadata extraction."""
        extractor = MetadataExtractor()
        
        raw_doc = {
            "title": "Test Document",
            "url": "https://example.edu/admissions",
            "content": "Test content" * 100,
        }
        
        metadata = extractor.extract(raw_doc)
        
        assert "document_id" in metadata
        assert metadata["title"] == "Test Document"
        assert metadata["source_url"] == "https://example.edu/admissions"
        assert metadata["word_count"] > 0

    def test_extract_section(self):
        """Test section extraction."""
        extractor = MetadataExtractor()
        
        doc = {
            "title": "Test",
            "url": "https://example.edu/admissions/requirements",
            "content": "Test",
        }
        
        metadata = extractor.extract(doc)
        assert metadata["section"] == "admissions"

    def test_extract_document_type(self):
        """Test document type extraction."""
        extractor = MetadataExtractor()
        
        doc = {
            "title": "Policy Document",
            "url": "https://example.edu/policy",
            "content": "This policy defines the procedure for student conduct.",
        }
        
        metadata = extractor.extract(doc)
        assert metadata["document_type"] == "policy"

    def test_extract_heading(self):
        """Test heading extraction."""
        extractor = MetadataExtractor()
        
        doc = {
            "title": "Test",
            "url": "https://example.edu",
            "content": "# Main Title\n\nContent here",
            "headings": [{"level": 1, "text": "Main Title"}],
        }
        
        metadata = extractor.extract(doc)
        assert metadata["primary_heading"] == "Main Title"

    def test_content_length_calculation(self):
        """Test content length calculation."""
        extractor = MetadataExtractor()
        
        content = "Test content " * 50
        doc = {
            "title": "Test",
            "url": "https://example.edu",
            "content": content,
        }
        
        metadata = extractor.extract(doc)
        assert metadata["content_length"] == len(content)
        assert metadata["word_count"] == len(content.split())


class TestKnowledgeBaseDocument:
    """Tests for knowledge base document model."""

    def test_create_document(self):
        """Test document creation."""
        doc = KnowledgeBaseDocument(
            title="Test Document",
            content="Test content",
            source_url="https://example.edu/test",
            page_title="Test Page",
        )
        
        assert doc.document_id
        assert doc.title == "Test Document"
        assert doc.source_url == "https://example.edu/test"

    def test_document_defaults(self):
        """Test document default values."""
        doc = KnowledgeBaseDocument(
            title="Test",
            content="Content",
            source_url="https://example.edu",
            page_title="Test",
        )
        
        assert doc.section == "general"
        assert doc.document_type == "content"
        assert doc.language == "en"
        assert len(doc.keywords) == 0
