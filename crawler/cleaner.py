"""
Content cleaning and normalization.

Cleans HTML-extracted content, removes noise,
normalizes text, and handles special cases.
"""

from typing import Optional, List, Dict, Any
import re
from bs4 import BeautifulSoup, NavigableString
from core.logger import get_logger

logger = get_logger(__name__)


class HTMLCleaner:
    """
    Removes unwanted elements from HTML before parsing.
    
    Removes navigation, footers, ads, scripts, styles, and other noise.
    """

    def __init__(self) -> None:
        """Initialize the HTML cleaner."""
        self.elements_to_remove = [
            'script', 'style', 'noscript', 'meta',
            'nav', 'footer', 'aside', '.navigation',
            '.nav', '.menu', '.navbar', '.sidebar',
            '.advertisement', '.ad', '.ads', '[role="navigation"]',
            '[role="contentinfo"]', '[role="complementary"]',
            '.cookie-banner', '.cookie-notice', '.gdpr',
            '.modal-overlay', '.popup', '.lightbox',
            'iframe[src*="ad"]', 'iframe[src*="facebook"]',
            'iframe[src*="twitter"]', 'iframe[src*="youtube"]',
        ]
        
        self.cleanup_patterns = [
            (r'(?i)cookie\s+(notice|consent|banner)', ''),
            (r'(?i)accept\s+all?\s+cookies?', ''),
            (r'(?i)subscribe\s+to\s+(newsletter|updates)', ''),
            (r'(?i)follow\s+us\s+(on\s+)?(social\s+)?media', ''),
            (r'(?i)©\s*\d{4}.*?(?=\n\n|\Z)', ''),
            (r'(?i)all\s+rights\s+reserved', ''),
            (r'(?i)(terms?|privacy)\s+(of\s+service|policy)', ''),
            (r'(?i)contact\s+us', ''),
        ]

    def clean_html(self, html: str) -> str:
        """
        Remove unwanted elements from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned HTML string
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style tags
            for tag in soup.find_all(['script', 'style', 'noscript']):
                tag.decompose()
            
            # Remove navigation elements
            for selector in ['nav', 'footer', '[role="navigation"]', '[role="contentinfo"]']:
                for tag in soup.select(selector):
                    tag.decompose()
            
            # Remove common ad/banner elements
            for tag in soup.find_all(class_=re.compile(
                r'(ad|advertisement|banner|popup|modal|sidebar|widget)', re.I
            )):
                tag.decompose()
            
            # Remove hidden elements
            for tag in soup.find_all(style=re.compile(r'display\s*:\s*none', re.I)):
                tag.decompose()
            
            return str(soup)
        
        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            return html


class ContentCleaner:
    """
    Cleans and normalizes extracted content.
    
    Removes HTML artifacts, normalizes whitespace,
    handles special characters, and validates content.
    """

    def __init__(self) -> None:
        """Initialize the content cleaner."""
        self.html_cleaner = HTMLCleaner()

    def clean(self, content: str) -> str:
        """
        Clean and normalize content.
        
        Args:
            content: Raw extracted content
            
        Returns:
            Cleaned content string
        """
        try:
            # Normalize whitespace
            content = self.normalize_whitespace(content)
            
            # Remove extra punctuation
            content = re.sub(r"([!?.]){2,}", r"\1", content)
            
            # Clean URLs (already linked in markdown)
            content = re.sub(r"\[([^\]]+)\]\(https?://", r"[\1](", content)
            
            return content.strip()
        
        except Exception as e:
            logger.error(f"Error cleaning content: {e}")
            return content

    def normalize_whitespace(self, content: str) -> str:
        """
        Normalize whitespace and line breaks.
        
        Args:
            content: Content to normalize
            
        Returns:
            Normalized content
        """
        try:
            # Replace multiple newlines (more than 2) with double newline
            content = re.sub(r"\n{3,}", "\n\n", content)
            
            # Replace multiple spaces with single space (per line)
            lines = content.split("\n")
            lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
            
            # Remove empty lines
            lines = [line for line in lines if line.strip()]
            content = "\n".join(lines)
            
            return content.strip()
        
        except Exception as e:
            logger.debug(f"Error normalizing whitespace: {e}")
            return content

    def validate_content(self, content: str) -> bool:
        """
        Validate content quality.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content meets quality thresholds
        """
        try:
            # Content should have minimum length
            if len(content.strip()) < 50:
                return False
            
            # Should have more text than numbers
            text_count = sum(1 for c in content if c.isalpha())
            number_count = sum(1 for c in content if c.isdigit())
            
            if text_count < number_count * 2:
                return False
            
            # Should not be mostly special characters
            special_count = sum(1 for c in content if not c.isalnum() and c not in " \n\t")
            if special_count > len(content) * 0.3:
                return False
            
            return True
        
        except Exception as e:
            logger.debug(f"Error validating content: {e}")
            return True

    def detect_duplicate_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        Detect and remove duplicate paragraphs.
        
        Args:
            paragraphs: List of paragraph strings
            
        Returns:
            List with duplicates removed
        """
        try:
            seen = {}
            unique = []
            
            for para in paragraphs:
                normalized = para.lower().strip()
                if normalized and normalized not in seen:
                    seen[normalized] = True
                    unique.append(para)
            
            logger.debug(f"Removed {len(paragraphs) - len(unique)} duplicate paragraphs")
            return unique
        
        except Exception as e:
            logger.warning(f"Error detecting duplicates: {e}")
            return paragraphs
