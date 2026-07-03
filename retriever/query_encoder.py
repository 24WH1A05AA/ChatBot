"""
Query encoding and embedding generation.

Converts text queries to embeddings for semantic search.
"""

from typing import List, Optional, Dict, Any
import openai

from core.logger import get_logger

logger = get_logger(__name__)


class QueryEncoder:
    """Encodes text queries to embeddings."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        max_retries: int = 3,
    ) -> None:
        """
        Initialize query encoder.
        
        Args:
            model: Embedding model name
            max_retries: Max retries for API calls
        """
        self.model = model
        self.max_retries = max_retries

    def encode(
        self,
        query: str,
    ) -> Optional[List[float]]:
        """
        Encode a single query to embedding.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector (1536 dims) or None on error
        """
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided")
                return None
            
            # Generate embedding
            for attempt in range(self.max_retries):
                try:
                    response = openai.Embedding.create(
                        input=query,
                        model=self.model,
                    )
                    
                    embedding = response.get("data", [{}])[0].get("embedding")
                    
                    if embedding:
                        logger.debug(f"Encoded query: {len(query)} chars → {len(embedding)} dims")
                        return embedding
                
                except openai.error.RateLimitError:
                    if attempt < self.max_retries - 1:
                        import time
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        raise
            
            return None
        
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            return None

    def encode_batch(
        self,
        queries: List[str],
    ) -> List[Optional[List[float]]]:
        """
        Encode multiple queries.
        
        Args:
            queries: List of query texts
            
        Returns:
            List of embeddings (may contain None for failed queries)
        """
        try:
            embeddings = []
            
            for query in queries:
                embedding = self.encode(query)
                embeddings.append(embedding)
            
            logger.debug(f"Batch encoded {len(queries)} queries, {len([e for e in embeddings if e])} successful")
            return embeddings
        
        except Exception as e:
            logger.error(f"Error batch encoding queries: {e}")
            return [None] * len(queries)

    def preprocess_query(
        self,
        query: str,
        lowercase: bool = True,
        remove_extra_spaces: bool = True,
    ) -> str:
        """
        Preprocess query text.
        
        Args:
            query: Query text
            lowercase: Convert to lowercase
            remove_extra_spaces: Remove extra whitespace
            
        Returns:
            Processed query
        """
        try:
            text = query
            
            if lowercase:
                text = text.lower()
            
            if remove_extra_spaces:
                text = " ".join(text.split())
            
            return text
        
        except Exception as e:
            logger.error(f"Error preprocessing query: {e}")
            return query
