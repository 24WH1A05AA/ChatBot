"""
Metadata extraction and enrichment for knowledge base.

Extracts and enriches metadata for each document.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse

from core.logger import get_logger

logger = get_logger(__name__)


class UniqueIDGenerator:
    """
    Generates unique IDs for knowledge base documents.
    
    Creates consistent, trackable IDs for each document.
    """

    def __init__(self, prefix: str = "doc") -> None:
        """
        Initialize ID generator.
        
        Args:
            prefix: Prefix for document IDs
        """
        self.prefix = prefix
        self.counter = 0
        self.used_ids = set()

    def generate(self, source_url: str = "") -> str:
        """
        Generate unique document ID.
        
        Args:
            source_url: Optional source URL for ID derivation
            
        Returns:
            Unique document ID
        """
        try:
            # Always use UUID for uniqueness
            doc_id = f"{self.prefix}-{uuid.uuid4().hex[:12]}"
            
            while doc_id in self.used_ids:
                doc_id = f"{self.prefix}-{uuid.uuid4().hex[:12]}"
            
            self.used_ids.add(doc_id)
            return doc_id
        
        except Exception as e:
            logger.error(f"Error generating ID: {e}")
            return str(uuid.uuid4())

    def get_stats(self) -> Dict[str, Any]:
        """Get ID generation statistics."""
        return {
            "total_ids": len(self.used_ids),
            "prefix": self.prefix,
        }


class MetadataExtractor:
    """
    Extracts and enriches metadata for documents.
    
    Derives metadata from source data and enriches with computed values.
    """

    def __init__(self) -> None:
        """Initialize the metadata extractor."""
        self.id_generator = UniqueIDGenerator()

    def extract(self, raw_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and enrich metadata from raw document.
        
        Args:
            raw_doc: Raw document from loader
            
        Returns:
            Enriched metadata dictionary
        """
        try:
            # Basic fields
            url = raw_doc.get("url", "")
            title = raw_doc.get("title", "Untitled")
            content = self._get_content(raw_doc)
            
            # Generate unique ID
            doc_id = self.id_generator.generate(url)
            
            # Extract metadata
            metadata = {
                "document_id": doc_id,
                "title": title,
                "page_title": raw_doc.get("page_title", title),
                "source_url": url,
                "source_type": self._determine_source_type(raw_doc),
                "section": self._extract_section(raw_doc, url),
                "subsection": raw_doc.get("subsection"),
                "department": self._extract_department(raw_doc, url),
                "document_type": self._extract_document_type(raw_doc),
                "primary_heading": self._extract_primary_heading(raw_doc, content),
                "headings": raw_doc.get("headings", []),
                "keywords": raw_doc.get("keywords", []),
                "tags": self._extract_tags(raw_doc),
                "content_length": len(content),
                "word_count": len(content.split()),
                "language": raw_doc.get("language", "en"),
                "author": raw_doc.get("author", raw_doc.get("metadata", {}).get("author")),
                "created_at": self._parse_timestamp(raw_doc.get("created_at")),
                "crawled_at": self._parse_timestamp(raw_doc.get("crawled_at")),
                "last_modified": self._parse_timestamp(raw_doc.get("modified_date")),
                "quality_score": raw_doc.get("quality_score", raw_doc.get("metadata", {}).get("quality_score")),
            }
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {"document_id": str(uuid.uuid4())}

    def _get_content(self, doc: Dict[str, Any]) -> str:
        """Get full content text."""
        if "markdown" in doc:
            return doc["markdown"]
        if "body" in doc:
            return doc["body"]
        if "content" in doc:
            return doc["content"]
        return ""

    def _determine_source_type(self, doc: Dict[str, Any]) -> str:
        """Determine source type."""
        if doc.get("_source") == "downloaded_document":
            return doc.get("file_type", "unknown")
        return "webpage"

    def _extract_section(self, doc: Dict[str, Any], url: str) -> str:
        """Extract section/category."""
        if "section" in doc:
            return doc["section"]
        
        # Infer from URL
        sections = {
            "admissions": ["admission", "apply", "enrollment"],
            "academics": ["course", "program", "curriculum", "academics"],
            "placements": ["placement", "recruitment", "career"],
            "faculty": ["faculty", "staff", "professor"],
            "facilities": ["facility", "lab", "library", "hostel"],
            "news": ["news", "announcement", "blog"],
            "events": ["event", "conference", "seminar"],
        }
        
        url_lower = url.lower()
        for section, keywords in sections.items():
            for keyword in keywords:
                if keyword in url_lower:
                    return section
        
        return "general"

    def _extract_department(self, doc: Dict[str, Any], url: str) -> Optional[str]:
        """Extract department information."""
        if "department" in doc:
            return doc["department"]
        
        # Common department identifiers in URLs
        departments = ["cse", "ece", "me", "civil", "chemical", "admin", "admissions"]
        
        url_lower = url.lower()
        for dept in departments:
            if dept in url_lower:
                return dept.upper()
        
        return None

    def _extract_document_type(self, doc: Dict[str, Any]) -> str:
        """Extract document type."""
        if "document_type" in doc:
            return doc["document_type"]
        
        # Infer from content or metadata
        title_lower = doc.get("title", "").lower()
        content_lower = self._get_content(doc).lower()
        
        type_patterns = {
            "announcement": ["announcement", "notice", "alert"],
            "policy": ["policy", "guideline", "procedure"],
            "form": ["form", "application", "request"],
            "resource": ["resource", "guide", "tutorial", "manual"],
            "schedule": ["schedule", "timetable", "calendar"],
            "procedure": ["procedure", "steps", "how to"],
        }
        
        for doc_type, patterns in type_patterns.items():
            for pattern in patterns:
                if pattern in title_lower or content_lower.count(pattern) > 2:
                    return doc_type
        
        return "content"

    def _extract_primary_heading(self, doc: Dict[str, Any], content: str) -> Optional[str]:
        """Extract primary heading from content."""
        # Check for H1 in headings
        headings = doc.get("headings", [])
        for heading in headings:
            if heading.get("level") == 1:
                return heading.get("text")
        
        # Try to extract from content
        lines = content.split("\n")
        for line in lines:
            if line.startswith("#") and not line.startswith("##"):
                return line.lstrip("#").strip()
        
        return None

    def _extract_tags(self, doc: Dict[str, Any]) -> List[str]:
        """Extract and generate tags."""
        tags = doc.get("tags", []) or doc.get("keywords", []).copy()
        
        # Add automatic tags based on section
        section = doc.get("section", "")
        if section and section not in tags:
            tags.insert(0, section)
        
        return tags[:10]  # Limit to 10 tags

    def _parse_timestamp(self, ts_value: Any) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if not ts_value:
            return None
        
        if isinstance(ts_value, datetime):
            return ts_value
        
        if isinstance(ts_value, str):
            try:
                return datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
            except Exception:
                try:
                    return datetime.strptime(ts_value, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
        
        return None
