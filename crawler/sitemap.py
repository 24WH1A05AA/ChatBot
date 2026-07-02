"""
Sitemap parsing and URL discovery.

Extracts URLs from XML sitemaps and helps optimize
crawling by identifying all pages upfront.
"""

from typing import Set, Optional
import xml.etree.ElementTree as ET
import aiohttp
from core.logger import get_logger

logger = get_logger(__name__)


class SitemapParser:
    """
    Parses XML sitemaps to extract URLs.
    
    Discovers all URLs in a website's sitemap(s),
    supporting nested and index sitemaps.
    """

    def __init__(self) -> None:
        """Initialize the sitemap parser."""
        pass

    async def parse(self, sitemap_url: str) -> Set[str]:
        """
        Parse sitemap and extract URLs.
        
        Args:
            sitemap_url: URL to the sitemap
            
        Returns:
            Set of discovered URLs
        """
        urls = set()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(sitemap_url, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(
                            f"Sitemap returned status {response.status}: {sitemap_url}"
                        )
                        return urls
                    
                    content = await response.text()
                    
                    # Parse XML
                    try:
                        root = ET.fromstring(content)
                        
                        # Handle sitemap index
                        namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                        
                        # Check if this is a sitemap index
                        sitemaps = root.findall("ns:sitemap", namespaces)
                        if sitemaps:
                            logger.info(f"Found sitemap index with {len(sitemaps)} sitemaps")
                            for sitemap in sitemaps:
                                loc = sitemap.find("ns:loc", namespaces)
                                if loc is not None and loc.text:
                                    # Recursively parse nested sitemap
                                    nested_urls = await self.parse(loc.text)
                                    urls.update(nested_urls)
                        
                        # Extract URLs from sitemap
                        else:
                            url_elements = root.findall("ns:url", namespaces)
                            logger.info(f"Found {len(url_elements)} URLs in sitemap")
                            
                            for url_elem in url_elements:
                                loc = url_elem.find("ns:loc", namespaces)
                                if loc is not None and loc.text:
                                    urls.add(loc.text.strip())
                    
                    except ET.ParseError as e:
                        logger.warning(f"Error parsing XML from {sitemap_url}: {e}")
        
        except Exception as e:
            logger.warning(f"Error fetching sitemap {sitemap_url}: {e}")
        
        return urls

    async def find_sitemaps(self, domain: str) -> Set[str]:
        """
        Discover sitemaps for a domain.
        
        Args:
            domain: Domain to search for sitemaps
            
        Returns:
            Set of discovered sitemap URLs
        """
        sitemaps = set()
        
        common_sitemap_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap1.xml",
            "/sitemap-index.xml",
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for path in common_sitemap_paths:
                    sitemap_url = f"{domain}{path}"
                    try:
                        async with session.head(
                            sitemap_url,
                            timeout=5,
                            allow_redirects=True
                        ) as response:
                            if response.status == 200:
                                sitemaps.add(sitemap_url)
                                logger.info(f"Found sitemap: {sitemap_url}")
                    except Exception:
                        pass
        
        except Exception as e:
            logger.warning(f"Error finding sitemaps for {domain}: {e}")
        
        return sitemaps
