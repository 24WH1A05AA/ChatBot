"""
ChromaDB vector store implementation.

Manages persistent vector database with similarity search, metadata filtering,
and incremental updates.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Persistent vector store using ChromaDB."""

    def __init__(
        self,
        collection_name: str = "college_faq",
        persist_dir: Path = Path("knowledge_base/vectorstore"),
        create_if_missing: bool = True,
    ) -> None:
        """
        Initialize vector store.
        
        Args:
            collection_name: Name of the collection
            persist_dir: Directory for persistence
            create_if_missing: Create if doesn't exist
        """
        self.collection_name = collection_name
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        settings = ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.persist_dir),
            anonymized_telemetry=False,
        )
        
        self.client = chromadb.Client(settings)
        self.collection = None
        self._load_or_create_collection()
        
        logger.info(f"Initialized VectorStore: {collection_name}")

    def _load_or_create_collection(self) -> None:
        """Load existing collection or create new one."""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
            count = self.collection.count()
            logger.info(f"Loaded existing collection: {count} embeddings")
        
        except Exception as e:
            # Create new collection
            logger.debug(f"Creating new collection: {e}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            logger.info("Created new collection")

    def add_embeddings(
        self,
        embeddings: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Add embeddings to the store.
        
        Args:
            embeddings: List of embedding dicts with vector and metadata
            batch_size: Batch size for insertion
            
        Returns:
            Statistics dictionary
        """
        try:
            if not embeddings:
                logger.warning("No embeddings to add")
                return {
                    "added": 0,
                    "skipped": 0,
                    "failed": 0,
                    "total": 0,
                }
            
            added = 0
            skipped = 0
            failed = 0
            existing_ids = set()
            
            # Get existing IDs
            try:
                existing_data = self.collection.get()
                existing_ids = set(existing_data.get("ids", []))
            except Exception:
                pass
            
            # Process in batches
            for i in range(0, len(embeddings), batch_size):
                batch = embeddings[i:i + batch_size]
                
                # Prepare batch data
                ids = []
                vectors = []
                metadatas = []
                documents = []
                
                for emb in batch:
                    emb_id = emb.get("embedding_id") or emb.get("chunk_id")
                    
                    # Skip if already exists
                    if emb_id in existing_ids:
                        skipped += 1
                        continue
                    
                    ids.append(emb_id)
                    vectors.append(emb.get("vector", []))
                    
                    # Extract metadata (exclude vector and text)
                    metadata = {
                        k: v for k, v in emb.items()
                        if k not in ["vector", "chunk_text", "embedding_id", "vector_dim"]
                        and v is not None
                    }
                    metadatas.append(metadata)
                    documents.append(emb.get("chunk_text", ""))
                
                if ids:
                    try:
                        self.collection.add(
                            ids=ids,
                            embeddings=vectors,
                            metadatas=metadatas,
                            documents=documents,
                        )
                        added += len(ids)
                    except Exception as e:
                        logger.error(f"Error adding batch: {e}")
                        failed += len(ids)
            
            stats = {
                "added": added,
                "skipped": skipped,
                "failed": failed,
                "total": added + skipped + failed,
            }
            
            logger.info(f"Added embeddings: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error adding embeddings: {e}")
            return {
                "added": 0,
                "skipped": 0,
                "failed": len(embeddings),
                "total": len(embeddings),
            }

    def query(
        self,
        query_embedding: List[float],
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Similarity search.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            where: Metadata filter conditions
            
        Returns:
            List of results with similarity scores
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where,
            )
            
            # Format results
            formatted = []
            for i in range(len(results.get("ids", [[]])[0])):
                result = {
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                }
                formatted.append(result)
            
            return formatted
        
        except Exception as e:
            logger.error(f"Error querying: {e}")
            return []

    def get_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding by chunk ID."""
        try:
            result = self.collection.get(ids=[chunk_id])
            
            if not result.get("ids"):
                return None
            
            return {
                "chunk_id": result["ids"][0],
                "text": result["documents"][0] if result.get("documents") else "",
                "metadata": result["metadatas"][0] if result.get("metadatas") else {},
            }
        
        except Exception as e:
            logger.error(f"Error getting by ID: {e}")
            return None

    def delete(self, chunk_ids: List[str]) -> Dict[str, int]:
        """Delete embeddings by chunk IDs."""
        try:
            deleted = 0
            for chunk_id in chunk_ids:
                try:
                    self.collection.delete(ids=[chunk_id])
                    deleted += 1
                except Exception as e:
                    logger.warning(f"Could not delete {chunk_id}: {e}")
            
            logger.info(f"Deleted {deleted} embeddings")
            return {"deleted": deleted, "total": len(chunk_ids)}
        
        except Exception as e:
            logger.error(f"Error deleting: {e}")
            return {"deleted": 0, "total": len(chunk_ids)}

    def filter_by_metadata(
        self,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Get embeddings matching metadata filters.
        
        Args:
            filters: Metadata filter conditions
            
        Returns:
            List of matching embeddings
        """
        try:
            results = self.collection.get(where=filters)
            
            formatted = []
            for i in range(len(results.get("ids", []))):
                formatted.append({
                    "chunk_id": results["ids"][i],
                    "text": results["documents"][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                })
            
            return formatted
        
        except Exception as e:
            logger.error(f"Error filtering by metadata: {e}")
            return []

    def update(self, embedding: Dict[str, Any]) -> bool:
        """Update an embedding."""
        try:
            emb_id = embedding.get("embedding_id") or embedding.get("chunk_id")
            
            self.collection.update(
                ids=[emb_id],
                embeddings=[embedding.get("vector", [])],
                metadatas=[{
                    k: v for k, v in embedding.items()
                    if k not in ["vector", "chunk_text", "embedding_id"]
                    and v is not None
                }],
                documents=[embedding.get("chunk_text", "")],
            )
            
            logger.debug(f"Updated embedding: {emb_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating embedding: {e}")
            return False

    def persist(self) -> None:
        """Persist the collection to disk."""
        try:
            self.client.persist()
            logger.info("Persisted collection to disk")
        except Exception as e:
            logger.error(f"Error persisting: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to infer schema
            sample = self.collection.get(limit=10)
            metadata_keys = set()
            for meta in sample.get("metadatas", []):
                metadata_keys.update(meta.keys())
            
            return {
                "collection_name": self.collection_name,
                "total_embeddings": count,
                "persist_directory": str(self.persist_dir),
                "metadata_fields": sorted(list(metadata_keys)),
                "created_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}

    def reload(self) -> None:
        """Reload collection from disk."""
        try:
            self._load_or_create_collection()
            logger.info("Reloaded collection from disk")
        except Exception as e:
            logger.error(f"Error reloading: {e}")
