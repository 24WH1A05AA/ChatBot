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
    """Single search result with comprehensive metadata."""

    def __init__(
        self,
        chunk_id: str,
        text: str,
        metadata: Dict[str, Any],
        similarity_score: float,
        rank: int = 0,
        retrieval_method: str = "semantic",
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
        """
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata
        self.similarity_score = similarity_score
        self.rank = rank
        self.retrieval_method = retrieval_method
        self.chunk_length = len(text)
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


class AdvancedRetriever:
    """Advanced retriever with semantic search and comprehensive filtering."""

    def __init__(
        self,
        vectorstore: VectorStore,
        config: Optional[RetrieverConfig] = None,
    ) -> None:
        """
        Initialize retriever.
        
        Args:
            vectorstore: Vector store instance
            config: Retriever configuration
        """
        self.vectorstore = vectorstore
        self.config = config or RetrieverConfig()

    def semantic_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        min_score: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Pure semantic similarity search.
        
        Args:
            query_embedding: Query vector (1536 dims)
            k: Number of results
            min_score: Minimum similarity score
            
        Returns:
            List of SearchResult objects ranked by similarity
        """
        try:
            threshold = min_score if min_score is not None else self.config.similarity_threshold
            
            # Query vector store (fetch extra for filtering)
            results = self.vectorstore.query(
                query_embedding=query_embedding,
                k=k * 2,
            )
            
            # Convert to SearchResult objects
            search_results = []
            for result in results:
                distance = result.get("distance", 1.0)
                similarity = 1 - distance
                
                if similarity >= threshold:
                    search_result = SearchResult(
                        chunk_id=result.get("chunk_id", ""),
                        text=result.get("text", ""),
                        metadata=result.get("metadata", {}),
                        similarity_score=similarity,
                        rank=len(search_results) + 1,
                        retrieval_method="semantic",
                    )
                    search_results.append(search_result)
                    
                    if len(search_results) >= k:
                        break
            
            logger.debug(f"Semantic search returned {len(search_results)} results")
            return search_results
        
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def filter_by_section(
        self,
        results: List[SearchResult],
        section: str,
    ) -> List[SearchResult]:
        """
        Filter results by section.
        
        Args:
            results: Search results
            section: Section name
            
        Returns:
            Filtered results
        """
        filtered = [r for r in results if r.metadata.get("section") == section]
        return self._update_ranks(filtered)

    def filter_by_department(
        self,
        results: List[SearchResult],
        department: str,
    ) -> List[SearchResult]:
        """
        Filter results by department.
        
        Args:
            results: Search results
            department: Department name
            
        Returns:
            Filtered results
        """
        filtered = [r for r in results if r.metadata.get("department") == department]
        return self._update_ranks(filtered)

    def filter_by_url(
        self,
        results: List[SearchResult],
        url: str,
    ) -> List[SearchResult]:
        """
        Filter results by source URL.
        
        Args:
            results: Search results
            url: Source URL
            
        Returns:
            Filtered results
        """
        filtered = [r for r in results if r.metadata.get("source_url") == url]
        return self._update_ranks(filtered)

    def filter_by_chunk_length(
        self,
        results: List[SearchResult],
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Filter results by chunk text length.
        
        Args:
            results: Search results
            min_length: Minimum length
            max_length: Maximum length
            
        Returns:
            Filtered results
        """
        min_len = min_length or self.config.min_chunk_length
        max_len = max_length or self.config.max_chunk_length
        
        filtered = [
            r for r in results
            if min_len <= len(r.text) <= max_len
        ]
        return self._update_ranks(filtered)

    def remove_duplicates(
        self,
        results: List[SearchResult],
        by: str = "url",
    ) -> List[SearchResult]:
        """
        Remove duplicate results.
        
        Args:
            results: Search results
            by: Deduplication method ("url", "chunk_id", "content")
            
        Returns:
            Deduplicated results
        """
        try:
            if not self.config.enable_duplicate_removal:
                return results
            
            seen = set()
            unique = []
            
            if by == "url":
                for result in results:
                    url = result.metadata.get("source_url", "")
                    if url not in seen:
                        seen.add(url)
                        unique.append(result)
            
            elif by == "chunk_id":
                for result in results:
                    if result.chunk_id not in seen:
                        seen.add(result.chunk_id)
                        unique.append(result)
            
            elif by == "content":
                for result in results:
                    content_hash = hash(result.text[:100])
                    if content_hash not in seen:
                        seen.add(content_hash)
                        unique.append(result)
            
            logger.debug(f"Removed duplicates: {len(results)} → {len(unique)}")
            return self._update_ranks(unique)
        
        except Exception as e:
            logger.error(f"Error removing duplicates: {e}")
            return results

    def apply_score_threshold(
        self,
        results: List[SearchResult],
        threshold: float,
    ) -> List[SearchResult]:
        """
        Filter results by similarity score threshold.
        
        Args:
            results: Search results
            threshold: Minimum score (0.0-1.0)
            
        Returns:
            Filtered results above threshold
        """
        filtered = [r for r in results if r.similarity_score >= threshold]
        return self._update_ranks(filtered)

    def top_k_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        min_score: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Top-K semantic search.
        
        Args:
            query_embedding: Query vector
            k: Number of top results
            min_score: Minimum similarity score
            
        Returns:
            Top K results
        """
        results = self.semantic_search(query_embedding, k=k, min_score=min_score)
        return results[:k]

    def hybrid_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        section: Optional[str] = None,
        department: Optional[str] = None,
        min_score: Optional[float] = None,
        remove_duplicates: bool = True,
    ) -> List[SearchResult]:
        """
        Hybrid search combining semantic search with filters.
        
        Args:
            query_embedding: Query vector
            k: Number of results
            section: Filter by section
            department: Filter by department
            min_score: Minimum similarity score
            remove_duplicates: Remove duplicate URLs
            
        Returns:
            Filtered and ranked results
        """
        try:
            logger.debug(f"Hybrid search: k={k}, section={section}, department={department}")
            
            # Semantic search
            results = self.semantic_search(
                query_embedding,
                k=k * 2,
                min_score=min_score,
            )
            
            # Apply filters
            if section:
                results = self.filter_by_section(results, section)
            
            if department:
                results = self.filter_by_department(results, department)
            
            # Remove duplicates
            if remove_duplicates:
                results = self.remove_duplicates(results)
            
            # Return top K
            return results[:k]
        
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    def rerank_by_diversity(
        self,
        results: List[SearchResult],
        diversity_penalty: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Rerank results emphasizing diversity.
        
        Args:
            results: Search results
            diversity_penalty: Weight for diversity (0.0-1.0)
            
        Returns:
            Diversity-reranked results
        """
        try:
            if not results or not self.config.enable_diversity_reranking:
                return results
            
            penalty = diversity_penalty or self.config.diversity_penalty
            reranked = []
            seen_urls = set()
            
            for result in results:
                url = result.metadata.get("source_url", "")
                
                if url in seen_urls:
                    result.similarity_score *= (1 - penalty)
                
                seen_urls.add(url)
                reranked.append(result)
            
            # Re-sort by adjusted score
            reranked.sort(key=lambda x: x.similarity_score, reverse=True)
            return self._update_ranks(reranked)
        
        except Exception as e:
            logger.error(f"Error reranking by diversity: {e}")
            return results

    def rerank_by_section_diversity(
        self,
        results: List[SearchResult],
        penalty: float = 0.15,
    ) -> List[SearchResult]:
        """
        Rerank to diversify across sections.
        
        Args:
            results: Search results
            penalty: Penalty for repeated sections
            
        Returns:
            Reranked results
        """
        try:
            reranked = []
            seen_sections = set()
            
            for result in results:
                section = result.metadata.get("section", "")
                
                if section in seen_sections:
                    result.similarity_score *= (1 - penalty)
                
                seen_sections.add(section)
                reranked.append(result)
            
            reranked.sort(key=lambda x: x.similarity_score, reverse=True)
            return self._update_ranks(reranked)
        
        except Exception as e:
            logger.error(f"Error reranking by section: {e}")
            return results

    def batch_search(
        self,
        query_embeddings: List[List[float]],
        k: int = 5,
        min_score: Optional[float] = None,
    ) -> List[List[SearchResult]]:
        """
        Batch search for multiple queries.
        
        Args:
            query_embeddings: List of query vectors
            k: Results per query
            min_score: Minimum score
            
        Returns:
            List of result lists
        """
        try:
            batch_results = []
            for query_embedding in query_embeddings:
                results = self.semantic_search(query_embedding, k=k, min_score=min_score)
                batch_results.append(results)
            
            logger.debug(f"Batch search: {len(query_embeddings)} queries")
            return batch_results
        
        except Exception as e:
            logger.error(f"Error in batch search: {e}")
            return []

    def get_result_stats(
        self,
        results: List[SearchResult],
    ) -> Dict[str, Any]:
        """
        Generate statistics from search results.
        
        Args:
            results: Search results
            
        Returns:
            Statistics dictionary
        """
        try:
            if not results:
                return {
                    "total_results": 0,
                    "avg_similarity": 0.0,
                    "min_similarity": 0.0,
                    "max_similarity": 0.0,
                }
            
            scores = [r.similarity_score for r in results]
            sections = defaultdict(int)
            departments = defaultdict(int)
            
            for result in results:
                sections[result.metadata.get("section", "unknown")] += 1
                departments[result.metadata.get("department", "unknown")] += 1
            
            return {
                "total_results": len(results),
                "avg_similarity": float(np.mean(scores)),
                "min_similarity": float(np.min(scores)),
                "max_similarity": float(np.max(scores)),
                "std_similarity": float(np.std(scores)),
                "sections": dict(sections),
                "departments": dict(departments),
            }
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def _update_ranks(self, results: List[SearchResult]) -> List[SearchResult]:
        """Update rank numbers for results."""
        for idx, result in enumerate(results):
            result.rank = idx + 1
        return results
