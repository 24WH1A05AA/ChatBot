"""
Scheduled ChromaDB Updater

Automatically updates ChromaDB when pages change:
- Add new pages
- Update modified pages
- Delete removed pages
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from scheduler.scheduled_crawler import PageChangeType, ScheduledCrawler
from vectorstore.vectorstore import VectorStore
from ingestion.chunk_processor import ChunkProcessor
from embedding.embedding_generator import EmbeddingGenerator
from core.logger import get_logger

logger = get_logger(__name__)


class ChromaDBUpdater:
    """Automatically updates ChromaDB with crawled page changes."""

    def __init__(
        self,
        vectorstore: VectorStore,
        chunk_processor: ChunkProcessor,
        embedding_generator: EmbeddingGenerator,
        crawl_interval_hours: int = 6,
    ) -> None:
        """
        Initialize ChromaDB updater.

        Args:
            vectorstore: ChromaDB vector store
            chunk_processor: Text chunking processor
            embedding_generator: Embedding generator
            crawl_interval_hours: Hours between scheduled crawls
        """
        self.vectorstore = vectorstore
        self.chunk_processor = chunk_processor
        self.embedding_generator = embedding_generator

        self.scheduler = ScheduledCrawler(
            crawl_interval_hours=crawl_interval_hours,
            snapshots_file="scheduler/page_snapshots.json",
            history_file="scheduler/crawl_history.json",
        )

        # Set callback for changes
        self.scheduler.set_crawl_callback(self._handle_crawl_changes)

        self.update_log: List[Dict[str, Any]] = []

    def _handle_crawl_changes(
        self,
        pages_to_crawl: Dict[str, Tuple[str, str]],
        changes: Dict[str, PageChangeType],
    ) -> None:
        """
        Handle crawl changes and update ChromaDB.

        Args:
            pages_to_crawl: Dict of url -> (title, content) for changed pages
            changes: Dict of url -> change type
        """
        update_log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "new_pages": [],
            "updated_pages": [],
            "deleted_pages": [],
            "errors": [],
        }

        # Process new and updated pages
        for url, (title, content) in pages_to_crawl.items():
            change_type = changes.get(url)

            try:
                if change_type == PageChangeType.NEW:
                    self._add_page_to_chromadb(url, title, content)
                    update_log_entry["new_pages"].append(url)
                    logger.info(f"Added new page to ChromaDB: {url}")

                elif change_type == PageChangeType.UPDATED:
                    self._update_page_in_chromadb(url, title, content)
                    update_log_entry["updated_pages"].append(url)
                    logger.info(f"Updated page in ChromaDB: {url}")

            except Exception as e:
                error_msg = f"Error updating {url}: {str(e)}"
                update_log_entry["errors"].append(error_msg)
                logger.error(error_msg)

        # Process deleted pages
        for url, change_type in changes.items():
            if change_type == PageChangeType.DELETED:
                try:
                    self._delete_page_from_chromadb(url)
                    update_log_entry["deleted_pages"].append(url)
                    logger.info(f"Deleted page from ChromaDB: {url}")

                except Exception as e:
                    error_msg = f"Error deleting {url}: {str(e)}"
                    update_log_entry["errors"].append(error_msg)
                    logger.error(error_msg)

        # Store update log
        self.update_log.append(update_log_entry)
        if len(self.update_log) > 100:
            self.update_log = self.update_log[-100:]

    def _add_page_to_chromadb(self, url: str, title: str, content: str) -> None:
        """Add new page to ChromaDB."""
        # Chunk the content
        chunks = self.chunk_processor.process(
            content=content,
            metadata={
                "url": url,
                "title": title,
                "type": "new",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Generate embeddings
        embeddings = self.embedding_generator.generate_batch(
            texts=[chunk.content for chunk in chunks]
        )

        # Add to ChromaDB
        for chunk, embedding in zip(chunks, embeddings):
            self.vectorstore.add_document(
                document_id=f"{url}_{chunk.chunk_id}",
                content=chunk.content,
                metadata=chunk.metadata,
                embedding=embedding,
            )

    def _update_page_in_chromadb(self, url: str, title: str, content: str) -> None:
        """Update existing page in ChromaDB."""
        # Remove old chunks
        self.vectorstore.delete_by_metadata({"url": url})

        # Add updated chunks
        self._add_page_to_chromadb(url, title, content)

    def _delete_page_from_chromadb(self, url: str) -> None:
        """Delete page from ChromaDB."""
        self.vectorstore.delete_by_metadata({"url": url})

    def get_status(self) -> Dict[str, Any]:
        """Get updater status."""
        return {
            "scheduler": self.scheduler.get_status(),
            "recent_updates": self.update_log[-5:],
            "total_updates": len(self.update_log),
        }

    def get_update_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent update history."""
        return self.update_log[-limit:]

    def export_update_log(self, filepath: str) -> None:
        """Export update log to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.update_log, f, indent=2)


class ScheduledIndexingManager:
    """Manages scheduled indexing with incremental updates."""

    def __init__(
        self,
        vectorstore: VectorStore,
        chunk_processor: ChunkProcessor,
        embedding_generator: EmbeddingGenerator,
        crawl_interval_hours: int = 6,
    ) -> None:
        """Initialize indexing manager."""
        self.chromadb_updater = ChromaDBUpdater(
            vectorstore=vectorstore,
            chunk_processor=chunk_processor,
            embedding_generator=embedding_generator,
            crawl_interval_hours=crawl_interval_hours,
        )

    def start_scheduling(self, crawl_function) -> None:
        """
        Start scheduled crawling and indexing.

        Args:
            crawl_function: Function that returns Dict[str, Tuple[str, str]]
                           (url -> (title, content))
        """
        self.chromadb_updater.scheduler.start_scheduler(crawl_function)
        logger.info("Scheduled indexing manager started")

    def stop_scheduling(self) -> None:
        """Stop scheduled crawling and indexing."""
        self.chromadb_updater.scheduler.stop_scheduler()
        logger.info("Scheduled indexing manager stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get full system status."""
        return {
            "scheduler_status": self.chromadb_updater.scheduler.get_status(),
            "chromadb_updates": self.chromadb_updater.get_status(),
        }

    def perform_manual_crawl(
        self,
        crawled_pages: Dict[str, Tuple[str, str]],
    ) -> Dict[str, Any]:
        """
        Perform a manual crawl and update.

        Args:
            crawled_pages: Dict of url -> (title, content)

        Returns:
            Crawl history record
        """
        success, history = self.chromadb_updater.scheduler.perform_crawl(
            crawled_pages
        )

        return {
            "success": success,
            "crawl_id": history.crawl_id,
            "timestamp": history.timestamp,
            "pages_crawled": history.pages_crawled,
            "pages_new": history.pages_new,
            "pages_updated": history.pages_updated,
            "pages_deleted": history.pages_deleted,
            "duration_seconds": history.duration_seconds,
        }

    def get_change_history(self) -> List[Dict[str, Any]]:
        """Get change detection history."""
        return self.chromadb_updater.scheduler.history_manager.get_recent_history()

    def get_update_log(self) -> List[Dict[str, Any]]:
        """Get ChromaDB update log."""
        return self.chromadb_updater.get_update_history()
