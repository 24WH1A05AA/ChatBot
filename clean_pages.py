"""
CLI script to run the content cleaning pipeline.

Usage:
    python clean_pages.py
    python clean_pages.py --raw-dir ./knowledge_base/raw --output-dir ./knowledge_base/cleaned
"""

import sys
import argparse
from pathlib import Path

from config import get_settings
from core.logger import setup_logging, get_logger
from crawler.page_cleaner import PageCleaner

logger = get_logger(__name__)


def main(args: argparse.Namespace) -> int:
    """
    Run the content cleaning pipeline.
    
    Args:
        args: Command-line arguments
        
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
        
        logger.info("=== Content Cleaning Pipeline ===")
        
        # Determine directories
        raw_dir = Path(args.raw_dir) if args.raw_dir else Path(settings.PERSIST_DIRECTORY) / "raw"
        cleaned_dir = Path(args.output_dir) if args.output_dir else Path(settings.PERSIST_DIRECTORY) / "cleaned"
        
        logger.info(f"Raw content directory: {raw_dir}")
        logger.info(f"Output directory: {cleaned_dir}")
        
        # Verify raw directory exists
        if not raw_dir.exists():
            logger.error(f"Raw directory not found: {raw_dir}")
            return 1
        
        # Initialize cleaner
        cleaner = PageCleaner(raw_dir=raw_dir, cleaned_dir=cleaned_dir)
        
        # Run cleaning pipeline
        stats = cleaner.clean_all_pages()
        
        # Print statistics
        logger.info("\n=== Cleaning Statistics ===")
        logger.info(f"Total Pages: {stats['total_pages']}")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Skipped: {stats['skipped']}")
        logger.info(f"Start Time: {stats['start_time']}")
        logger.info(f"End Time: {stats['end_time']}")
        
        # Success rate
        if stats['total_pages'] > 0:
            success_rate = (stats['successful'] / stats['total_pages']) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("\nCleaning pipeline completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean crawled content and convert to markdown"
    )
    
    parser.add_argument(
        "--raw-dir",
        type=str,
        help="Directory with raw crawled pages (default: knowledge_base/raw)",
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to store cleaned pages (default: knowledge_base/cleaned)",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    exit_code = main(args)
    sys.exit(exit_code)
