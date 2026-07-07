"""
Main crawler orchestrator using Crawl4AI.

Coordinates website crawling, recursive link discovery,
and content extraction with configuration-driven behavior.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Set, Dict, Any, List
from urllib.parse import urljoin, urlparse
from collections import deque

from crawl4ai import AsyncWebCrawler, CrawlResult
from core.logger import get_logger
from core.exceptions import CrawlerError, ValidationError
from config import get_settings
from crawler.sitemap import SitemapParser
from crawler.parser import HTMLParser
from crawler.cleaner import ContentCleaner
from crawler.metadata import MetadataExtractor
from core.optimization import (
    get_optimization_engine,
    ParallelExecutor,
    RetryQueue,
    RetryPolicy,
    Cache,
    CacheStrategy,
    HealthMonitor,
    HealthCheck,
    HealthStatus,
    Compression,
    cached,
    retry,
    timed,
)

logger = get_logger(__name__)


class CrawlerOrchestrator:
    """
    Orchestrates the web crawling process.
    
    Handles recursive crawling, URL deduplication, and
    content extraction across the website.
    """

    def __init__(self) -> None:
        """Initialize the crawler orchestrator."""
        self.settings = get_settings()
        self.crawled_urls: Set[str] = set()
        self.failed_urls: Dict[str, str] = {}
        self.queue: deque = deque()
        self.domain: Optional[str] = None
        self.base_path: Path = Path(self.settings.PERSIST_DIRECTORY) / "raw"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.html_parser = HTMLParser()
        self.content_cleaner = ContentCleaner()
        self.metadata_extractor = MetadataExtractor()
        self.sitemap_parser = SitemapParser()
        
        self.crawl_stats = {
            "total_urls_found": 0,
            "total_urls_crawled": 0,
            "total_urls_failed": 0,
            "start_time": None,
            "end_time": None,
            "pages_saved": 0,
        }
        
        self.progress_file = self.base_path / "crawl_progress.json"

    def _validate_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ("http", "https"), result.netloc])
        except Exception:
            return False

    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: Full URL
            
        Returns:
            Domain without scheme
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _is_internal_url(self, url: str) -> bool:
        """
        Check if URL is internal (same domain).
        
        Args:
            url: URL to check
            
        Returns:
            True if internal
        """
        if not self.domain:
            return False
        return url.startswith(self.domain)

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL (remove fragments, trailing slashes, etc.).
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        # Remove fragment
        url = url.split("#")[0]
        # Remove trailing slash except for root
        if url.endswith("/") and url != self.domain + "/":
            url = url.rstrip("/")
        return url

    def _load_progress(self) -> None:
        """Load crawl progress from file."""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, "r") as f:
                    data = json.load(f)
                    self.crawled_urls = set(data.get("crawled_urls", []))
                    self.failed_urls = data.get("failed_urls", {})
                    self.crawl_stats = {**self.crawl_stats, **data.get("stats", {})}
                logger.info(
                    f"Loaded progress: {len(self.crawled_urls)} crawled, "
                    f"{len(self.failed_urls)} failed"
                )
        except Exception as e:
            logger.warning(f"Could not load progress: {e}")

    def _save_progress(self) -> None:
        """Save crawl progress to file."""
        try:
            progress_data = {
                "crawled_urls": list(self.crawled_urls),
                "failed_urls": self.failed_urls,
                "stats": self.crawl_stats,
            }
            with open(self.progress_file, "w") as f:
                json.dump(progress_data, f, indent=2)
            logger.debug("Crawl progress saved")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    async def _crawl_page(self, crawler: AsyncWebCrawler, url: str) -> Optional[CrawlResult]:
        """
        Crawl a single page using Crawl4AI.
        
        Args:
            crawler: AsyncWebCrawler instance
            url: URL to crawl
            
        Returns:
            CrawlResult if successful, None otherwise
        """
        try:
            logger.info(f"Crawling: {url}")
            result = await crawler.arun(
                url=url,
                wait_for_images=True,
                screenshot=False,
                cache_mode="bypass",
            )
            
            if result.success:
                logger.debug(f"Successfully crawled: {url}")
                return result
            else:
                error_msg = result.error_message or "Unknown error"
                self.failed_urls[url] = error_msg
                self.crawl_stats["total_urls_failed"] += 1
                logger.warning(f"Failed to crawl {url}: {error_msg}")
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.failed_urls[url] = error_msg
            self.crawl_stats["total_urls_failed"] += 1
            logger.error(f"Error crawling {url}: {error_msg}")
            return None

    def _extract_links(self, html: str, base_url: str) -> Set[str]:
        """
        Extract all internal links from HTML.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Set of extracted URLs
        """
        try:
            links = self.html_parser.extract_links(html, base_url)
            internal_links = set()
            
            for link in links:
                try:
                    normalized = self._normalize_url(link)
                    if (self._is_internal_url(normalized) and 
                        self._validate_url(normalized)):
                        internal_links.add(normalized)
                except Exception as e:
                    logger.debug(f"Error processing link {link}: {e}")
            
            logger.debug(f"Extracted {len(internal_links)} internal links from {base_url}")
            return internal_links
            
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
            return set()

    def _save_page(self, url: str, crawl_result: CrawlResult) -> bool:
        """
        Save crawled page to disk.
        
        Args:
            url: Page URL
            crawl_result: Crawl4AI result
            
        Returns:
            True if saved successfully
        """
        try:
            # Extract and clean content
            html_content = crawl_result.html or ""
            markdown_content = crawl_result.markdown or ""
            
            # Extract metadata
            metadata = self.metadata_extractor.extract(
                url=url,
                html=html_content,
                content=markdown_content,
            )
            
            # Generate filename from URL
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip("/").split("/")
            filename = "_".join(path_parts) if path_parts and path_parts[0] else "index"
            if parsed_url.query:
                filename += "_" + parsed_url.query.replace("=", "_").replace("&", "_")
            
            filename = f"{filename}.json"
            file_path = self.base_path / filename
            
            # Prepare page data
            page_data = {
                "url": url,
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "keywords": metadata.get("keywords", ""),
                "breadcrumb": metadata.get("breadcrumb", []),
                "section": metadata.get("section", ""),
                "headings": metadata.get("headings", []),
                "body": markdown_content,
                "tables": metadata.get("tables", []),
                "lists": metadata.get("lists", []),
                "images": metadata.get("images", []),
                "links": metadata.get("links", []),
                "metadata": {
                    "og_title": metadata.get("og_title"),
                    "og_description": metadata.get("og_description"),
                    "og_image": metadata.get("og_image"),
                    "author": metadata.get("author"),
                    "published_date": metadata.get("published_date"),
                    "modified_date": metadata.get("modified_date"),
                    "language": metadata.get("language"),
                    "canonical": metadata.get("canonical"),
                },
                "crawled_at": datetime.utcnow().isoformat(),
                "status_code": crawl_result.status_code,
            }
            
            # Save to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)
            
            self.crawl_stats["pages_saved"] += 1
            logger.info(f"Saved page to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving page {url}: {e}")
            return False

    async def crawl(self, start_url: str) -> None:
        """
        Start the crawling process.
        
        Args:
            start_url: Initial URL to start crawling from
            
        Raises:
            CrawlerError: If crawling fails
        """
        if not self._validate_url(start_url):
            raise ValidationError(f"Invalid URL: {start_url}")
        
        try:
            self.crawl_stats["start_time"] = datetime.utcnow().isoformat()
            logger.info(f"Starting crawl from: {start_url}")
            
            # Set domain and normalize start URL
            self.domain = self._get_domain(start_url)
            start_url = self._normalize_url(start_url)
            
            # Load progress if resuming
            self._load_progress()
            
            # Discover URLs from sitemap
            sitemap_urls = await self._discover_sitemap_urls()
            logger.info(f"Found {len(sitemap_urls)} URLs from sitemap")
            
            # Initialize queue
            self.queue = deque([start_url])
            self.queue.extend(sitemap_urls)
            
            async with AsyncWebCrawler(verbose=False) as crawler:
                depth = 0
                while self.queue and depth < self.settings.CRAWL_DEPTH:
                    # Process batch of URLs at current depth
                    batch_size = len(self.queue)
                    logger.info(
                        f"Processing depth {depth}, "
                        f"{batch_size} URLs in queue"
                    )
                    
                    for _ in range(batch_size):
                        if not self.queue:
                            break
                        
                        url = self.queue.popleft()
                        
                        # Skip if already crawled
                        if url in self.crawled_urls:
                            logger.debug(f"Skipping already crawled: {url}")
                            continue
                        
                        # Mark as crawled
                        self.crawled_urls.add(url)
                        self.crawl_stats["total_urls_crawled"] += 1
                        
                        # Crawl page
                        result = await self._crawl_page(crawler, url)
                        
                        if result and result.success:
                            # Save page
                            self._save_page(url, result)
                            
                            # Extract links for next depth
                            if depth < self.settings.CRAWL_DEPTH - 1:
                                new_links = self._extract_links(
                                    result.html or "",
                                    url
                                )
                                for link in new_links:
                                    if link not in self.crawled_urls:
                                        self.queue.append(link)
                                        self.crawl_stats["total_urls_found"] += 1
                        
                        # Save progress periodically
                        if len(self.crawled_urls) % 10 == 0:
                            self._save_progress()
                    
                    depth += 1
            
            self.crawl_stats["end_time"] = datetime.utcnow().isoformat()
            self._save_progress()
            
            logger.info(
                f"Crawl completed. "
                f"Crawled: {self.crawl_stats['total_urls_crawled']}, "
                f"Failed: {self.crawl_stats['total_urls_failed']}, "
                f"Saved: {self.crawl_stats['pages_saved']}"
            )
            
        except Exception as e:
            logger.error(f"Crawl failed: {e}", exc_info=True)
            self.crawl_stats["end_time"] = datetime.utcnow().isoformat()
            self._save_progress()
            raise CrawlerError(f"Crawling failed: {str(e)}", cause=e)

    async def _discover_sitemap_urls(self) -> Set[str]:
        """
        Discover URLs from website sitemaps.
        
        Returns:
            Set of URLs from sitemaps
        """
        try:
            logger.info("Discovering sitemaps...")
            sitemap_urls = set()
            
            # Check for sitemap.xml
            potential_sitemaps = [
                urljoin(self.domain, "/sitemap.xml"),
                urljoin(self.domain, "/sitemap_index.xml"),
            ]
            
            for sitemap_url in potential_sitemaps:
                try:
                    urls = self.sitemap_parser.parse(sitemap_url)
                    sitemap_urls.update(urls)
                    logger.info(f"Found {len(urls)} URLs in {sitemap_url}")
                except Exception as e:
                    logger.debug(f"Sitemap not found at {sitemap_url}: {e}")
            
            return sitemap_urls
            
        except Exception as e:
            logger.warning(f"Error discovering sitemaps: {e}")
            return set()

    def get_crawled_pages(self) -> list[dict]:
        """
        Get list of crawled pages.
        
        Returns:
            List of crawled page metadata
        """
        try:
            pages = []
            for json_file in self.base_path.glob("*.json"):
                if json_file.name == "crawl_progress.json":
                    continue
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        page_data = json.load(f)
                        pages.append({
                            "file": json_file.name,
                            "url": page_data.get("url"),
                            "title": page_data.get("title"),
                            "crawled_at": page_data.get("crawled_at"),
                        })
                except Exception as e:
                    logger.warning(f"Error reading {json_file}: {e}")
            
            logger.info(f"Found {len(pages)} crawled pages")
            return sorted(pages, key=lambda x: x.get("crawled_at", ""))
            
        except Exception as e:
            logger.error(f"Error getting crawled pages: {e}")
            return []

    def get_statistics(self) -> dict:
        """
        Get crawl statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.crawl_stats.copy()

    def get_failed_urls(self) -> dict:
        """
        Get list of failed URLs.
        
        Returns:
            Dictionary of failed URLs and errors
        """
        return self.failed_urls.copy()
