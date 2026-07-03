"""
Embedding data models for vector representation.

Defines structures for embeddings, metadata, and statistics.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class EmbeddingVector(BaseModel):
    """Complete embedding with metadata."""

    # Embedding identification
    embedding_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique embedding identifier"
    )
    chunk_id: str = Field(..., description="Source chunk ID")
    document_id: str = Field(..., description="Source document ID")
    
    # Vector data
    vector: List[float] = Field(..., description="Embedding vector (1536 dims)")
    vector_dim: int = Field(
        default=1536,
        description="Vector dimension"
    )
    model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model used"
    )
    
    # Content metadata
    chunk_text: str = Field(..., description="Original chunk text")
    chunk_title: Optional[str] = Field(
        default=None,
        description="Chunk heading if applicable"
    )
    section: str = Field(..., description="Document section")
    source_url: str = Field(..., description="Source document URL")
    
    # Processing metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Embedding creation time"
    )
    processing_time_ms: float = Field(
        default=0.0,
        description="Time to generate embedding"
    )
    
    # Quality metrics
    magnitude: Optional[float] = Field(
        default=None,
        description="Vector magnitude (L2 norm)"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "embedding_id": "emb-uuid",
                "chunk_id": "chunk-uuid",
                "document_id": "doc-uuid",
                "vector": [0.1, 0.2, 0.3, ...],
                "model": "text-embedding-3-small",
                "chunk_text": "Content here...",
                "section": "admissions",
            }
        }


class EmbeddingBatch(BaseModel):
    """Batch of chunks for embedding."""
    
    chunk_ids: List[str] = Field(..., description="Chunk IDs in batch")
    texts: List[str] = Field(..., description="Chunk texts in batch")
    batch_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique batch ID"
    )
    batch_size: int = Field(..., description="Batch size")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Batch creation time"
    )


class EmbeddingRequest(BaseModel):
    """Embedding generation request."""
    
    chunks_file: str = Field(
        default="knowledge_base/chunks/chunks.json",
        description="Path to chunks JSON file"
    )
    output_dir: str = Field(
        default="knowledge_base/embeddings",
        description="Output directory for embeddings"
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=2000,
        description="Batch size for embedding requests"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retries for failed requests"
    )


class EmbeddingResult(BaseModel):
    """Result of embedding generation."""
    
    total_chunks: int = Field(..., description="Total chunks processed")
    total_embeddings: int = Field(..., description="Embeddings generated")
    skipped_duplicates: int = Field(..., description="Duplicate chunks skipped")
    failed_chunks: int = Field(..., description="Failed chunks")
    total_batches: int = Field(..., description="Total batches processed")
    avg_processing_time_ms: float = Field(..., description="Average processing time")
    total_tokens_used: int = Field(..., description="Approximate tokens used")
    output_file: Optional[str] = Field(..., description="Path to embeddings file")
    generation_time: float = Field(..., description="Total generation time")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total_chunks": 2250,
                "total_embeddings": 2200,
                "skipped_duplicates": 50,
                "failed_chunks": 0,
                "total_batches": 22,
                "avg_processing_time_ms": 150.0,
                "total_tokens_used": 250000,
                "output_file": "knowledge_base/embeddings/embeddings.json",
                "generation_time": 300.5,
            }
        }
