"""
Chunk data models for intelligent document chunking.

Defines all chunk structures with metadata preservation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class DocumentChunk(BaseModel):
    """
    Complete chunk with all metadata.
    
    Represents a single chunk from a document with
    preserved metadata and structural information.
    """

    # Chunk identification
    chunk_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique chunk identifier"
    )
    document_id: str = Field(..., description="Source document ID")
    chunk_index: int = Field(..., description="Sequence index within document")
    total_chunks: int = Field(..., description="Total chunks in document")
    
    # Content
    content: str = Field(..., description="Chunk text content")
    
    # Source information
    source_url: str = Field(..., description="Original document URL")
    source_type: str = Field(
        default="webpage",
        description="Source type (webpage, pdf, docx, etc.)"
    )
    
    # Document metadata
    document_title: str = Field(..., description="Document title")
    page_title: str = Field(..., description="Page title")
    section: str = Field(..., description="Document section")
    heading: Optional[str] = Field(
        default=None,
        description="Primary heading of chunk"
    )
    heading_level: Optional[int] = Field(
        default=None,
        description="Heading level (1-6) if chunk starts with heading"
    )
    
    # Content statistics
    character_count: int = Field(
        default=0,
        description="Total characters in chunk"
    )
    word_count: int = Field(
        default=0,
        description="Total words in chunk"
    )
    line_count: int = Field(
        default=0,
        description="Number of lines"
    )
    
    # Structure information
    contains_table: bool = Field(
        default=False,
        description="Contains markdown table"
    )
    contains_list: bool = Field(
        default=False,
        description="Contains bullet or ordered list"
    )
    contains_code: bool = Field(
        default=False,
        description="Contains code block"
    )
    
    # Position in document
    start_char: int = Field(
        default=0,
        description="Start character index in document"
    )
    end_char: int = Field(
        default=0,
        description="End character index in document"
    )
    
    # Metadata
    keywords: List[str] = Field(
        default_factory=list,
        description="Associated keywords"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Chunk tags"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Chunk creation time"
    )
    
    # Quality metrics
    quality_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Chunk quality score"
    )
    semantic_completeness: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Semantic completeness score"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk-uuid",
                "document_id": "doc-uuid",
                "chunk_index": 1,
                "total_chunks": 10,
                "content": "# Admissions Requirements\n\nStudents must...",
                "source_url": "https://example.edu/admissions",
                "document_title": "Admissions",
                "page_title": "Admissions - College",
                "section": "admissions",
                "heading": "Admissions Requirements",
                "character_count": 1024,
                "word_count": 150,
            }
        }


class ChunkingRequest(BaseModel):
    """Request for document chunking."""
    
    knowledge_base_dir: str = Field(
        default="knowledge_base/merged",
        description="Directory with knowledge base"
    )
    output_dir: str = Field(
        default="knowledge_base/chunks",
        description="Output directory for chunks"
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Target chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between chunks in characters"
    )


class ChunkingResult(BaseModel):
    """Result of chunking process."""
    
    total_documents: int = Field(..., description="Total documents processed")
    total_chunks: int = Field(..., description="Total chunks created")
    avg_chunk_size: float = Field(..., description="Average chunk size")
    min_chunk_size: int = Field(..., description="Minimum chunk size")
    max_chunk_size: int = Field(..., description="Maximum chunk size")
    chunks_with_tables: int = Field(..., description="Chunks containing tables")
    chunks_with_lists: int = Field(..., description="Chunks containing lists")
    total_words: int = Field(..., description="Total words in all chunks")
    output_file: Optional[str] = Field(..., description="Path to chunks JSON file")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total_documents": 450,
                "total_chunks": 2250,
                "avg_chunk_size": 850.5,
                "min_chunk_size": 150,
                "max_chunk_size": 1100,
                "chunks_with_tables": 150,
                "chunks_with_lists": 450,
                "total_words": 337500,
                "output_file": "knowledge_base/chunks/chunks.json",
                "processing_time": 45.2,
            }
        }
