"""
File association tracker.

Associates downloaded documents with their source webpages.
"""

from typing import Dict, List, Set, Any
from datetime import datetime
import json
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)


class FileAssociationTracker:
    """
    Tracks associations between downloaded files and source pages.
    
    Maintains bidirectional mapping of files to pages and pages to files.
    """

    def __init__(self, storage_dir: Path) -> None:
        """
        Initialize the association tracker.
        
        Args:
            storage_dir: Directory to store association data
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.storage_file = self.storage_dir / "file_associations.json"
        
        # In-memory maps
        self.file_to_pages: Dict[str, Set[str]] = {}  # file_hash -> set of page URLs
        self.page_to_files: Dict[str, Set[str]] = {}  # page_url -> set of file hashes
        self.file_info: Dict[str, Dict[str, Any]] = {}  # file_hash -> file info
        
        self._load()

    def associate(
        self,
        file_hash: str,
        file_info: Dict[str, Any],
        page_url: str,
    ) -> None:
        """
        Associate a file with a source page.
        
        Args:
            file_hash: File hash (SHA256)
            file_info: File information dictionary
            page_url: Source page URL
        """
        try:
            # Add file to pages mapping
            if file_hash not in self.file_to_pages:
                self.file_to_pages[file_hash] = set()
            self.file_to_pages[file_hash].add(page_url)
            
            # Add page to files mapping
            if page_url not in self.page_to_files:
                self.page_to_files[page_url] = set()
            self.page_to_files[page_url].add(file_hash)
            
            # Store file info
            self.file_info[file_hash] = {
                **file_info,
                "associated_at": datetime.utcnow().isoformat(),
            }
            
            logger.debug(f"Associated {file_hash[:8]} with {page_url}")
        
        except Exception as e:
            logger.error(f"Error associating file: {e}")

    def get_pages_for_file(self, file_hash: str) -> List[str]:
        """
        Get all pages that have this file.
        
        Args:
            file_hash: File hash
            
        Returns:
            List of page URLs
        """
        return list(self.file_to_pages.get(file_hash, set()))

    def get_files_for_page(self, page_url: str) -> List[str]:
        """
        Get all files from a specific page.
        
        Args:
            page_url: Page URL
            
        Returns:
            List of file hashes
        """
        return list(self.page_to_files.get(page_url, set()))

    def get_file_info(self, file_hash: str) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            file_hash: File hash
            
        Returns:
            File information dictionary
        """
        return self.file_info.get(file_hash, {})

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get association statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_unique_files": len(self.file_to_pages),
            "total_pages_with_files": len(self.page_to_files),
            "total_associations": sum(len(v) for v in self.file_to_pages.values()),
            "files_by_page_count": {
                url: len(hashes) for url, hashes in self.page_to_files.items()
            }
        }

    def _load(self) -> None:
        """Load associations from storage."""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                
                # Restore maps
                for file_hash, pages in data.get("file_to_pages", {}).items():
                    self.file_to_pages[file_hash] = set(pages)
                
                for page_url, files in data.get("page_to_files", {}).items():
                    self.page_to_files[page_url] = set(files)
                
                self.file_info = data.get("file_info", {})
                
                logger.debug(f"Loaded {len(self.file_to_pages)} file associations")
        
        except Exception as e:
            logger.warning(f"Error loading associations: {e}")

    def save(self) -> None:
        """Save associations to storage."""
        try:
            data = {
                "file_to_pages": {k: list(v) for k, v in self.file_to_pages.items()},
                "page_to_files": {k: list(v) for k, v in self.page_to_files.items()},
                "file_info": self.file_info,
                "saved_at": datetime.utcnow().isoformat(),
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved file associations")
        
        except Exception as e:
            logger.error(f"Error saving associations: {e}")
