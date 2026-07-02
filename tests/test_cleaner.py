"""
Tests for the content cleaning pipeline.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from crawler.cleaner import ContentCleaner, HTMLCleaner
from crawler.formatter import (
    MarkdownFormatter, HeadingNormalizer, TableConverter,
    ListConverter, LinkConverter, ImageConverter
)
from crawler.page_cleaner import PageCleaner


class TestHTMLCleaner:
    """Tests for HTMLCleaner."""

    def test_clean_removes_scripts(self):
        """Test removal of script tags."""
        cleaner = HTMLCleaner()
        html = "<html><script>alert('hi');</script><p>Content</p></html>"
        cleaned = cleaner.clean_html(html)
        assert "<script>" not in cleaned
        assert "Content" in cleaned

    def test_clean_removes_navigation(self):
        """Test removal of navigation elements."""
        cleaner = HTMLCleaner()
        html = "<html><nav>Menu</nav><p>Content</p></html>"
        cleaned = cleaner.clean_html(html)
        assert "<nav>" not in cleaned
        assert "Content" in cleaned


class TestContentCleaner:
    """Tests for ContentCleaner."""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        cleaner = ContentCleaner()
        content = "Line 1\n\n\nLine 2  with   spaces"
        normalized = cleaner.normalize_whitespace(content)
        assert "\n\n\n" not in normalized
        assert "   " not in normalized

    def test_validate_content_valid(self):
        """Test content validation with valid content."""
        cleaner = ContentCleaner()
        content = "This is a valid content with enough text to pass validation."
        assert cleaner.validate_content(content)

    def test_validate_content_too_short(self):
        """Test content validation with short content."""
        cleaner = ContentCleaner()
        content = "Short"
        assert not cleaner.validate_content(content)

    def test_detect_duplicate_paragraphs(self):
        """Test duplicate paragraph detection."""
        cleaner = ContentCleaner()
        paragraphs = [
            "This is a paragraph",
            "Another paragraph",
            "This is a paragraph",  # Duplicate
        ]
        unique = cleaner.detect_duplicate_paragraphs(paragraphs)
        assert len(unique) == 2


class TestHeadingNormalizer:
    """Tests for HeadingNormalizer."""

    def test_normalize_headings(self):
        """Test heading normalization."""
        normalizer = HeadingNormalizer()
        headings = [
            {"level": 1, "text": "Main Title"},
            {"level": 2, "text": "Section"},
            {"level": 3, "text": "Subsection"},
        ]
        result = normalizer.normalize_headings(headings)
        assert "# Main Title" in result
        assert "## Section" in result
        assert "### Subsection" in result

    def test_heading_level_limit(self):
        """Test heading level clamping to H6."""
        normalizer = HeadingNormalizer()
        headings = [{"level": 10, "text": "Too Deep"}]
        result = normalizer.normalize_headings(headings)
        assert "###### Too Deep" in result


class TestTableConverter:
    """Tests for TableConverter."""

    def test_convert_table(self):
        """Test table conversion to markdown."""
        converter = TableConverter()
        tables = [
            {
                "rows": [
                    ["Header 1", "Header 2"],
                    ["Cell 1", "Cell 2"],
                    ["Cell 3", "Cell 4"],
                ]
            }
        ]
        result = converter.convert_tables(tables)
        assert "|" in result
        assert "---" in result
        assert "Header 1" in result
        assert "Cell 1" in result


class TestListConverter:
    """Tests for ListConverter."""

    def test_convert_unordered_list(self):
        """Test unordered list conversion."""
        converter = ListConverter()
        lists = [
            {
                "type": "ul",
                "items": ["Item 1", "Item 2", "Item 3"]
            }
        ]
        result = converter.convert_lists(lists)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result

    def test_convert_ordered_list(self):
        """Test ordered list conversion."""
        converter = ListConverter()
        lists = [
            {
                "type": "ol",
                "items": ["First", "Second", "Third"]
            }
        ]
        result = converter.convert_lists(lists)
        assert "1. First" in result
        assert "1. Second" in result
        assert "1. Third" in result


class TestLinkConverter:
    """Tests for LinkConverter."""

    def test_convert_links(self):
        """Test link conversion."""
        converter = LinkConverter()
        links = [
            {"url": "https://example.com/page1", "text": "Page 1", "title": "First Page"},
            {"url": "https://example.com/page2", "text": "Page 2", "title": ""},
        ]
        result = converter.convert_links(links)
        assert "[Page 1](https://example.com/page1)" in result
        assert "[Page 2](https://example.com/page2)" in result

    def test_skip_social_media_links(self):
        """Test that social media links are skipped."""
        converter = LinkConverter()
        links = [
            {"url": "https://facebook.com/page", "text": "Facebook", "title": ""},
            {"url": "https://example.com/real", "text": "Real Link", "title": ""},
        ]
        result = converter.convert_links(links)
        assert "facebook.com" not in result
        assert "[Real Link]" in result


class TestImageConverter:
    """Tests for ImageConverter."""

    def test_convert_images(self):
        """Test image conversion."""
        converter = ImageConverter()
        images = [
            {"src": "image1.jpg", "alt": "Image 1", "title": "Picture 1"},
            {"src": "image2.jpg", "alt": "Image 2", "title": ""},
        ]
        result = converter.convert_images(images)
        assert "![Image 1](image1.jpg" in result
        assert "![Image 2](image2.jpg" in result


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_format_page_with_all_elements(self):
        """Test formatting page with all elements."""
        formatter = MarkdownFormatter()
        page_data = {
            "title": "Test Page",
            "description": "Test Description",
            "keywords": ["tag1", "tag2"],
            "breadcrumb": ["Home", "Section"],
            "body": "# Main Content\n\nParagraph text.",
            "headings": [],
            "tables": [],
            "lists": [],
            "images": [],
            "links": [],
            "metadata": {"author": "Test Author"},
        }
        result = formatter.format_page(page_data)
        assert "# Test Page" in result
        assert "*Test Description*" in result
        assert "tag1" in result
        assert "Main Content" in result

    def test_format_page_markdown_cleanup(self):
        """Test that excessive newlines are cleaned up."""
        formatter = MarkdownFormatter()
        page_data = {
            "title": "Test",
            "body": "Content\n\n\n\nMore content",
            "headings": [],
            "tables": [],
            "lists": [],
            "images": [],
            "links": [],
        }
        result = formatter.format_page(page_data)
        assert "\n\n\n\n" not in result


class TestPageCleaner:
    """Tests for PageCleaner."""

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        cleaner = PageCleaner()
        
        # Page with good quality
        page_data = {
            "title": "Test",
            "description": "Description",
            "keywords": ["tag"],
            "body": "x" * 1000,
        }
        markdown = "# Test\n\n" + "x" * 1000
        score = cleaner._calculate_quality_score(markdown, page_data)
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should be fairly high

    def test_calculate_preservation_rate(self):
        """Test preservation rate calculation."""
        cleaner = PageCleaner()
        
        page_data = {
            "title": "Test",
            "headings": [{"level": 1, "text": "H1"}],
            "tables": [{"rows": [["A", "B"]]}],
            "lists": [{"type": "ul", "items": ["Item"]}],
            "links": [{"url": "url", "text": "link"}],
        }
        rate = cleaner._calculate_preservation_rate(page_data)
        
        assert 0 <= rate <= 1
        assert rate > 0.7  # Should preserve most elements
