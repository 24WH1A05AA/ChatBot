"""
Knowledge base data models with comprehensive metadata.

Defines all required fields and structures for knowledge base generation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class KnowledgeBaseDocument(BaseModel):
    """
    Complete knowledge base document with all metadata.
    
    Represents a single document in the knowledge base with
    comprehensive tracking and metadata fields.
    """

    # Unique identification
    document_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique document identifier"
    )
    
    # Content
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content (markdown)")
    summary: Optional[str] = Field(
        default=None,
        description="Brief summary"
    )
    
    # Source information
    source_url: str = Field(..., description="Original source URL")
    source_type: str = Field(
        default="webpage",
        description="Source type (webpage, pdf, docx, csv, txt)"
    )
    
    # Organization
    section: str = Field(
        default="general",
        description="Main section/category"
    )
    subsection: Optional[str] = Field(
        default=None,
        description="Sub-section if applicable"
    )
    department: Optional[str] = Field(
        default=None,
        description="Department or department identifier"
    )
    
    # Document structure
    page_title: str = Field(..., description="Page/document title")
    primary_heading: Optional[str] = Field(
        default=None,
        description="Primary H1 heading"
    )
    headings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Heading hierarchy"
    )
    
    # Metadata
    document_type: str = Field(
        default="content",
        description="Type: content, announcement, policy, procedure, form, resource"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Associated keywords"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Additional tags"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Document creation time"
    )
    crawled_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Crawl timestamp"
    )
    indexed_at: Optional[datetime] = Field(
        default=None,
        description="Knowledge base indexing time"
    )
    
    # Quality metrics
    quality_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Content quality score"
    )
    content_length: int = Field(
        default=0,
        description="Content length in characters"
    )
    word_count: int = Field(
        default=0,
        description="Word count"
    )
    
    # Associated content
    related_links: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Related links found in content"
    )
    images: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Images in content"
    )
    tables: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tables in content"
    )
    
    # Additional metadata
    language: str = Field(
        default="en",
        description="Content language code"
    )
    author: Optional[str] = Field(
        default=None,
        description="Document author"
    )
    last_modified: Optional[datetime] = Field(
        default=None,
        description="Last modification date"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "document_id": "doc-uuid-here",
                "title": "Admissions Process",
                "content": "# Admissions\n\nContent here...",
                "source_url": "https://example.edu/admissions",
                "section": "admissions",
                "document_type": "content",
                "page_title": "Admissions - Example College",
            }
        }


class KnowledgeBaseMergeRequest(BaseModel):
    """Request for knowledge base generation."""

    cleaned_pages_dir: str = Field(
        default="knowledge_base/cleaned",
        description="Directory with cleaned pages"
    )
    documents_dir: Optional[str] = Field(
        default="knowledge_base/documents",
        description="Directory with downloaded documents"
    )
    output_dir: str = Field(
        default="knowledge_base/merged",
        description="Output directory for knowledge base"
    )
    include_documents: bool = Field(
        default=True,
        description="Include downloaded documents"
    )


class KnowledgeBaseMergeResult(BaseModel):
    """Result of knowledge base generation."""

    total_documents: int = Field(..., description="Total documents merged")
    documents_from_pages: int = Field(..., description="Documents from crawled pages")
    documents_from_files: int = Field(..., description="Documents from downloaded files")
    json_file: Optional[str] = Field(..., description="Path to knowledge.json")
    markdown_file: Optional[str] = Field(..., description="Path to knowledge.md")
    csv_file: Optional[str] = Field(..., description="Path to knowledge.csv")
    total_words: int = Field(..., description="Total words in knowledge base")
    total_characters: int = Field(..., description="Total characters")
    sections_found: List[str] = Field(..., description="Unique sections")
    generation_time: float = Field(..., description="Generation time in seconds")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total_documents": 450,
                "documents_from_pages": 400,
                "documents_from_files": 50,
                "json_file": "knowledge_base/merged/knowledge.json",
                "markdown_file": "knowledge_base/merged/knowledge.md",
                "csv_file": "knowledge_base/merged/knowledge.csv",
                "total_words": 125000,
                "total_characters": 750000,
                "sections_found": ["admissions", "academics", "placements"],
            }
        }
