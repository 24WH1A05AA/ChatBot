"""
Scheduled Crawling System

Implements intelligent scheduled crawling with:
- Change detection (new, updated, deleted pages)
- Incremental indexing
- Crawl history tracking
- Automatic ChromaDB updates
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import hashlib
import threading
import time
from collections import defaultdict


class PageChangeType(Enum):
    """Type of page change detected."""
    NEW = "new"
    UPDATED = "updated"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class PageSnapshot:
    """Snapshot of a crawled page."""
    url: str
    title: str
    content: str
    content_hash: str
    last_modified: str
    crawl_timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CrawlHistory:
    """Record of a crawl operation."""
    crawl_id: str
    timestamp: str
    duration_seconds: float
    pages_crawled: int
    pages_new: int
    pages_updated: int
    pages_deleted: int
    pages_unchanged: int
    success: bool
    errors: List[str] = field(default_factory=list)
    changes: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PageChangeDetector:
    """Detects changes in crawled pages."""

    def __init__(self, history_file: str = "page_snapshots.json") -> None:
        """Initialize detector."""
        self.history_file = Path(history_file)
        self.snapshots: Dict[str, PageSnapshot] = self._load_snapshots()

    def _load_snapshots(self) -> Dict[str, PageSnapshot]:
        """Load previous snapshots from file."""
        if not self.history_file.exists():
            return {}

        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return {
                    url: PageSnapshot(**snapshot)
                    for url, snapshot in data.items()
                }
        except Exception as e:
            print(f"Error loading snapshots: {e}")
            return {}

    def _save_snapshots(self) -> None:
        """Save snapshots to file."""
        try:
            with open(self.history_file, 'w') as f:
                data = {url: snap.to_dict() for url, snap in self.snapshots.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving snapshots: {e}")

    def detect_changes(
        self,
        new_pages: Dict[str, Tuple[str, str]],  # url -> (title, content)
    ) -> Dict[str, PageChangeType]:
        """
        Detect changes in pages.

        Args:
            new_pages: Dict of url -> (title, content)

        Returns:
            Dict of url -> change type
        """
        changes = {}

        # New and updated pages
        for url, (title, content) in new_pages.items():
            content_hash = PageSnapshot.compute_hash(content)

            if url not in self.snapshots:
                changes[url] = PageChangeType.NEW
            elif self.snapshots[url].content_hash != content_hash:
                changes[url] = PageChangeType.UPDATED
            else:
                changes[url] = PageChangeType.UNCHANGED

        # Deleted pages (in old snapshots but not in new)
        for url in self.snapshots:
            if url not in new_pages:
                changes[url] = PageChangeType.DELETED

        return changes

    def update_snapshots(
        self,
        new_pages: Dict[str, Tuple[str, str]],
        changes: Dict[str, PageChangeType],
    ) -> None:
        """
        Update snapshots with current page state.

        Args:
            new_pages: Dict of url -> (title, content)
            changes: Dict of url -> change type
        """
        current_time = datetime.utcnow().isoformat()

        # Update existing pages
        for url, (title, content) in new_pages.items():
            if changes[url] != PageChangeType.DELETED:
                content_hash = PageSnapshot.compute_hash(content)
                self.snapshots[url] = PageSnapshot(
                    url=url,
                    title=title,
                    content=content,
                    content_hash=content_hash,
                    last_modified=current_time,
                    crawl_timestamp=current_time,
                )

        # Remove deleted pages
        for url in list(self.snapshots.keys()):
            if url in changes and changes[url] == PageChangeType.DELETED:
                del self.snapshots[url]

        self._save_snapshots()

    def get_changed_pages(
        self,
        new_pages: Dict[str, Tuple[str, str]],
        include_unchanged: bool = False,
    ) -> Dict[str, Tuple[str, str]]:
        """Get only changed pages."""
        changes = self.detect_changes(new_pages)
        changed = {}

        for url, change_type in changes.items():
            if include_unchanged or change_type != PageChangeType.UNCHANGED:
                if url in new_pages:
                    changed[url] = new_pages[url]

        return changed

    def get_change_summary(
        self,
        new_pages: Dict[str, Tuple[str, str]],
    ) -> Dict[str, int]:
        """Get summary of changes."""
        changes = self.detect_changes(new_pages)

        summary = {
            "new": sum(1 for c in changes.values() if c == PageChangeType.NEW),
            "updated": sum(1 for c in changes.values() if c == PageChangeType.UPDATED),
            "deleted": sum(1 for c in changes.values() if c == PageChangeType.DELETED),
            "unchanged": sum(1 for c in changes.values() if c == PageChangeType.UNCHANGED),
        }

        return summary


class CrawlHistoryManager:
    """Manages crawl history and statistics."""

    def __init__(self, history_file: str = "crawl_history.json") -> None:
        """Initialize manager."""
        self.history_file = Path(history_file)
        self.history: List[CrawlHistory] = self._load_history()

    def _load_history(self) -> List[CrawlHistory]:
        """Load history from file."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return [CrawlHistory(**record) for record in data]
        except Exception as e:
            print(f"Error loading history: {e}")
            return []

    def _save_history(self) -> None:
        """Save history to file."""
        try:
            with open(self.history_file, 'w') as f:
                data = [record.to_dict() for record in self.history]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_record(self, record: CrawlHistory) -> None:
        """Add a crawl record."""
        self.history.append(record)
        # Keep last 100 records
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self._save_history()

    def get_last_crawl(self) -> Optional[CrawlHistory]:
        """Get last crawl record."""
        return self.history[-1] if self.history else None

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get statistics summary."""
        if not self.history:
            return {
                "total_crawls": 0,
                "successful_crawls": 0,
                "failed_crawls": 0,
                "total_pages_crawled": 0,
                "total_new_pages": 0,
                "total_updated_pages": 0,
                "total_deleted_pages": 0,
                "avg_duration_seconds": 0,
            }

        successful = [h for h in self.history if h.success]
        failed = [h for h in self.history if not h.success]

        return {
            "total_crawls": len(self.history),
            "successful_crawls": len(successful),
            "failed_crawls": len(failed),
            "total_pages_crawled": sum(h.pages_crawled for h in self.history),
            "total_new_pages": sum(h.pages_new for h in self.history),
            "total_updated_pages": sum(h.pages_updated for h in self.history),
            "total_deleted_pages": sum(h.pages_deleted for h in self.history),
            "avg_duration_seconds": (
                sum(h.duration_seconds for h in self.history) / len(self.history)
                if self.history else 0
            ),
        }

    def get_recent_history(self, limit: int = 10) -> List[CrawlHistory]:
        """Get recent crawl records."""
        return self.history[-limit:]


class ScheduledCrawler:
    """Manages scheduled crawling with change detection."""

    def __init__(
        self,
        crawl_interval_hours: int = 6,
        snapshots_file: str = "page_snapshots.json",
        history_file: str = "crawl_history.json",
    ) -> None:
        """
        Initialize scheduled crawler.

        Args:
            crawl_interval_hours: Hours between crawls
            snapshots_file: File to store page snapshots
            history_file: File to store crawl history
        """
        self.crawl_interval_hours = crawl_interval_hours
        self.change_detector = PageChangeDetector(snapshots_file)
        self.history_manager = CrawlHistoryManager(history_file)
        
        self.is_running = False
        self.last_crawl_time: Optional[datetime] = None
        self.crawl_thread: Optional[threading.Thread] = None
        self.crawl_callback = None

    def set_crawl_callback(self, callback) -> None:
        """
        Set callback function for crawling.

        Callback should accept:
        - pages_to_crawl: Dict[str, Tuple[str, str]]
        - changes: Dict[str, PageChangeType]
        """
        self.crawl_callback = callback

    def should_crawl(self) -> bool:
        """Check if crawl is due."""
        if self.last_crawl_time is None:
            return True

        elapsed = datetime.utcnow() - self.last_crawl_time
        return elapsed >= timedelta(hours=self.crawl_interval_hours)

    def perform_crawl(
        self,
        crawled_pages: Dict[str, Tuple[str, str]],  # url -> (title, content)
    ) -> Tuple[bool, CrawlHistory]:
        """
        Perform a crawl operation with change detection.

        Args:
            crawled_pages: Newly crawled pages

        Returns:
            Tuple of (success, CrawlHistory)
        """
        crawl_start = time.time()
        crawl_id = f"crawl_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Detect changes
            changes = self.change_detector.detect_changes(crawled_pages)
            change_summary = self.change_detector.get_change_summary(crawled_pages)

            # Get changed pages
            changed_pages = self.change_detector.get_changed_pages(crawled_pages)

            # Call crawl callback if set
            if self.crawl_callback:
                self.crawl_callback(
                    pages_to_crawl=changed_pages,
                    changes=changes,
                )

            # Update snapshots
            self.change_detector.update_snapshots(crawled_pages, changes)

            # Record history
            duration = time.time() - crawl_start
            history = CrawlHistory(
                crawl_id=crawl_id,
                timestamp=datetime.utcnow().isoformat(),
                duration_seconds=duration,
                pages_crawled=len(crawled_pages),
                pages_new=change_summary["new"],
                pages_updated=change_summary["updated"],
                pages_deleted=change_summary["deleted"],
                pages_unchanged=change_summary["unchanged"],
                success=True,
                changes=change_summary,
            )

            self.history_manager.add_record(history)
            self.last_crawl_time = datetime.utcnow()

            return True, history

        except Exception as e:
            duration = time.time() - crawl_start
            history = CrawlHistory(
                crawl_id=crawl_id,
                timestamp=datetime.utcnow().isoformat(),
                duration_seconds=duration,
                pages_crawled=0,
                pages_new=0,
                pages_updated=0,
                pages_deleted=0,
                pages_unchanged=0,
                success=False,
                errors=[str(e)],
            )

            self.history_manager.add_record(history)

            return False, history

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        last_crawl = self.history_manager.get_last_crawl()
        next_crawl = None

        if last_crawl:
            last_time = datetime.fromisoformat(last_crawl.timestamp)
            next_crawl = (
                last_time + timedelta(hours=self.crawl_interval_hours)
            ).isoformat()

        return {
            "is_running": self.is_running,
            "crawl_interval_hours": self.crawl_interval_hours,
            "last_crawl": last_crawl.to_dict() if last_crawl else None,
            "next_crawl": next_crawl,
            "should_crawl_now": self.should_crawl(),
            "stats": self.history_manager.get_stats_summary(),
        }

    def start_scheduler(self, crawl_function) -> None:
        """
        Start the scheduler in a background thread.

        Args:
            crawl_function: Function that performs the crawl and returns
                          Dict[str, Tuple[str, str]] (url -> (title, content))
        """
        if self.is_running:
            print("Scheduler is already running")
            return

        self.is_running = True

        def scheduler_loop():
            """Background scheduler loop."""
            while self.is_running:
                if self.should_crawl():
                    try:
                        # Perform crawl
                        crawled_pages = crawl_function()

                        # Process with change detection
                        self.perform_crawl(crawled_pages)

                    except Exception as e:
                        print(f"Crawl error: {e}")

                # Sleep for 1 minute before checking again
                time.sleep(60)

        self.crawl_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.crawl_thread.start()
        print(f"Scheduler started with {self.crawl_interval_hours}-hour interval")

    def stop_scheduler(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        if self.crawl_thread:
            self.crawl_thread.join(timeout=5)
        print("Scheduler stopped")
