"""
CLI for embedding generation.

Usage:
    python generate_embeddings.py
    python generate_embeddings.py --chunks-file ./chunks.json --batch-size 50
"""

import sys
import time
import json
import asyncio
import argparse
from pathlib import Path

from config import get_settings
from core.logger import setup_logging, get_logger
from embedding.embedding_models import EmbeddingBatch
from embedding.embedding_generator import (
    DuplicateDetector,
    RateLimiter,
    BatchManager,
    OpenAIEmbeddingGenerator,
)
from embedding.embedding_orchestrator import EmbeddingOrchestrator, EmbeddingStatistics

logger = get_logger(__name__)


async def generate_embeddings(
    chunks_file: Path,
    output_dir: Path,
    batch_size: int = 100,
    max_retries: int = 3,
    resume: bool = True,
) -> int:
    """
    Generate embeddings for all chunks.
    
    Args:
        chunks_file: Path to chunks JSON
        output_dir: Output directory
        batch_size: Batch size for requests
        max_retries: Max retries for failures
        resume: Resume from previous state
        
    Returns:
        Exit code
    """
    try:
        logger.info("=== Starting Embedding Generation ===")
        start_time = time.time()
        
        # Load chunks
        logger.info(f"Loading chunks from {chunks_file}")
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        chunks = chunks_data.get("chunks", [])
        logger.info(f"Loaded {len(chunks)} chunks")
        
        # Create chunk lookup
        chunk_lookup = {c.get("chunk_id"): c for c in chunks}
        
        # Create batch manager
        batch_mgr = BatchManager(batch_size=batch_size)
        batches, skipped_dups = batch_mgr.create_batches(
            chunks,
            skip_duplicates=True
        )
        
        # Create generator and orchestrator
        generator = OpenAIEmbeddingGenerator(
            batch_size=batch_size,
            max_retries=max_retries,
        )
        
        orchestrator = EmbeddingOrchestrator(
            batch_size=batch_size,
            output_dir=output_dir,
        )
        
        # Process batches
        logger.info(f"Processing {len(batches)} batches")
        failed_chunks = set()
        total_tokens = 0
        
        for i, batch in enumerate(batches):
            try:
                # Skip if already processed (resume)
                if resume and orchestrator.state_tracker.is_processed(batch.chunk_ids[0]):
                    logger.debug(f"Skipping already processed batch {i + 1}")
                    continue
                
                # Generate embeddings
                vectors = await generator.generate_batch(batch, chunk_lookup)
                
                # Add to orchestrator
                for vector in vectors:
                    orchestrator.add_embedding(vector)
                
                # Estimate tokens (rough: ~4 chars per token)
                batch_tokens = sum(len(t) for t in batch.texts) // 4
                total_tokens += batch_tokens
                
                # Progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(batches)} batches")
                    orchestrator.state_tracker.save_state()
                
            except Exception as e:
                logger.error(f"Error processing batch {i}: {e}")
                failed_chunks.update(batch.chunk_ids)
        
        # Save embeddings
        output_file = orchestrator.save_embeddings()
        orchestrator.state_tracker.save_state()
        
        # Generate result
        elapsed = time.time() - start_time
        result = orchestrator.get_result(
            total_chunks=len(chunks),
            skipped=len(skipped_dups),
            failed=len(failed_chunks),
            total_tokens=total_tokens,
            generation_time=elapsed,
        )
        
        # Print results
        logger.info("\n=== Embedding Generation Complete ===")
        logger.info(f"Total Chunks: {result.total_chunks}")
        logger.info(f"Generated: {result.total_embeddings}")
        logger.info(f"Skipped (duplicates): {result.skipped_duplicates}")
        logger.info(f"Failed: {result.failed_chunks}")
        logger.info(f"Avg Processing Time: {result.avg_processing_time_ms:.1f}ms")
        logger.info(f"Total Tokens: {result.total_tokens_used:,}")
        logger.info(f"Generation Time: {result.generation_time:.1f}s")
        logger.info(f"Output: {result.output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def main(args: argparse.Namespace) -> int:
    """CLI entry point."""
    try:
        settings = get_settings()
        setup_logging(
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE,
            is_debug=settings.DEBUG,
        )
        
        chunks_file = Path(args.chunks_file) if args.chunks_file else Path(settings.PERSIST_DIRECTORY) / "chunks" / "chunks.json"
        output_dir = Path(args.output_dir) if args.output_dir else Path(settings.PERSIST_DIRECTORY) / "embeddings"
        
        if not chunks_file.exists():
            logger.error(f"Chunks file not found: {chunks_file}")
            logger.info("Run: python chunk_documents.py")
            return 1
        
        return asyncio.run(generate_embeddings(
            chunks_file=chunks_file,
            output_dir=output_dir,
            batch_size=args.batch_size,
            max_retries=args.max_retries,
            resume=args.resume,
        ))
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for chunks")
    parser.add_argument("--chunks-file", help="Path to chunks JSON file")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries")
    parser.add_argument("--no-resume", action="store_false", dest="resume", help="Don't resume")
    
    args = parser.parse_args()
    sys.exit(main(args))
