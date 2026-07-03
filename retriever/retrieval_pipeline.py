"""
Retrieval pipeline orchestrating query encoding and search.

Handles end-to-end retrieval from query text to results.
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime

from retriever.retriever_advanced import AdvancedRetriever, SearchResult, RetrieverConfig
from retriever.query_encoder import QueryEncoder
from vectorstore.vectorstore import VectorStore
from core.logger import get_logger

logger = get_logger(__name__)


class RetrievalResult:
    """Complete retrieval result with query and results."""

    def __init__(
        self,
        query: str,
        results: List[SearchResult],
        retrieval_time_ms: float,
        method: str = "hybrid",
    ) -> None:
        """Initialize retrieval result."""
        self.query = query
        self.results = results
        self.retrieval_time_ms = retrieval_time_ms
        self.method = method
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "method": self.method,
            "results": [r.to_dict() for r in self.results],
            "total_results": len(self.results),
            "retrieval_time_ms": self.retrieval_time_ms,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class RetrievalPipeline:
    """End-to-end retrieval pipeline."""

    def __init__(
        self,
        vectorstore: VectorStore,
        retriever_config: Optional[RetrieverConfig] = None,
        cache_embeddings: bool = True,
    ) -> None:
        """
        Initialize retrieval pipeline.
        
        Args:
            vectorstore: Vector store instance
            retriever_config: Retriever configuration
            cache_embeddings: Cache query embeddings
        """
        self.vectorstore = vectorstore
        self.retriever = AdvancedRetriever(vectorstore, retriever_config)
        self.query_encoder = QueryEncoder()
        
        # Cache for query embeddings
        self.embedding_cache = {} if cache_embeddings else None

    def retrieve(
        self,
        query: str,
        k: int = 5,
        section: Optional[str] = None,
        department: Optional[str] = None,
        min_score: Optional[float] = None,
        use_cache: bool = True,
    ) -> Optional[RetrievalResult]:
        """
        Retrieve documents for query.
        
        Args:
            query: Query text
            k: Number of results
            section: Filter by section
            department: Filter by department
            min_score: Minimum similarity score
            use_cache: Use cached embeddings
            
        Returns:
            RetrievalResult object or None on error
        """
        try:
            import time
            start_time = time.time()
            
            # Preprocess query
            processed_query = self.query_encoder.preprocess_query(query)
            
            # Check cache
            if use_cache and self.embedding_cache is not None:
                if processed_query in self.embedding_cache:
                    query_embedding = self.embedding_cache[processed_query]
                    logger.debug("Query embedding from cache")
                else:
                    query_embedding = self.query_encoder.encode(processed_query)
                    if query_embedding:
                        self.embedding_cache[processed_query] = query_embedding
            else:
                query_embedding = self.query_encoder.encode(processed_query)
            
            if query_embedding is None:
                logger.error("Failed to encode query")
                return None
            
            # Hybrid search
            results = self.retriever.hybrid_search(
                query_embedding=query_embedding,
                k=k,
                section=section,
                department=department,
                min_score=min_score,
            )
            
            # Calculate retrieval time
            retrieval_time = (time.time() - start_time) * 1000
            
            result = RetrievalResult(
                query=query,
                results=results,
                retrieval_time_ms=retrieval_time,
                method="hybrid",
            )
            
            logger.info(f"Retrieved {len(results)} results in {retrieval_time:.1f}ms")
            return result
        
        except Exception as e:
            logger.error(f"Error in retrieval pipeline: {e}")
            return None

    def retrieve_semantic(
        self,
        query: str,
        k: int = 5,
        min_score: Optional[float] = None,
    ) -> Optional[RetrievalResult]:
        """Pure semantic search without filtering."""
        try:
            import time
            start_time = time.time()
            
            processed_query = self.query_encoder.preprocess_query(query)
            query_embedding = self.query_encoder.encode(processed_query)
            
            if query_embedding is None:
                return None
            
            results = self.retriever.semantic_search(
                query_embedding,
                k=k,
                min_score=min_score,
            )
            
            retrieval_time = (time.time() - start_time) * 1000
            
            return RetrievalResult(
                query=query,
                results=results,
                retrieval_time_ms=retrieval_time,
                method="semantic",
            )
        
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            return None

    def retrieve_by_section(
        self,
        query: str,
        section: str,
        k: int = 5,
    ) -> Optional[RetrievalResult]:
        """Retrieve from specific section."""
        return self.retrieve(query, k=k, section=section)

    def retrieve_by_department(
        self,
        query: str,
        department: str,
        k: int = 5,
    ) -> Optional[RetrievalResult]:
        """Retrieve from specific department."""
        return self.retrieve(query, k=k, department=department)

    def batch_retrieve(
        self,
        queries: List[str],
        k: int = 5,
        section: Optional[str] = None,
    ) -> List[Optional[RetrievalResult]]:
        """
        Retrieve for multiple queries.
        
        Args:
            queries: List of query texts
            k: Results per query
            section: Filter by section
            
        Returns:
            List of RetrievalResult objects
        """
        try:
            results = []
            for query in queries:
                result = self.retrieve(query, k=k, section=section)
                results.append(result)
            
            logger.info(f"Batch retrieved {len(queries)} queries")
            return results
        
        except Exception as e:
            logger.error(f"Error in batch retrieval: {e}")
            return [None] * len(queries)

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        if self.embedding_cache is not None:
            self.embedding_cache.clear()
            logger.info("Cleared embedding cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.embedding_cache is None:
            return {"cache_enabled": False}
        
        return {
            "cache_enabled": True,
            "cached_queries": len(self.embedding_cache),
            "cache_size_kb": len(str(self.embedding_cache)) / 1024,
        }


class RetrievalEvaluator:
    """Evaluate retrieval quality and performance."""

    @staticmethod
    def evaluate_result(
        result: RetrievalResult,
        ground_truth_chunks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a retrieval result.
        
        Args:
            result: RetrievalResult to evaluate
            ground_truth_chunks: Expected chunk IDs
            
        Returns:
            Evaluation metrics
        """
        try:
            metrics = {
                "query": result.query,
                "total_results": len(result.results),
                "retrieval_time_ms": result.retrieval_time_ms,
                "method": result.method,
            }
            
            if result.results:
                scores = [r.similarity_score for r in result.results]
                metrics.update({
                    "avg_similarity": sum(scores) / len(scores),
                    "min_similarity": min(scores),
                    "max_similarity": max(scores),
                    "avg_chunk_length": sum(len(r.text) for r in result.results) / len(result.results),
                })
            
            # Calculate recall if ground truth provided
            if ground_truth_chunks:
                retrieved_chunks = {r.chunk_id for r in result.results}
                ground_truth = set(ground_truth_chunks)
                recall = len(retrieved_chunks & ground_truth) / len(ground_truth)
                precision = len(retrieved_chunks & ground_truth) / len(retrieved_chunks) if retrieved_chunks else 0
                
                metrics.update({
                    "recall": recall,
                    "precision": precision,
                    "f1": 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0,
                })
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error evaluating result: {e}")
            return {}

    @staticmethod
    def batch_evaluate(
        results: List[RetrievalResult],
        ground_truth: Optional[List[List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate multiple retrieval results.
        
        Args:
            results: List of RetrievalResult objects
            ground_truth: List of ground truth chunk IDs per query
            
        Returns:
            Aggregate evaluation metrics
        """
        try:
            evaluations = []
            
            for i, result in enumerate(results):
                gt = ground_truth[i] if ground_truth and i < len(ground_truth) else None
                evals = RetrievalEvaluator.evaluate_result(result, gt)
                evaluations.append(evals)
            
            # Aggregate metrics
            if not evaluations:
                return {}
            
            avg_time = sum(e.get("retrieval_time_ms", 0) for e in evaluations) / len(evaluations)
            total_results = sum(e.get("total_results", 0) for e in evaluations)
            
            return {
                "total_queries": len(evaluations),
                "avg_retrieval_time_ms": avg_time,
                "total_results": total_results,
                "evaluations": evaluations,
            }
        
        except Exception as e:
            logger.error(f"Error batch evaluating: {e}")
            return {}
