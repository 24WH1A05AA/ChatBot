"""
Embedding generation with batching, rate limiting, and resume capability.

Generates embeddings using OpenAI's text-embedding-3-small model.
"""

import hashlib
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from datetime import datetime
from collections import defaultdict

import openai
from embedding.embedding_models import EmbeddingVector, EmbeddingBatch
from core.logger import get_logger
from core.optimization import (
    get_optimization_engine,
    ParallelExecutor,
    BatchProcessor,
    BatchConfig,
    RetryPolicy,
    cached,
    retry,
    timed,
    Compression,
)

logger = get_logger(__name__)


class DuplicateDetector:
    """Detects duplicate chunks."""

    def __init__(self) -> None:
        """Initialize detector."""
        self.chunk_hashes: Set[str] = set()

    def is_duplicate(self, text: str) -> bool:
        """
        Check if chunk is duplicate.
        
        Args:
            text: Chunk text
            
        Returns:
            True if duplicate
        """
        chunk_hash = hashlib.sha256(text.encode()).hexdigest()
        
        if chunk_hash in self.chunk_hashes:
            return True
        
        self.chunk_hashes.add(chunk_hash)
        return False


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 3000) -> None:
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Max requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
        self.min_interval = 60.0 / requests_per_minute

    def acquire(self) -> None:
        """Wait until rate limit allows next request."""
        now = time.time()
        
        # Remove old requests outside the minute window
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60.0 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        self.request_times.append(time.time())


class BatchManager:
    """Manages batch creation and processing."""

    def __init__(self, batch_size: int = 100) -> None:
        """
        Initialize batch manager.
        
        Args:
            batch_size: Number of chunks per batch
        """
        self.batch_size = batch_size

    def create_batches(
        self,
        chunks: List[Dict[str, Any]],
        skip_duplicates: bool = True,
    ) -> Tuple[List[EmbeddingBatch], Set[str]]:
        """
        Create batches from chunks.
        
        Args:
            chunks: List of chunks
            skip_duplicates: Skip duplicate chunks
            
        Returns:
            Tuple of (batches, skipped_chunk_ids)
        """
        try:
            detector = DuplicateDetector()
            batches = []
            skipped = set()
            
            batch_chunks = []
            batch_texts = []
            batch_ids = []
            
            for chunk in chunks:
                chunk_text = chunk.get("content", "")
                chunk_id = chunk.get("chunk_id", "")
                
                # Check for duplicates
                if skip_duplicates and detector.is_duplicate(chunk_text):
                    skipped.add(chunk_id)
                    continue
                
                batch_chunks.append(chunk)
                batch_texts.append(chunk_text)
                batch_ids.append(chunk_id)
                
                # Create batch when full
                if len(batch_chunks) >= self.batch_size:
                    batch = EmbeddingBatch(
                        chunk_ids=batch_ids,
                        texts=batch_texts,
                        batch_size=len(batch_chunks),
                    )
                    batches.append(batch)
                    batch_chunks = []
                    batch_texts = []
                    batch_ids = []
            
            # Add remaining batch
            if batch_chunks:
                batch = EmbeddingBatch(
                    chunk_ids=batch_ids,
                    texts=batch_texts,
                    batch_size=len(batch_chunks),
                )
                batches.append(batch)
            
            logger.info(f"Created {len(batches)} batches, skipped {len(skipped)} duplicates")
            return batches, skipped
        
        except Exception as e:
            logger.error(f"Error creating batches: {e}")
            return [], set()


class OpenAIEmbeddingGenerator:
    """Generates embeddings using OpenAI API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize embedding generator.
        
        Args:
            model: Embedding model name
            batch_size: Batch size
            max_retries: Max retries for failed requests
        """
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.rate_limiter = RateLimiter()

    async def generate_batch(
        self,
        batch: EmbeddingBatch,
        chunk_data: Dict[str, Dict[str, Any]],
    ) -> List[EmbeddingVector]:
        """
        Generate embeddings for a batch.
        
        Args:
            batch: Batch to process
            chunk_data: Chunk metadata by ID
            
        Returns:
            List of EmbeddingVector objects
        """
        try:
            # Wait for rate limit
            self.rate_limiter.acquire()
            
            # Generate embeddings with retry logic
            embeddings = None
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    response = openai.Embedding.create(
                        input=batch.texts,
                        model=self.model,
                    )
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    embeddings = response.get("data", [])
                    break
                
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        raise
            
            if not embeddings:
                logger.error("No embeddings returned")
                return []
            
            # Create EmbeddingVector objects
            vectors = []
            for i, emb_data in enumerate(embeddings):
                chunk_id = batch.chunk_ids[i]
                chunk_info = chunk_data.get(chunk_id, {})
                
                vector = EmbeddingVector(
                    chunk_id=chunk_id,
                    document_id=chunk_info.get("document_id", ""),
                    vector=emb_data["embedding"],
                    model=self.model,
                    chunk_text=batch.texts[i],
                    chunk_title=chunk_info.get("heading"),
                    section=chunk_info.get("section", ""),
                    source_url=chunk_info.get("source_url", ""),
                    processing_time_ms=processing_time / len(embeddings),
                )
                vectors.append(vector)
            
            logger.info(f"Generated {len(vectors)} embeddings for batch {batch.batch_id}")
            return vectors
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return []
