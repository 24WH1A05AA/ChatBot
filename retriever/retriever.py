"""
Advanced retrieval system with semantic search, filtering, and hybrid retrieval.

Provides semantic search, metadata filtering, department filtering, top-K
retrieval, hybrid search, score thresholding, and duplicate removal.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import numpy as np
from datetime import datetime
from collections import defaultdict

from vectorstore.vectorstore import VectorStore
from core.logger import get_logger

logger = get_logger(__name__)


class SearchResult:
    """Single search result with all metadata."""

    def __init__(
        self,
        chunk_id: str,
        text: str,
        metadata: Dict[str, Any],
        similarity_score: float,
        rank: int = 0,
        retrieval_method: str = "semantic",
        chunk_length: int = 0,
    ) -> None:
        """
        Initialize search result.
        
        Args:
            chunk_id: Unique chunk identifier
            text: Chunk content
            metadata: Document metadata (15+ fields)
            similarity_score: Cosine similarity (0.0-1.0)
            rank: Result ranking
            retrieval_method: How this was retrieved
            chunk_length: Text length in characters
        """
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata
        self.similarity_score = similarity_score
        self.rank = rank
        self.retrieval_method = retrieval_method
        self.chunk_length = len(text) if not chunk_length else chunk_length
        self.retrieved_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
            "similarity_score": self.similarity_score,
            "rank": self.rank,
            "retrieval_method": self.retrieval_method,
            "chunk_length": self.chunk_length,
            "source_url": self.metadata.get("source_url"),
            "section": self.metadata.get("section"),
            "department": self.metadata.get("department"),
            "heading": self.metadata.get("chunk_title"),
            "retrieved_at": self.retrieved_at,
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"SearchResult(rank={self.rank}, score={self.similarity_score:.3f}, chunk_id={self.chunk_id})"


class RetrieverConfig:
    """Configuration for retriever."""

    def __init__(
        self,
        similarity_threshold: float = 0.3,
        top_k: int = 5,
        enable_duplicate_removal: bool = True,
        enable_diversity_reranking: bool = True,
        diversity_penalty: float = 0.2,
        min_chunk_length: int = 10,
        max_chunk_length: int = 10000,
    ) -> None:
        """
        Initialize configuration.
        
        Args:
            similarity_threshold: Minimum similarity score (0.0-1.0)
            top_k: Default number of results
            enable_duplicate_removal: Remove duplicate URLs
            enable_diversity_reranking: Apply diversity penalty
            diversity_penalty: Weight for diversity (0.0-1.0)
            min_chunk_length: Minimum chunk text length
            max_chunk_length: Maximum chunk text length
        """
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.enable_duplicate_removal = enable_duplicate_removal
        self.enable_diversity_reranking = enable_diversity_reranking
        self.diversity_penalty = diversity_penalty
        self.min_chunk_length = min_chunk_length
        self.max_chunk_length = max_chunk_length


class Retriever:
    """Advanced retriever with semantic search and filtering."""

    def __init__(
        self,
        vectorstore: VectorStore,
        similarity_threshold: float = 0.3,
    ) -> None:
        """
        Initialize retriever.
        
        Args:
            vectorstore: Vector store instance
            similarity_threshold: Minimum similarity score
        """
        self.vectorstore = vectorstore
        self.similarity_threshold = similarity_threshold

    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        section: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Search for relevant documents.
        
        Args:
            query_embedding: Query vector (1536 dims)
            k: Number of results
            section: Filter by section
            min_score: Minimum similarity score
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        try:
            # Use provided min_score or default
            threshold = min_score if min_score is not None else self.similarity_threshold
            
            # Build metadata filter if section specified
            where = None
            if section:
                where = {"section": section}
            
            # Query vector store
            results = self.vectorstore.query(
                query_embedding=query_embedding,
                k=k,
                where=where,
            )
            
            # Convert to SearchResult objects
            search_results = []
            for rank, result in enumerate(results):
                # Convert distance to similarity (cosine)
                # ChromaDB returns distance, we convert to similarity
                distance = result.get("distance", 1.0)
                similarity = 1 - distance  # For cosine distance
                
                if similarity >= threshold:
                    search_result = SearchResult(
                        chunk_id=result.get("chunk_id", ""),
                        text=result.get("text", ""),
                        metadata=result.get("metadata", {}),
                        similarity_score=similarity,
                        rank=rank + 1,
                    )
                    search_results.append(search_result)
            
            logger.debug(f"Search returned {len(search_results)} results above threshold")
            return search_results
        
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def search_by_section(
        self,
        query_embedding: List[float],
        section: str,
        k: int = 5,
    ) -> List[SearchResult]:
        """Search within a specific section."""
        return self.search(
            query_embedding=query_embedding,
            k=k,
            section=section,
        )

    def rerank_results(
        self,
        results: List[SearchResult],
        query_text: Optional[str] = None,
        diversity_factor: float = 0.2,
    ) -> List[SearchResult]:
        """
        Rerank search results for diversity and relevance.
        
        Args:
            results: Initial search results
            query_text: Query text for keyword matching
            diversity_factor: Weight for diversity (0.0-1.0)
            
        Returns:
            Reranked results
        """
        try:
            if not results:
                return results
            
            # Calculate diversity penalties
            ranked = []
            seen_urls = set()
            
            for result in results:
                url = result.metadata.get("source_url", "")
                
                # Penalize similar URLs for diversity
                diversity_penalty = 0
                if url in seen_urls:
                    diversity_penalty = diversity_factor
                
                seen_urls.add(url)
                
                # Adjust score
                adjusted_score = result.similarity_score * (1 - diversity_penalty)
                result.similarity_score = adjusted_score
                ranked.append(result)
            
            # Re-sort by adjusted score
            ranked.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Update ranks
            for rank, result in enumerate(ranked):
                result.rank = rank + 1
            
            return ranked
        
        except Exception as e:
            logger.error(f"Error reranking results: {e}")
            return results

    def get_context(
        self,
        results: List[SearchResult],
        include_metadata: bool = True,
    ) -> str:
        """
        Generate context string from search results.
        
        Args:
            results: Search results
            include_metadata: Include metadata in context
            
        Returns:
            Formatted context string
        """
        try:
            context_parts = []
            
            for result in results:
                part = f"[Source: {result.metadata.get('source_url', 'Unknown')}]\n"
                
                if result.metadata.get("chunk_title"):
                    part += f"## {result.metadata.get('chunk_title')}\n"
                
                part += f"{result.text}\n"
                
                if include_metadata:
                    part += f"(Similarity: {result.similarity_score:.2%})\n"
                
                context_parts.append(part)
            
            return "\n---\n".join(context_parts)
        
        except Exception as e:
            logger.error(f"Error generating context: {e}")
            return ""

    def get_citations(
        self,
        results: List[SearchResult],
    ) -> List[Dict[str, str]]:
        """
        Extract citations from search results.
        
        Args:
            results: Search results
            
        Returns:
            List of citations with URL and section
        """
        try:
            citations = []
            seen = set()
            
            for result in results:
                url = result.metadata.get("source_url", "")
                section = result.metadata.get("section", "")
                title = result.metadata.get("chunk_title", "")
                
                citation_key = f"{url}:{section}"
                
                if citation_key not in seen:
                    citations.append({
                        "url": url,
                        "section": section,
                        "title": title,
                        "rank": result.rank,
                    })
                    seen.add(citation_key)
            
            return citations
        
        except Exception as e:
            logger.error(f"Error generating citations: {e}")
            return []

    def batch_search(
        self,
        query_embeddings: List[List[float]],
        k: int = 5,
    ) -> List[List[SearchResult]]:
        """
        Batch search for multiple queries.
        
        Args:
            query_embeddings: List of query vectors
            k: Results per query
            
        Returns:
            List of result lists
        """
        try:
            batch_results = []
            for query_embedding in query_embeddings:
                results = self.search(query_embedding, k=k)
                batch_results.append(results)
            
            logger.debug(f"Batch search processed {len(query_embeddings)} queries")
            return batch_results
        
        except Exception as e:
            logger.error(f"Error in batch search: {e}")
            return []
