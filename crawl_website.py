"""
CLI script to run the website crawler.

Usage:
    python crawl_website.py <start_url>
"""

import asyncio
import sys
from pathlib import Path

from config import get_settings
from core.logger import setup_logging, get_logger
from crawler.crawl import CrawlerOrchestrator

logger = get_logger(__name__)


async def main(start_url: str) -> int:
    """
    Run the crawler.
    
    Args:
        start_url: Website URL to start crawling from
        
    Returns:
        Exit code
    """
    try:
        settings = get_settings()
        
        # Setup logging
        setup_logging(
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE,
            is_debug=settings.DEBUG,
        )
        
        logger.info("=== College FAQ Chatbot - Website Crawler ===")
        logger.info(f"Start URL: {start_url}")
        logger.info(f"Max Depth: {settings.CRAWL_DEPTH}")
        logger.info(f"Max Pages: {settings.MAX_PAGES}")
        
        # Initialize crawler
        crawler = CrawlerOrchestrator()
        
        # Run crawl
        await crawler.crawl(start_url)
        
        # Print statistics
        stats = crawler.get_statistics()
        logger.info("\n=== Crawl Statistics ===")
        logger.info(f"Total URLs Found: {stats['total_urls_found']}")
        logger.info(f"Total URLs Crawled: {stats['total_urls_crawled']}")
        logger.info(f"Total URLs Failed: {stats['total_urls_failed']}")
        logger.info(f"Pages Saved: {stats['pages_saved']}")
        logger.info(f"Start Time: {stats['start_time']}")
        logger.info(f"End Time: {stats['end_time']}")
        
        # Print failed URLs if any
        if crawler.failed_urls:
            logger.info("\n=== Failed URLs ===")
            for url, error in list(crawler.failed_urls.items())[:10]:
                logger.warning(f"{url}: {error}")
            if len(crawler.failed_urls) > 10:
                logger.warning(f"... and {len(crawler.failed_urls) - 10} more")
        
        # List crawled pages
        pages = crawler.get_crawled_pages()
        logger.info(f"\n=== Crawled Pages ({len(pages)}) ===")
        for page in pages[:10]:
            logger.info(f"  - {page['title']} ({page['url']})")
        if len(pages) > 10:
            logger.info(f"  ... and {len(pages) - 10} more pages")
        
        logger.info("\nCrawl completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Crawler failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawl_website.py <start_url>")
        print("Example: python crawl_website.py https://example.com")
        sys.exit(1)
    
    start_url = sys.argv[1]
    exit_code = asyncio.run(main(start_url))
    sys.exit(exit_code)
