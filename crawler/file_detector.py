"""
File detection and identification module.

Detects and identifies downloadable files (PDF, DOCX, TXT, CSV)
from crawled content.
"""

from typing import Set, List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import re
from core.logger import get_logger

logger = get_logger(__name__)


class FileDetector:
    """
    Detects downloadable files in crawled content.
    
    Identifies and extracts download links from HTML pages.
    """

    def __init__(self) -> None:
        """Initialize the file detector."""
        self.supported_extensions = {
            'pdf', 'docx', 'doc', 'txt', 'csv', 'xlsx', 'xls', 'pptx'
        }
        
        self.mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }

    def detect_files_in_html(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Detect downloadable files in HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of detected file information
        """
        try:
            files = []
            
            # Pattern to match download links
            link_pattern = r'href=["\']((?:[^"\']*?\.(?:pdf|docx?|txt|csv|xlsx?|pptx))(?:\?[^"\']*)?)["\']'
            
            matches = re.finditer(link_pattern, html, re.IGNORECASE)
            
            for match in matches:
                url = match.group(1)
                
                # Convert to absolute URL
                if not url.startswith('http'):
                    url = urljoin(base_url, url)
                
                file_info = self._extract_file_info(url)
                if file_info:
                    files.append(file_info)
            
            logger.debug(f"Detected {len(files)} files in {base_url}")
            return files
        
        except Exception as e:
            logger.warning(f"Error detecting files in {base_url}: {e}")
            return []

    def detect_files_in_links(
        self,
        links: List[Dict[str, str]],
        base_url: str,
    ) -> List[Dict[str, Any]]:
        """
        Detect downloadable files from link objects.
        
        Args:
            links: List of link objects with 'url', 'text', 'title'
            base_url: Base URL for context
            
        Returns:
            List of detected file information
        """
        try:
            files = []
            
            for link in links:
                url = link.get("url", "")
                text = link.get("text", "")
                title = link.get("title", "")
                
                if self._is_downloadable(url):
                    file_info = self._extract_file_info(url)
                    if file_info:
                        file_info["source_text"] = text
                        file_info["source_title"] = title
                        file_info["source_page"] = base_url
                        files.append(file_info)
            
            logger.debug(f"Found {len(files)} downloadable files from links")
            return files
        
        except Exception as e:
            logger.warning(f"Error detecting files from links: {e}")
            return []

    def _is_downloadable(self, url: str) -> bool:
        """
        Check if URL points to a downloadable file.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is a downloadable file
        """
        try:
            # Remove query parameters for checking
            url_path = url.split('?')[0].lower()
            
            # Check extension
            for ext in self.supported_extensions:
                if url_path.endswith(f".{ext}"):
                    return True
            
            return False
        
        except Exception:
            return False

    def _extract_file_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract file information from URL.
        
        Args:
            url: File URL
            
        Returns:
            Dictionary with file information or None
        """
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # Get filename
            filename = path.split('/')[-1]
            if not filename:
                return None
            
            # Get extension
            extension = filename.split('.')[-1].lower()
            
            if extension not in self.supported_extensions:
                return None
            
            return {
                "url": url,
                "filename": filename,
                "extension": extension,
                "mime_type": self.mime_types.get(extension, "application/octet-stream"),
                "size": None,  # Will be populated after download
                "detected_at": None,  # Will be populated during detection
            }
        
        except Exception as e:
            logger.debug(f"Error extracting file info from {url}: {e}")
            return None

    def is_supported_format(self, filename: str) -> bool:
        """
        Check if file format is supported.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if format is supported
        """
        try:
            extension = filename.split('.')[-1].lower()
            return extension in self.supported_extensions
        except Exception:
            return False

    def get_file_type(self, filename: str) -> Optional[str]:
        """
        Get file type from filename.
        
        Args:
            filename: Filename
            
        Returns:
            File type (pdf, docx, txt, csv, etc.) or None
        """
        try:
            extension = filename.split('.')[-1].lower()
            if extension in self.supported_extensions:
                return extension
            return None
        except Exception:
            return None

    def filter_by_type(
        self,
        files: List[Dict[str, Any]],
        file_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Filter files by type.
        
        Args:
            files: List of file info dicts
            file_type: File type to filter (pdf, docx, txt, csv)
            
        Returns:
            Filtered file list
        """
        return [f for f in files if f.get("extension") == file_type.lower()]
