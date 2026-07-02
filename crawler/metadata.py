"""
Metadata extraction and enrichment.

Extracts and enriches metadata from crawled pages
including structure information, dates, and content type.
"""

from typing import Optional
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
from core.logger import get_logger

logger = get_logger(__name__)


class MetadataExtractor:
    """
    Extracts and enriches page metadata.
    
    Handles metadata from HTML meta tags, structured data,
    and content-based inference.
    """

    def __init__(self) -> None:
        """Initialize the metadata extractor."""
        pass

    def extract(self, url: str, html: str, content: str) -> dict:
        """
        Extract metadata from a page.
        
        Args:
            url: Page URL
            html: HTML content
            content: Cleaned content
            
        Returns:
            Dictionary of extracted metadata
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            metadata = {
                "url": url,
                "title": self._extract_title(soup),
                "description": self._extract_description(soup),
                "keywords": self._extract_keywords(soup),
                "breadcrumb": self._extract_breadcrumb(soup, url),
                "section": self.infer_category(url, content),
                "headings": self._extract_heading_hierarchy(soup),
                "og_title": self._extract_og_property(soup, "title"),
                "og_description": self._extract_og_property(soup, "description"),
                "og_image": self._extract_og_property(soup, "image"),
                "author": self._extract_author(soup),
                "published_date": self._extract_published_date(soup),
                "modified_date": self._extract_modified_date(soup),
                "language": self._extract_language(soup),
                "canonical": self._extract_canonical(soup),
                "tables": self._extract_tables(soup),
                "lists": self._extract_lists(soup),
                "images": self._extract_images(soup, url),
                "links": self._extract_links(soup, url),
            }
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {e}")
            return {}

    def extract_open_graph(self, html: str) -> dict:
        """
        Extract Open Graph metadata.
        
        Args:
            html: HTML content
            
        Returns:
            Open Graph metadata dictionary
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            og_data = {}
            
            for meta in soup.find_all("meta", attrs={"property": re.compile(r"^og:")}):
                prop = meta.get("property", "").replace("og:", "")
                content = meta.get("content", "")
                og_data[prop] = content
            
            return og_data
        
        except Exception as e:
            logger.debug(f"Error extracting Open Graph: {e}")
            return {}

    def extract_structured_data(self, html: str) -> list:
        """
        Extract structured data (JSON-LD, microdata).
        
        Args:
            html: HTML content
            
        Returns:
            List of structured data objects
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            structured_data = []
            
            # Extract JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    data = json.loads(script.string)
                    structured_data.append(data)
                except Exception as e:
                    logger.debug(f"Error parsing JSON-LD: {e}")
            
            return structured_data
        
        except Exception as e:
            logger.debug(f"Error extracting structured data: {e}")
            return []

    def infer_category(self, url: str, content: str) -> str:
        """
        Infer page category based on URL and content.
        
        Args:
            url: Page URL
            content: Page content
            
        Returns:
            Inferred category string
        """
        try:
            categories = {
                "admissions": ["admission", "apply", "enrollment", "requirements"],
                "academics": ["course", "program", "curriculum", "academic"],
                "placements": ["placement", "recruitment", "career", "job"],
                "faculty": ["faculty", "staff", "professor", "instructor"],
                "facilities": ["facility", "lab", "library", "hostel", "transport"],
                "news": ["news", "announcement", "press", "blog"],
                "events": ["event", "conference", "seminar", "workshop"],
                "contact": ["contact", "about", "location", "phone"],
            }
            
            # Check URL path
            url_lower = url.lower()
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in url_lower:
                        return category
            
            # Check content
            content_lower = content.lower()
            for category, keywords in categories.items():
                count = sum(content_lower.count(keyword) for keyword in keywords)
                if count > 5:
                    return category
            
            return "general"
        
        except Exception as e:
            logger.debug(f"Error inferring category: {e}")
            return "general"

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
        except Exception:
            return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract description."""
        try:
            meta = soup.find("meta", attrs={"name": "description"})
            if meta:
                return meta.get("content", "")
            return ""
        except Exception:
            return ""

    def _extract_keywords(self, soup: BeautifulSoup) -> list:
        """Extract keywords."""
        try:
            meta = soup.find("meta", attrs={"name": "keywords"})
            if meta:
                keywords = meta.get("content", "")
                return [k.strip() for k in keywords.split(",")]
            return []
        except Exception:
            return []

    def _extract_breadcrumb(self, soup: BeautifulSoup, url: str) -> list:
        """Extract breadcrumb navigation."""
        try:
            breadcrumb = []
            
            # Try to find breadcrumb element
            nav = soup.find("nav", {"role": "navigation"}) or soup.find("ol", class_=re.compile("breadcrumb", re.I))
            if nav:
                for li in nav.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        breadcrumb.append(text)
            
            # Fallback to URL path
            if not breadcrumb:
                parsed = urlparse(url)
                parts = [p for p in parsed.path.split("/") if p]
                breadcrumb = ["Home"] + parts
            
            return breadcrumb
        
        except Exception:
            return []

    def _extract_heading_hierarchy(self, soup: BeautifulSoup) -> list:
        """Extract heading hierarchy."""
        try:
            headings = []
            for level in range(1, 7):
                for h in soup.find_all(f"h{level}"):
                    text = h.get_text(strip=True)
                    if text:
                        headings.append({"level": level, "text": text})
            return headings
        except Exception:
            return []

    def _extract_og_property(self, soup: BeautifulSoup, prop: str) -> str:
        """Extract Open Graph property."""
        try:
            meta = soup.find("meta", attrs={"property": f"og:{prop}"})
            if meta:
                return meta.get("content", "")
            return ""
        except Exception:
            return ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author."""
        try:
            meta = soup.find("meta", attrs={"name": "author"})
            if meta:
                return meta.get("content", "")
            return ""
        except Exception:
            return ""

    def _extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract published date."""
        try:
            for attr in ["published_date", "article:published_time", "datePublished"]:
                meta = soup.find("meta", attrs={"property": attr}) or soup.find("meta", attrs={"name": attr})
                if meta:
                    return meta.get("content", "")
            return ""
        except Exception:
            return ""

    def _extract_modified_date(self, soup: BeautifulSoup) -> str:
        """Extract modified date."""
        try:
            for attr in ["modified_date", "article:modified_time", "dateModified"]:
                meta = soup.find("meta", attrs={"property": attr}) or soup.find("meta", attrs={"name": attr})
                if meta:
                    return meta.get("content", "")
            return ""
        except Exception:
            return ""

    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract language."""
        try:
            html_tag = soup.find("html")
            if html_tag:
                lang = html_tag.get("lang", "")
                if lang:
                    return lang
            
            meta = soup.find("meta", attrs={"http-equiv": "Content-Language"})
            if meta:
                return meta.get("content", "")
            
            return ""
        except Exception:
            return ""

    def _extract_canonical(self, soup: BeautifulSoup) -> str:
        """Extract canonical URL."""
        try:
            link = soup.find("link", attrs={"rel": "canonical"})
            if link:
                return link.get("href", "")
            return ""
        except Exception:
            return ""

    def _extract_tables(self, soup: BeautifulSoup) -> list:
        """Extract tables."""
        try:
            tables = []
            for table in soup.find_all("table"):
                rows = []
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    tables.append({"rows": rows})
            return tables
        except Exception:
            return []

    def _extract_lists(self, soup: BeautifulSoup) -> list:
        """Extract lists."""
        try:
            lists = []
            for ul in soup.find_all("ul"):
                items = [li.get_text(strip=True) for li in ul.find_all("li", recursive=False)]
                if items:
                    lists.append({"type": "ul", "items": items})
            for ol in soup.find_all("ol"):
                items = [li.get_text(strip=True) for li in ol.find_all("li", recursive=False)]
                if items:
                    lists.append({"type": "ol", "items": items})
            return lists
        except Exception:
            return []

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract images."""
        try:
            from urllib.parse import urljoin
            images = []
            for img in soup.find_all("img"):
                src = img.get("src", "").strip()
                if src:
                    if not src.startswith("http"):
                        src = urljoin(base_url, src)
                    images.append({
                        "src": src,
                        "alt": img.get("alt", ""),
                        "title": img.get("title", ""),
                    })
            return images
        except Exception:
            return []

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract links."""
        try:
            from urllib.parse import urljoin
            links = []
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a.get("href", "").strip()
                if href and href not in seen:
                    if not href.startswith("http"):
                        href = urljoin(base_url, href)
                    seen.add(href)
                    links.append({
                        "url": href,
                        "text": a.get_text(strip=True),
                        "title": a.get("title", ""),
                    })
            return links
        except Exception:
            return []
