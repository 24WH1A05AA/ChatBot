"""
Vector store indexing orchestrator.

Handles loading embeddings, managing incremental updates, and generating statistics.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from vectorstore.vectorstore import VectorStore
from core.logger import get_logger

logger = get_logger(__name__)


class IndexStatistics:
    """Statistics generator for the vector index."""

    @staticmethod
    def calculate(
        total_embeddings: int,
        indexed: int,
        duplicates: int,
        failed: int,
        indexing_time: float,
        file_size_mb: float,
        metadata_fields: List[str],
    ) -> Dict[str, Any]:
        """Calculate indexing statistics."""
        try:
            return {
                "total_embeddings": total_embeddings,
                "indexed": indexed,
                "skipped_duplicates": duplicates,
                "failed": failed,
                "success_rate": (indexed / max(total_embeddings, 1)) * 100,
                "indexing_time_seconds": indexing_time,
                "embeddings_per_second": indexed / max(indexing_time, 1),
                "file_size_mb": file_size_mb,
                "metadata_fields": metadata_fields,
                "indexed_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}


class IndexingOrchestrator:
    """Orchestrates indexing of embeddings into vector store."""

    def __init__(
        self,
        collection_name: str = "college_faq",
        vectorstore_dir: Path = Path("knowledge_base/vectorstore"),
        embeddings_file: Path = Path("knowledge_base/embeddings/embeddings.json"),
    ) -> None:
        """
        Initialize orchestrator.
        
        Args:
            collection_name: ChromaDB collection name
            vectorstore_dir: Vector store persistence directory
            embeddings_file: Path to embeddings JSON file
        """
        self.collection_name = collection_name
        self.vectorstore_dir = Path(vectorstore_dir)
        self.embeddings_file = Path(embeddings_file)
        
        # Initialize vector store
        self.vectorstore = VectorStore(
            collection_name=collection_name,
            persist_dir=vectorstore_dir,
        )
        
        # Track state
        self.processed_ids: Set[str] = set()
        self.failed_ids: Set[str] = set()
        self.duplicate_ids: Set[str] = set()

    def load_embeddings_file(self) -> List[Dict[str, Any]]:
        """Load embeddings from JSON file."""
        try:
            if not self.embeddings_file.exists():
                logger.error(f"Embeddings file not found: {self.embeddings_file}")
                return []
            
            with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            embeddings = data.get("embeddings", [])
            logger.info(f"Loaded {len(embeddings)} embeddings from file")
            return embeddings
        
        except Exception as e:
            logger.error(f"Error loading embeddings file: {e}")
            return []

    def index_embeddings(
        self,
        embeddings: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100,
        skip_existing: bool = True,
    ) -> Dict[str, Any]:
        """
        Index embeddings into vector store.
        
        Args:
            embeddings: Embeddings to index (if None, loads from file)
            batch_size: Batch size for insertion
            skip_existing: Skip already indexed embeddings
            
        Returns:
            Statistics dictionary
        """
        try:
            start_time = time.time()
            
            # Load embeddings if not provided
            if embeddings is None:
                embeddings = self.load_embeddings_file()
            
            if not embeddings:
                logger.warning("No embeddings to index")
                return {
                    "indexed": 0,
                    "skipped": 0,
                    "failed": 0,
                    "total": 0,
                }
            
            logger.info(f"Indexing {len(embeddings)} embeddings...")
            
            # Index embeddings
            stats = self.vectorstore.add_embeddings(
                embeddings=embeddings,
                batch_size=batch_size,
            )
            
            # Add timing
            elapsed = time.time() - start_time
            stats["indexing_time"] = elapsed
            
            # Persist
            self.vectorstore.persist()
            
            logger.info(f"Indexing complete: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error indexing embeddings: {e}")
            return {
                "indexed": 0,
                "skipped": 0,
                "failed": len(embeddings) if embeddings else 0,
                "total": len(embeddings) if embeddings else 0,
            }

    def incremental_index(
        self,
        new_embeddings: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Incrementally index new embeddings.
        
        Args:
            new_embeddings: New embeddings to add
            batch_size: Batch size
            
        Returns:
            Statistics
        """
        try:
            logger.info(f"Incrementally indexing {len(new_embeddings)} new embeddings...")
            
            stats = self.vectorstore.add_embeddings(
                embeddings=new_embeddings,
                batch_size=batch_size,
            )
            
            self.vectorstore.persist()
            logger.info(f"Incremental indexing complete: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error in incremental indexing: {e}")
            return {
                "indexed": 0,
                "skipped": 0,
                "failed": len(new_embeddings),
                "total": len(new_embeddings),
            }

    def delete_embeddings(self, chunk_ids: List[str]) -> Dict[str, int]:
        """Delete embeddings by chunk IDs."""
        try:
            logger.info(f"Deleting {len(chunk_ids)} embeddings...")
            
            stats = self.vectorstore.delete(chunk_ids)
            self.vectorstore.persist()
            
            logger.info(f"Deletion complete: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error deleting embeddings: {e}")
            return {"deleted": 0, "total": len(chunk_ids)}

    def get_index_statistics(self) -> Dict[str, Any]:
        """Get comprehensive index statistics."""
        try:
            # Get vectorstore stats
            vs_stats = self.vectorstore.get_statistics()
            
            # Calculate file size
            file_size = 0
            if self.embeddings_file.exists():
                file_size = self.embeddings_file.stat().st_size / (1024 * 1024)
            
            # Get persist dir size
            persist_size = 0
            if self.vectorstore_dir.exists():
                for file in self.vectorstore_dir.rglob('*'):
                    if file.is_file():
                        persist_size += file.stat().st_size / (1024 * 1024)
            
            return {
                **vs_stats,
                "embeddings_file_size_mb": file_size,
                "index_persist_size_mb": persist_size,
                "statistics_generated_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Error getting index statistics: {e}")
            return {"error": str(e)}

    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the index.
        
        Args:
            query_embedding: Query vector
            k: Number of results
            where: Metadata filters
            
        Returns:
            List of results
        """
        try:
            return self.vectorstore.query(
                query_embedding=query_embedding,
                k=k,
                where=where,
            )
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def filter_by_section(
        self,
        section: str,
    ) -> List[Dict[str, Any]]:
        """Get embeddings from a specific section."""
        try:
            return self.vectorstore.filter_by_metadata({
                "section": section
            })
        except Exception as e:
            logger.error(f"Error filtering by section: {e}")
            return []

    def filter_by_url(
        self,
        url: str,
    ) -> List[Dict[str, Any]]:
        """Get embeddings from a specific URL."""
        try:
            return self.vectorstore.filter_by_metadata({
                "source_url": url
            })
        except Exception as e:
            logger.error(f"Error filtering by URL: {e}")
            return []

    def reload_from_disk(self) -> None:
        """Reload index from disk."""
        try:
            logger.info("Reloading index from disk...")
            self.vectorstore.reload()
            logger.info("Index reloaded successfully")
        except Exception as e:
            logger.error(f"Error reloading index: {e}")

    def export_statistics(self, output_file: Path) -> None:
        """Export statistics to file."""
        try:
            stats = self.get_index_statistics()
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, default=str)
            
            logger.info(f"Statistics exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}")
