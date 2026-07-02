"""
HTML parsing and content extraction.

Extracts structured content from HTML pages including
text, links, metadata, and preserves semantic structure.
"""

from typing import Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from core.logger import get_logger

logger = get_logger(__name__)


class HTMLParser:
    """
    Parses HTML content and extracts structured information.
    
    Handles HTML parsing, link extraction, metadata
    extraction, and semantic content preservation.
    """

    def __init__(self) -> None:
        """Initialize the HTML parser."""
        pass

    def parse(self, html: str, url: str) -> dict:
        """
        Parse HTML and extract content.
        
        Args:
            html: HTML content string
            url: Source URL
            
        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            return {
                "url": url,
                "title": self._extract_title(soup),
                "description": self._extract_description(soup),
                "keywords": self._extract_keywords(soup),
                "headings": self._extract_headings(soup),
                "links": self._extract_links(soup, url),
                "images": self._extract_images(soup, url),
                "tables": self._extract_tables(soup),
                "lists": self._extract_lists(soup),
            }
        except Exception as e:
            logger.error(f"Error parsing HTML from {url}: {e}")
            return {}

    def extract_links(self, html: str, base_url: str) -> Set[str]:
        """
        Extract all links from HTML.
        
        Args:
            html: HTML content
            base_url: Base URL for relative link resolution
            
        Returns:
            Set of absolute URLs
        """
        links = set()
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            for link in soup.find_all("a", href=True):
                href = link["href"].strip()
                if not href:
                    continue
                
                # Handle relative URLs
                if href.startswith("/") or not href.startswith("http"):
                    href = urljoin(base_url, href)
                
                # Skip anchor-only links
                if href == base_url + "#":
                    continue
                
                links.add(href)
            
            logger.debug(f"Extracted {len(links)} links from {base_url}")
            return links
        
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
            return set()

    def extract_metadata(self, html: str) -> dict:
        """
        Extract metadata from HTML head.
        
        Args:
            html: HTML content
            
        Returns:
            Dictionary of metadata
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            metadata = {}
            
            # Extract meta tags
            for meta in soup.find_all("meta"):
                name = meta.get("name", "").lower()
                property_name = meta.get("property", "").lower()
                content = meta.get("content", "")
                
                if name == "description":
                    metadata["description"] = content
                elif name == "keywords":
                    metadata["keywords"] = content
                elif name == "author":
                    metadata["author"] = content
                elif name == "og:title" or property_name == "og:title":
                    metadata["og_title"] = content
                elif name == "og:description" or property_name == "og:description":
                    metadata["og_description"] = content
                elif name == "og:image" or property_name == "og:image":
                    metadata["og_image"] = content
                elif name == "robots":
                    metadata["robots"] = content
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        try:
            title_tag = soup.find("title")
            if title_tag:
                return title_tag.get_text(strip=True)
            
            h1 = soup.find("h1")
            if h1:
                return h1.get_text(strip=True)
            
            return ""
        except Exception as e:
            logger.debug(f"Error extracting title: {e}")
            return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description from meta tags."""
        try:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                return meta_desc.get("content", "")
            
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc:
                return og_desc.get("content", "")
            
            return ""
        except Exception as e:
            logger.debug(f"Error extracting description: {e}")
            return ""

    def _extract_keywords(self, soup: BeautifulSoup) -> list:
        """Extract keywords from meta tags."""
        try:
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords:
                keywords_str = meta_keywords.get("content", "")
                return [k.strip() for k in keywords_str.split(",")]
            return []
        except Exception as e:
            logger.debug(f"Error extracting keywords: {e}")
            return []

    def _extract_headings(self, soup: BeautifulSoup) -> list:
        """Extract heading hierarchy."""
        try:
            headings = []
            for level in range(1, 7):
                for heading in soup.find_all(f"h{level}"):
                    text = heading.get_text(strip=True)
                    if text:
                        headings.append({
                            "level": level,
                            "text": text,
                        })
            return headings
        except Exception as e:
            logger.debug(f"Error extracting headings: {e}")
            return []

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract all links with anchors and titles."""
        try:
            links = []
            seen = set()
            
            for link in soup.find_all("a", href=True):
                href = link.get("href", "").strip()
                if not href or href in seen:
                    continue
                
                if not href.startswith("http"):
                    href = urljoin(base_url, href)
                
                seen.add(href)
                links.append({
                    "url": href,
                    "text": link.get_text(strip=True),
                    "title": link.get("title", ""),
                })
            
            return links
        except Exception as e:
            logger.debug(f"Error extracting links: {e}")
            return []

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract images with alt text."""
        try:
            images = []
            for img in soup.find_all("img"):
                src = img.get("src", "").strip()
                if not src:
                    continue
                
                if not src.startswith("http"):
                    src = urljoin(base_url, src)
                
                images.append({
                    "src": src,
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                })
            
            return images
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []

    def _extract_tables(self, soup: BeautifulSoup) -> list:
        """Extract tables as structured data."""
        try:
            tables = []
            for table in soup.find_all("table"):
                rows = []
                for tr in table.find_all("tr"):
                    cells = []
                    for cell in tr.find_all(["td", "th"]):
                        cells.append(cell.get_text(strip=True))
                    if cells:
                        rows.append(cells)
                
                if rows:
                    tables.append({
                        "rows": rows,
                        "title": table.get("title", ""),
                    })
            
            return tables
        except Exception as e:
            logger.debug(f"Error extracting tables: {e}")
            return []

    def _extract_lists(self, soup: BeautifulSoup) -> list:
        """Extract lists."""
        try:
            lists = []
            
            for ul in soup.find_all("ul"):
                items = [li.get_text(strip=True) for li in ul.find_all("li", recursive=False)]
                if items:
                    lists.append({"type": "unordered", "items": items})
            
            for ol in soup.find_all("ol"):
                items = [li.get_text(strip=True) for li in ol.find_all("li", recursive=False)]
                if items:
                    lists.append({"type": "ordered", "items": items})
            
            return lists
        except Exception as e:
            logger.debug(f"Error extracting lists: {e}")
            return []
