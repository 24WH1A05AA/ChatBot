"""
Base data models and types for the application.

Defines core data structures used throughout the application
with type hints and validation.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Represents a crawled document from the website."""

    id: str = Field(..., description="Unique document identifier")
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "doc_001",
                "url": "https://example.com/page",
                "title": "Page Title",
                "content": "Page content...",
                "metadata": {"section": "admissions"},
            }
        }


class Chunk(BaseModel):
    """Represents a text chunk from a document."""

    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk text content")
    start_index: int = Field(..., description="Start index in document")
    end_index: int = Field(..., description="End index in document")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk metadata"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "chunk_001",
                "document_id": "doc_001",
                "content": "Chunk content...",
                "start_index": 0,
                "end_index": 100,
                "metadata": {},
            }
        }


class RetrievalResult(BaseModel):
    """Represents a retrieval result from the vector store."""

    chunk_id: str = Field(..., description="Chunk identifier")
    document_id: str = Field(..., description="Document identifier")
    content: str = Field(..., description="Chunk content")
    similarity_score: float = Field(..., description="Similarity score")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Associated metadata"
    )
    url: Optional[str] = Field(
        default=None,
        description="Source document URL"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "content": "Relevant content...",
                "similarity_score": 0.87,
                "metadata": {},
                "url": "https://example.com/page",
            }
        }


class ChatMessage(BaseModel):
    """Represents a message in the conversation."""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What are the admission requirements?",
                "timestamp": "2024-01-01T12:00:00",
            }
        }


class ChatResponse(BaseModel):
    """Represents a chatbot response."""

    message: str = Field(..., description="Response message")
    citations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of citations"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Response confidence score"
    )
    retrieval_results: list[RetrievalResult] = Field(
        default_factory=list,
        description="Retrieved documents used for response"
    )
    processing_time_ms: float = Field(
        default=0.0,
        description="Processing time in milliseconds"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "message": "The admission deadline is...",
                "citations": [{"source": "url", "title": "Page Title"}],
                "confidence": 0.92,
                "retrieval_results": [],
                "processing_time_ms": 250.5,
            }
        }


class EvaluationMetrics(BaseModel):
    """Represents evaluation metrics for a response."""

    faithfulness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Faithfulness to retrieved context"
    )
    context_precision: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Precision of retrieved context"
    )
    context_recall: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Recall of retrieved context"
    )
    answer_relevancy: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevancy of the answer"
    )
    latency_ms: float = Field(
        default=0.0,
        description="Query latency in milliseconds"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "faithfulness": 0.85,
                "context_precision": 0.88,
                "context_recall": 0.82,
                "answer_relevancy": 0.87,
                "latency_ms": 450.0,
            }
        }
