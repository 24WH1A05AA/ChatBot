"""
Tests for the crawler module.
"""

import pytest
from pathlib import Path
from urllib.parse import urljoin

from crawler.crawl import CrawlerOrchestrator
from crawler.parser import HTMLParser
from crawler.cleaner import ContentCleaner
from crawler.metadata import MetadataExtractor


class TestCrawlerOrchestrator:
    """Tests for CrawlerOrchestrator."""

    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        crawler = CrawlerOrchestrator()
        
        assert crawler._validate_url("https://example.com")
        assert crawler._validate_url("http://example.com/path")
        assert crawler._validate_url("https://example.com:8080/path?query=1")

    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        crawler = CrawlerOrchestrator()
        
        assert not crawler._validate_url("not a url")
        assert not crawler._validate_url("ftp://example.com")
        assert not crawler._validate_url("")

    def test_get_domain(self):
        """Test domain extraction."""
        crawler = CrawlerOrchestrator()
        
        assert crawler._get_domain("https://example.com/path") == "https://example.com"
        assert crawler._get_domain("http://sub.example.com:8080") == "http://sub.example.com:8080"

    def test_is_internal_url(self):
        """Test internal URL detection."""
        crawler = CrawlerOrchestrator()
        crawler.domain = "https://example.com"
        
        assert crawler._is_internal_url("https://example.com/page")
        assert crawler._is_internal_url("https://example.com/page/subpage")
        assert not crawler._is_internal_url("https://other.com/page")

    def test_normalize_url(self):
        """Test URL normalization."""
        crawler = CrawlerOrchestrator()
        crawler.domain = "https://example.com"
        
        assert crawler._normalize_url("https://example.com/page#section") == "https://example.com/page"
        assert crawler._normalize_url("https://example.com/page/") == "https://example.com/page"
        assert crawler._normalize_url("https://example.com/") == "https://example.com/"


class TestHTMLParser:
    """Tests for HTMLParser."""

    def test_extract_links(self):
        """Test link extraction."""
        parser = HTMLParser()
        
        html = """
        <html>
            <a href="/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
            <a href="https://external.com">External</a>
        </html>
        """
        
        links = parser.extract_links(html, "https://example.com")
        
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://external.com" in links

    def test_extract_metadata(self):
        """Test metadata extraction."""
        parser = HTMLParser()
        
        html = """
        <html>
            <head>
                <meta name="description" content="Test description">
                <meta name="keywords" content="test, example">
            </head>
        </html>
        """
        
        metadata = parser.extract_metadata(html)
        
        assert metadata["description"] == "Test description"
        assert "test" in metadata["keywords"]


class TestContentCleaner:
    """Tests for ContentCleaner."""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        cleaner = ContentCleaner()
        
        content = "Line 1\n\n\nLine 2  with   spaces"
        cleaned = cleaner.normalize_whitespace(content)
        
        assert "\n\n\n" not in cleaned
        assert "   " not in cleaned

    def test_validate_content_valid(self):
        """Test content validation with valid content."""
        cleaner = ContentCleaner()
        
        content = "This is a valid content with enough text to pass validation."
        assert cleaner.validate_content(content)

    def test_validate_content_invalid_short(self):
        """Test content validation with short content."""
        cleaner = ContentCleaner()
        
        content = "Short"
        assert not cleaner.validate_content(content)


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    def test_infer_category_admissions(self):
        """Test category inference for admissions."""
        extractor = MetadataExtractor()
        
        url = "https://example.com/admissions/apply"
        content = "Apply for admission requirements"
        
        category = extractor.infer_category(url, content)
        assert category == "admissions"

    def test_infer_category_academics(self):
        """Test category inference for academics."""
        extractor = MetadataExtractor()
        
        url = "https://example.com/courses"
        content = "Course curriculum and academic programs"
        
        category = extractor.infer_category(url, content)
        assert category == "academics"

    def test_infer_category_default(self):
        """Test category inference default."""
        extractor = MetadataExtractor()
        
        url = "https://example.com/page"
        content = "Some random content"
        
        category = extractor.infer_category(url, content)
        assert category == "general"
