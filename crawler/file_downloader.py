"""
File downloader with async support and deduplication.

Downloads files with caching and duplicate prevention.
"""

import hashlib
from typing import Optional, Dict, Any, Set
from pathlib import Path
from datetime import datetime
import json

import aiohttp
import asyncio
from core.logger import get_logger
from core.exceptions import IngestionError

logger = get_logger(__name__)


class FileDownloader:
    """
    Downloads files from URLs with deduplication and caching.
    
    Prevents duplicate downloads using hash-based deduplication.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize the file downloader.
        
        Args:
            cache_dir: Directory to cache downloaded files
        """
        self.cache_dir = cache_dir or Path("knowledge_base/downloads")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.cache_dir / "download_metadata.json"
        self.downloaded_hashes: Set[str] = set()
        self.file_mapping: Dict[str, Dict[str, Any]] = {}
        
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load download metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.file_mapping = data.get("files", {})
                    self.downloaded_hashes = set(data.get("hashes", []))
                
                logger.debug(f"Loaded metadata for {len(self.downloaded_hashes)} files")
        except Exception as e:
            logger.warning(f"Error loading download metadata: {e}")

    def _save_metadata(self) -> None:
        """Save download metadata to file."""
        try:
            data = {
                "files": self.file_mapping,
                "hashes": list(self.downloaded_hashes),
                "last_updated": datetime.utcnow().isoformat(),
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved download metadata")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    async def download(
        self,
        url: str,
        source_page: str,
        timeout: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Download a file from URL.
        
        Args:
            url: File URL
            source_page: Source page URL
            timeout: Download timeout in seconds
            
        Returns:
            Dictionary with download info or None if failed/duplicate
        """
        try:
            logger.info(f"Downloading: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 200:
                        logger.warning(f"Download failed with status {response.status}: {url}")
                        return None
                    
                    # Read file content
                    content = await response.read()
                    
                    # Calculate hash for deduplication
                    file_hash = hashlib.sha256(content).hexdigest()
                    
                    # Check if already downloaded
                    if file_hash in self.downloaded_hashes:
                        logger.debug(f"File already downloaded (duplicate): {url}")
                        return None
                    
                    # Save file
                    file_info = self._save_file(content, url, file_hash, source_page)
                    
                    if file_info:
                        self.downloaded_hashes.add(file_hash)
                        self.file_mapping[file_hash] = file_info
                        self._save_metadata()
                        
                        logger.info(f"Downloaded: {file_info['local_path']}")
                        return file_info
                    
                    return None
        
        except asyncio.TimeoutError:
            logger.warning(f"Download timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None

    def _save_file(
        self,
        content: bytes,
        url: str,
        file_hash: str,
        source_page: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Save downloaded file to disk.
        
        Args:
            content: File content
            url: Source URL
            file_hash: SHA256 hash
            source_page: Source page URL
            
        Returns:
            File info dictionary
        """
        try:
            # Get filename from URL
            filename = url.split('/')[-1].split('?')[0]
            if not filename:
                filename = f"file_{file_hash[:8]}"
            
            # Create type directory
            file_ext = filename.split('.')[-1].lower()
            type_dir = self.cache_dir / file_ext
            type_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = type_dir / filename
            
            # Handle filename collision
            counter = 1
            base_name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            while file_path.exists():
                filename = f"{base_name}_{counter}.{ext}"
                file_path = type_dir / filename
                counter += 1
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            return {
                "url": url,
                "filename": filename,
                "local_path": str(file_path),
                "file_type": file_ext,
                "file_size": len(content),
                "hash": file_hash,
                "source_page": source_page,
                "downloaded_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return None

    async def download_batch(
        self,
        files: list,
        source_page: str,
        max_concurrent: int = 5,
    ) -> list:
        """
        Download multiple files concurrently.
        
        Args:
            files: List of file URLs
            source_page: Source page URL
            max_concurrent: Maximum concurrent downloads
            
        Returns:
            List of download info dictionaries
        """
        try:
            results = []
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def download_with_semaphore(url):
                async with semaphore:
                    return await self.download(url, source_page)
            
            tasks = [download_with_semaphore(file_url) for file_url in files]
            results = await asyncio.gather(*tasks)
            
            # Filter out None results
            return [r for r in results if r is not None]
        
        except Exception as e:
            logger.error(f"Error in batch download: {e}")
            return []

    def is_duplicate(self, content: bytes) -> bool:
        """
        Check if file content was already downloaded.
        
        Args:
            content: File content
            
        Returns:
            True if duplicate
        """
        file_hash = hashlib.sha256(content).hexdigest()
        return file_hash in self.downloaded_hashes

    def get_downloaded_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all downloaded files.
        
        Returns:
            Dictionary of downloaded files
        """
        return self.file_mapping.copy()

    def get_files_by_type(self, file_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get downloaded files by type.
        
        Args:
            file_type: File type (pdf, docx, txt, csv)
            
        Returns:
            Filtered files dictionary
        """
        return {
            k: v for k, v in self.file_mapping.items()
            if v.get("file_type") == file_type.lower()
        }

    def get_files_from_page(self, source_page: str) -> list:
        """
        Get all files downloaded from a specific page.
        
        Args:
            source_page: Source page URL
            
        Returns:
            List of file info dictionaries
        """
        return [
            v for v in self.file_mapping.values()
            if v.get("source_page") == source_page
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get download statistics.
        
        Returns:
            Statistics dictionary
        """
        total_size = sum(
            v.get("file_size", 0) for v in self.file_mapping.values()
        )
        
        by_type = {}
        for file_info in self.file_mapping.values():
            ftype = file_info.get("file_type", "unknown")
            if ftype not in by_type:
                by_type[ftype] = {"count": 0, "total_size": 0}
            by_type[ftype]["count"] += 1
            by_type[ftype]["total_size"] += file_info.get("file_size", 0)
        
        return {
            "total_files": len(self.file_mapping),
            "total_size": total_size,
            "unique_hashes": len(self.downloaded_hashes),
            "by_type": by_type,
        }
