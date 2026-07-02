"""
File processing extension for the crawler.

Extends CrawlerOrchestrator to handle file detection and downloads.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from crawler.file_detector import FileDetector
from crawler.file_downloader import FileDownloader
from crawler.file_converter import FileDocumentConverter
from crawler.file_association import FileAssociationTracker
from core.logger import get_logger

logger = get_logger(__name__)


class CrawlerFileExtension:
    """
    Handles file detection, download, and processing for the crawler.
    
    Integrates with CrawlerOrchestrator to add file support.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize the file extension.
        
        Args:
            cache_dir: Directory for cached downloads
            output_dir: Directory for converted documents
        """
        self.cache_dir = cache_dir or Path("knowledge_base/downloads")
        self.output_dir = output_dir or Path("knowledge_base/documents")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.detector = FileDetector()
        self.downloader = FileDownloader(cache_dir=self.cache_dir)
        self.converter = FileDocumentConverter()
        self.tracker = FileAssociationTracker(self.cache_dir)
        
        self.file_stats = {
            "total_detected": 0,
            "total_downloaded": 0,
            "total_failed": 0,
            "total_converted": 0,
            "duplicates_skipped": 0,
        }

    async def process_page_files(
        self,
        page_url: str,
        page_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Process files for a crawled page.
        
        Args:
            page_url: URL of the page
            page_data: Parsed page data with links
            
        Returns:
            List of processed documents
        """
        try:
            logger.info(f"Processing files for: {page_url}")
            
            processed_docs = []
            
            # Detect files in links
            links = page_data.get("links", [])
            detected_files = self.detector.detect_files_in_links(links, page_url)
            
            if not detected_files:
                logger.debug(f"No files detected in {page_url}")
                return []
            
            logger.info(f"Detected {len(detected_files)} files in {page_url}")
            self.file_stats["total_detected"] += len(detected_files)
            
            # Download files
            download_urls = [f["url"] for f in detected_files]
            downloaded = await self.downloader.download_batch(
                download_urls,
                page_url,
                max_concurrent=3,
            )
            
            logger.info(f"Downloaded {len(downloaded)} files from {page_url}")
            self.file_stats["total_downloaded"] += len(downloaded)
            
            # Process each downloaded file
            for file_info in downloaded:
                try:
                    # Convert to markdown
                    doc = self.converter.convert(
                        Path(file_info["local_path"]),
                        file_info["file_type"],
                        file_info,
                    )
                    
                    if doc:
                        # Save document
                        doc_file = self.output_dir / f"{Path(file_info['filename']).stem}.json"
                        with open(doc_file, 'w', encoding='utf-8') as f:
                            json.dump(doc, f, indent=2, ensure_ascii=False)
                        
                        # Track association
                        self.tracker.associate(
                            file_info["hash"],
                            file_info,
                            page_url,
                        )
                        
                        processed_docs.append(doc)
                        self.file_stats["total_converted"] += 1
                        
                        logger.info(f"Processed: {file_info['filename']}")
                
                except Exception as e:
                    logger.error(f"Error processing {file_info.get('filename')}: {e}")
                    self.file_stats["total_failed"] += 1
            
            # Save tracker state
            self.tracker.save()
            
            return processed_docs
        
        except Exception as e:
            logger.error(f"Error processing page files: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get file processing statistics.
        
        Returns:
            Statistics dictionary
        """
        downloader_stats = self.downloader.get_statistics()
        tracker_stats = self.tracker.get_statistics()
        
        return {
            "crawler": self.file_stats.copy(),
            "downloader": downloader_stats,
            "tracker": tracker_stats,
        }

    def get_files_for_page(self, page_url: str) -> List[Dict[str, Any]]:
        """
        Get all downloaded files for a page.
        
        Args:
            page_url: Page URL
            
        Returns:
            List of file information
        """
        file_hashes = self.tracker.get_files_for_page(page_url)
        return [self.tracker.get_file_info(fh) for fh in file_hashes]

    def get_pages_for_file(self, file_hash: str) -> List[str]:
        """
        Get all pages that have a file.
        
        Args:
            file_hash: File hash
            
        Returns:
            List of page URLs
        """
        return self.tracker.get_pages_for_file(file_hash)
