"""
Embedding state tracking and orchestration.

Handles resume capability, persistence, and statistics.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime

from embedding.embedding_models import EmbeddingVector, EmbeddingResult
from core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingStateTracker:
    """Tracks embedding generation state for resume capability."""

    def __init__(self, state_file: Path) -> None:
        """Initialize state tracker."""
        self.state_file = state_file
        self.processed_chunks: Set[str] = set()
        self.failed_chunks: Set[str] = set()
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.processed_chunks = set(data.get("processed", []))
                    self.failed_chunks = set(data.get("failed", []))
                logger.info(f"Loaded state: {len(self.processed_chunks)} processed, {len(self.failed_chunks)} failed")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")

    def save_state(self) -> None:
        """Save state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "processed": list(self.processed_chunks),
                "failed": list(self.failed_chunks),
                "saved_at": datetime.utcnow().isoformat(),
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def mark_processed(self, chunk_id: str) -> None:
        """Mark chunk as processed."""
        self.processed_chunks.add(chunk_id)

    def mark_failed(self, chunk_id: str) -> None:
        """Mark chunk as failed."""
        self.failed_chunks.add(chunk_id)

    def is_processed(self, chunk_id: str) -> bool:
        """Check if chunk was already processed."""
        return chunk_id in self.processed_chunks


class EmbeddingStatistics:
    """Generates embedding statistics."""

    @staticmethod
    def calculate(
        total_chunks: int,
        generated: int,
        skipped: int,
        failed: int,
        processing_times: List[float],
        total_tokens: int,
        generation_time: float,
    ) -> Dict[str, Any]:
        """
        Calculate statistics.
        
        Args:
            total_chunks: Total chunks
            generated: Successfully generated embeddings
            skipped: Skipped duplicates
            failed: Failed chunks
            processing_times: Individual processing times
            total_tokens: Tokens used
            generation_time: Total time
            
        Returns:
            Statistics dictionary
        """
        try:
            avg_time = sum(processing_times) / max(len(processing_times), 1)
            
            return {
                "total_chunks": total_chunks,
                "generated": generated,
                "skipped": skipped,
                "failed": failed,
                "success_rate": (generated / max(total_chunks, 1)) * 100,
                "avg_processing_time_ms": avg_time,
                "min_time_ms": min(processing_times) if processing_times else 0,
                "max_time_ms": max(processing_times) if processing_times else 0,
                "total_tokens": total_tokens,
                "generation_time_seconds": generation_time,
                "chunks_per_second": generated / max(generation_time, 1),
            }
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}


class EmbeddingOrchestrator:
    """Orchestrates embedding generation."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        output_dir: Path = Path("knowledge_base/embeddings"),
    ) -> None:
        """Initialize orchestrator."""
        self.model = model
        self.batch_size = batch_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_tracker = EmbeddingStateTracker(
            self.output_dir / "embedding_state.json"
        )
        self.embeddings: List[EmbeddingVector] = []
        self.processing_times: List[float] = []

    def add_embedding(self, vector: EmbeddingVector) -> None:
        """Add embedding to collection."""
        self.embeddings.append(vector)
        self.processing_times.append(vector.processing_time_ms)
        self.state_tracker.mark_processed(vector.chunk_id)

    def save_embeddings(self) -> Path:
        """Save embeddings to JSON."""
        try:
            output_file = self.output_dir / "embeddings.json"
            
            embedding_dicts = [
                json.loads(e.model_dump_json(default=str))
                for e in self.embeddings
            ]
            
            output_data = {
                "version": "1.0",
                "model": self.model,
                "total_embeddings": len(self.embeddings),
                "embeddings": embedding_dicts,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(self.embeddings)} embeddings to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            raise

    def get_result(
        self,
        total_chunks: int,
        skipped: int,
        failed: int,
        total_tokens: int,
        generation_time: float,
    ) -> EmbeddingResult:
        """Create result object."""
        stats = EmbeddingStatistics.calculate(
            total_chunks=total_chunks,
            generated=len(self.embeddings),
            skipped=skipped,
            failed=failed,
            processing_times=self.processing_times,
            total_tokens=total_tokens,
            generation_time=generation_time,
        )
        
        output_file = self.output_dir / "embeddings.json"
        
        return EmbeddingResult(
            total_chunks=total_chunks,
            total_embeddings=len(self.embeddings),
            skipped_duplicates=skipped,
            failed_chunks=failed,
            total_batches=len(self.embeddings) // max(self.batch_size, 1),
            avg_processing_time_ms=stats.get("avg_processing_time_ms", 0),
            total_tokens_used=total_tokens,
            output_file=str(output_file) if output_file.exists() else None,
            generation_time=generation_time,
        )
