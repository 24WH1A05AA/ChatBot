"""
Tests for file download and processing functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from crawler.file_detector import FileDetector
from crawler.file_extractor import FileExtractor
from crawler.file_converter import FileDocumentConverter
from crawler.file_association import FileAssociationTracker


class TestFileDetector:
    """Tests for FileDetector."""

    def test_is_downloadable_pdf(self):
        """Test PDF detection."""
        detector = FileDetector()
        assert detector._is_downloadable("https://example.com/document.pdf")

    def test_is_downloadable_docx(self):
        """Test DOCX detection."""
        detector = FileDetector()
        assert detector._is_downloadable("https://example.com/file.docx")

    def test_is_downloadable_csv(self):
        """Test CSV detection."""
        detector = FileDetector()
        assert detector._is_downloadable("https://example.com/data.csv")

    def test_is_downloadable_with_query(self):
        """Test detection with query parameters."""
        detector = FileDetector()
        assert detector._is_downloadable("https://example.com/file.pdf?v=1")

    def test_not_downloadable(self):
        """Test non-downloadable URL."""
        detector = FileDetector()
        assert not detector._is_downloadable("https://example.com/page")

    def test_extract_file_info(self):
        """Test file info extraction."""
        detector = FileDetector()
        info = detector._extract_file_info("https://example.com/docs/report.pdf")
        
        assert info is not None
        assert info["filename"] == "report.pdf"
        assert info["extension"] == "pdf"
        assert "mime_type" in info

    def test_detect_files_in_links(self):
        """Test file detection from links."""
        detector = FileDetector()
        links = [
            {"url": "https://example.com/file.pdf", "text": "PDF", "title": ""},
            {"url": "https://example.com/data.csv", "text": "Data", "title": ""},
            {"url": "https://example.com/page", "text": "Page", "title": ""},
        ]
        
        files = detector.detect_files_in_links(links, "https://example.com")
        
        assert len(files) == 2
        assert files[0]["extension"] == "pdf"
        assert files[1]["extension"] == "csv"

    def test_filter_by_type(self):
        """Test filtering files by type."""
        detector = FileDetector()
        files = [
            {"extension": "pdf", "url": "file1.pdf"},
            {"extension": "pdf", "url": "file2.pdf"},
            {"extension": "docx", "url": "file3.docx"},
        ]
        
        pdf_files = detector.filter_by_type(files, "pdf")
        
        assert len(pdf_files) == 2
        assert all(f["extension"] == "pdf" for f in pdf_files)


class TestFileConverter:
    """Tests for FileDocumentConverter."""

    def test_format_size(self):
        """Test file size formatting."""
        converter = FileDocumentConverter()
        
        assert converter._format_size(0) == "0.0 B"
        assert converter._format_size(1024) == "1.0 KB"
        assert converter._format_size(1024 * 1024) == "1.0 MB"

    def test_create_markdown_structure(self):
        """Test markdown creation."""
        converter = FileDocumentConverter()
        
        file_info = {
            "filename": "test.pdf",
            "file_type": "pdf",
            "file_size": 1024,
            "url": "https://example.com/test.pdf",
            "source_page": "https://example.com",
        }
        
        metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "pages": 10,
        }
        
        content = "Test content"
        
        markdown = converter._create_markdown(file_info, content, metadata)
        
        assert "# test.pdf" in markdown
        assert "## Document Information" in markdown
        assert "## Document Metadata" in markdown
        assert "## Content" in markdown
        assert "Test Document" in markdown
        assert "Test Author" in markdown
        assert "Test content" in markdown


class TestFileAssociationTracker:
    """Tests for FileAssociationTracker."""

    def test_associate_file_and_page(self, tmp_path):
        """Test file-page association."""
        tracker = FileAssociationTracker(tmp_path)
        
        file_hash = "abc123"
        file_info = {"filename": "test.pdf", "url": "https://example.com/test.pdf"}
        page_url = "https://example.com/page"
        
        tracker.associate(file_hash, file_info, page_url)
        
        # Check associations
        assert page_url in tracker.get_pages_for_file(file_hash)
        assert file_hash in tracker.get_files_for_page(page_url)

    def test_multiple_associations(self, tmp_path):
        """Test multiple associations."""
        tracker = FileAssociationTracker(tmp_path)
        
        file_hash = "abc123"
        file_info = {"filename": "test.pdf", "url": "https://example.com/test.pdf"}
        
        # Associate with multiple pages
        tracker.associate(file_hash, file_info, "https://example.com/page1")
        tracker.associate(file_hash, file_info, "https://example.com/page2")
        
        pages = tracker.get_pages_for_file(file_hash)
        assert len(pages) == 2

    def test_file_info_storage(self, tmp_path):
        """Test file information storage."""
        tracker = FileAssociationTracker(tmp_path)
        
        file_hash = "abc123"
        file_info = {
            "filename": "test.pdf",
            "url": "https://example.com/test.pdf",
            "file_size": 1024,
        }
        
        tracker.associate(file_hash, file_info, "https://example.com/page")
        
        stored_info = tracker.get_file_info(file_hash)
        assert stored_info["filename"] == "test.pdf"
        assert stored_info["file_size"] == 1024

    def test_get_statistics(self, tmp_path):
        """Test statistics generation."""
        tracker = FileAssociationTracker(tmp_path)
        
        tracker.associate("hash1", {"filename": "f1.pdf"}, "page1")
        tracker.associate("hash2", {"filename": "f2.pdf"}, "page1")
        tracker.associate("hash2", {"filename": "f2.pdf"}, "page2")
        
        stats = tracker.get_statistics()
        
        assert stats["total_unique_files"] == 2
        assert stats["total_pages_with_files"] == 2
        assert stats["total_associations"] == 3

    def test_persistence(self, tmp_path):
        """Test saving and loading."""
        # Save
        tracker1 = FileAssociationTracker(tmp_path)
        tracker1.associate("hash1", {"filename": "test.pdf"}, "page1")
        tracker1.save()
        
        # Load
        tracker2 = FileAssociationTracker(tmp_path)
        
        assert "page1" in tracker2.get_pages_for_file("hash1")
