"""
Page cleaner orchestrator for processing crawled content.

Coordinates cleaning, formatting, and storage of cleaned pages.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from crawler.cleaner import ContentCleaner, HTMLCleaner
from crawler.formatter import MarkdownFormatter
from core.logger import get_logger
from core.exceptions import IngestionError

logger = get_logger(__name__)


class PageCleaner:
    """
    Orchestrates page cleaning process.
    
    Loads raw pages, cleans content, formats to markdown,
    generates metadata, and stores output.
    """

    def __init__(
        self,
        raw_dir: Optional[Path] = None,
        cleaned_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize page cleaner.
        
        Args:
            raw_dir: Directory with raw crawled pages
            cleaned_dir: Directory to store cleaned pages
        """
        self.raw_dir = raw_dir or Path("knowledge_base/raw")
        self.cleaned_dir = cleaned_dir or Path("knowledge_base/cleaned")
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)
        
        self.html_cleaner = HTMLCleaner()
        self.content_cleaner = ContentCleaner()
        self.formatter = MarkdownFormatter()
        
        self.cleaning_stats = {
            "total_pages": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None,
        }

    def clean_page(self, page_file: Path) -> Optional[Dict[str, Any]]:
        """
        Clean a single page.
        
        Args:
            page_file: Path to JSON page file
            
        Returns:
            Cleaned page data or None if failed
        """
        try:
            # Load raw page
            with open(page_file, "r", encoding="utf-8") as f:
                page_data = json.load(f)
            
            logger.info(f"Cleaning: {page_data.get('url', 'Unknown')}")
            
            # Clean the body content
            body = page_data.get("body", "")
            if body:
                body = self.content_cleaner.clean(body)
                page_data["body"] = body
            
            # Detect and remove duplicate paragraphs
            if body:
                paragraphs = [p for p in body.split("\n\n") if p.strip()]
                unique_paras = self.content_cleaner.detect_duplicate_paragraphs(paragraphs)
                page_data["body"] = "\n\n".join(unique_paras)
            
            # Format to markdown
            markdown_content = self.formatter.format_page(page_data)
            
            # Validate content
            if not self.content_cleaner.validate_content(markdown_content):
                logger.warning(f"Content validation failed for {page_data.get('url')}")
                self.cleaning_stats["skipped"] += 1
                return None
            
            # Generate cleaned page data
            cleaned_data = {
                "url": page_data.get("url"),
                "title": page_data.get("title"),
                "description": page_data.get("description"),
                "keywords": page_data.get("keywords", []),
                "section": page_data.get("section", "general"),
                "markdown": markdown_content,
                "metadata": self._generate_metadata(page_data, markdown_content),
                "cleaned_at": datetime.utcnow().isoformat(),
                "statistics": self._generate_statistics(markdown_content, page_data),
            }
            
            return cleaned_data
        
        except Exception as e:
            logger.error(f"Error cleaning page {page_file}: {e}")
            self.cleaning_stats["failed"] += 1
            return None

    def save_cleaned_page(
        self,
        cleaned_data: Dict[str, Any],
        original_filename: str,
    ) -> bool:
        """
        Save cleaned page to disk.
        
        Args:
            cleaned_data: Cleaned page data
            original_filename: Original filename
            
        Returns:
            True if saved successfully
        """
        try:
            # Save as JSON
            json_file = self.cleaned_dir / original_filename
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            # Save markdown separately
            md_file = self.cleaned_dir / original_filename.replace(".json", ".md")
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(cleaned_data.get("markdown", ""))
            
            logger.info(f"Saved cleaned page: {json_file}")
            self.cleaning_stats["successful"] += 1
            return True
        
        except Exception as e:
            logger.error(f"Error saving cleaned page: {e}")
            self.cleaning_stats["failed"] += 1
            return False

    def clean_all_pages(self) -> Dict[str, Any]:
        """
        Clean all pages in raw directory.
        
        Returns:
            Statistics dictionary
        """
        try:
            self.cleaning_stats["start_time"] = datetime.utcnow().isoformat()
            logger.info("Starting page cleaning pipeline...")
            
            # Get all JSON files (except progress)
            raw_files = [
                f for f in self.raw_dir.glob("*.json")
                if f.name != "crawl_progress.json"
            ]
            
            self.cleaning_stats["total_pages"] = len(raw_files)
            logger.info(f"Found {len(raw_files)} pages to clean")
            
            # Clean each page
            for page_file in raw_files:
                cleaned_data = self.clean_page(page_file)
                
                if cleaned_data:
                    self.save_cleaned_page(cleaned_data, page_file.name)
            
            self.cleaning_stats["end_time"] = datetime.utcnow().isoformat()
            
            logger.info(
                f"Cleaning complete. "
                f"Successful: {self.cleaning_stats['successful']}, "
                f"Failed: {self.cleaning_stats['failed']}, "
                f"Skipped: {self.cleaning_stats['skipped']}"
            )
            
            return self.cleaning_stats.copy()
        
        except Exception as e:
            logger.error(f"Error in cleaning pipeline: {e}")
            raise IngestionError(f"Cleaning pipeline failed: {str(e)}", cause=e)

    def _generate_metadata(
        self,
        page_data: Dict[str, Any],
        markdown_content: str,
    ) -> Dict[str, Any]:
        """
        Generate metadata for cleaned page.
        
        Args:
            page_data: Original page data
            markdown_content: Formatted markdown
            
        Returns:
            Metadata dictionary
        """
        try:
            # Count various elements
            lines = markdown_content.split("\n")
            headings = len([l for l in lines if l.strip().startswith("#")])
            lists = len([l for l in lines if l.strip().startswith(("-", "1."))])
            tables = len([l for l in lines if "|" in l])
            links = len([l for l in lines if "](" in l])
            
            return {
                "url": page_data.get("url"),
                "title": page_data.get("title"),
                "section": page_data.get("section", "general"),
                "source_metadata": page_data.get("metadata", {}),
                "content_statistics": {
                    "word_count": len(markdown_content.split()),
                    "character_count": len(markdown_content),
                    "line_count": len(lines),
                    "heading_count": headings,
                    "list_count": lists,
                    "table_count": tables,
                    "link_count": links,
                },
                "quality_score": self._calculate_quality_score(markdown_content, page_data),
            }
        
        except Exception as e:
            logger.warning(f"Error generating metadata: {e}")
            return {}

    def _generate_statistics(
        self,
        markdown_content: str,
        page_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate detailed statistics for page.
        
        Args:
            markdown_content: Formatted markdown
            page_data: Original page data
            
        Returns:
            Statistics dictionary
        """
        try:
            lines = markdown_content.split("\n")
            non_empty_lines = [l for l in lines if l.strip()]
            
            # Calculate readability
            paragraphs = [p for p in markdown_content.split("\n\n") if p.strip()]
            avg_para_length = len(non_empty_lines) / max(len(paragraphs), 1)
            
            return {
                "total_lines": len(lines),
                "non_empty_lines": len(non_empty_lines),
                "total_paragraphs": len(paragraphs),
                "avg_paragraph_length": avg_para_length,
                "total_words": len(markdown_content.split()),
                "total_characters": len(markdown_content),
                "preservation_rate": self._calculate_preservation_rate(page_data),
            }
        
        except Exception as e:
            logger.warning(f"Error generating statistics: {e}")
            return {}

    def _calculate_quality_score(
        self,
        markdown_content: str,
        page_data: Dict[str, Any],
    ) -> float:
        """
        Calculate quality score for cleaned page (0-1).
        
        Args:
            markdown_content: Formatted markdown
            page_data: Original page data
            
        Returns:
            Quality score
        """
        try:
            score = 0.0
            
            # Title present
            if page_data.get("title"):
                score += 0.15
            
            # Description present
            if page_data.get("description"):
                score += 0.1
            
            # Keywords present
            if page_data.get("keywords"):
                score += 0.1
            
            # Sufficient content
            if len(markdown_content) > 500:
                score += 0.25
            elif len(markdown_content) > 200:
                score += 0.15
            
            # Has headings
            if "#" in markdown_content:
                score += 0.15
            
            # Has lists
            if "-" in markdown_content or "1." in markdown_content:
                score += 0.1
            
            # Has links
            if "](" in markdown_content:
                score += 0.1
            
            return min(score, 1.0)
        
        except Exception as e:
            logger.warning(f"Error calculating quality: {e}")
            return 0.5

    def _calculate_preservation_rate(self, page_data: Dict[str, Any]) -> float:
        """
        Calculate how much original content was preserved (0-1).
        
        Args:
            page_data: Original page data
            
        Returns:
            Preservation rate
        """
        try:
            original_elements = 0
            preserved_elements = 0
            
            # Check each content type
            if page_data.get("title"):
                original_elements += 1
                preserved_elements += 1
            
            if page_data.get("headings"):
                original_elements += len(page_data["headings"])
                preserved_elements += len(page_data["headings"])
            
            if page_data.get("tables"):
                original_elements += len(page_data["tables"])
                preserved_elements += len(page_data["tables"])
            
            if page_data.get("lists"):
                original_elements += len(page_data["lists"])
                preserved_elements += len(page_data["lists"])
            
            if page_data.get("links"):
                original_elements += len(page_data["links"])
                # Some links might be removed (ads, social media)
                preserved_elements += max(1, len(page_data["links"]) - 2)
            
            if original_elements == 0:
                return 0.5
            
            return min(preserved_elements / original_elements, 1.0)
        
        except Exception as e:
            logger.warning(f"Error calculating preservation: {e}")
            return 0.5

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cleaning statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.cleaning_stats.copy()
