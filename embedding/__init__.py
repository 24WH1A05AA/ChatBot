"""
Embedding module for generating and managing document embeddings.

Provides text embedding generation using OpenAI's embedding models,
orchestration of embedding processes, and model configuration.
"""

from .embedding_generator import OpenAIEmbeddingGenerator
from .embedding_orchestrator import EmbeddingOrchestrator
from .embedding_models import EmbeddingVector, EmbeddingBatch, EmbeddingRequest, EmbeddingResult

__all__ = [
    "OpenAIEmbeddingGenerator",
    "EmbeddingOrchestrator",
    "EmbeddingVector",
    "EmbeddingBatch",
    "EmbeddingRequest",
    "EmbeddingResult",
]
