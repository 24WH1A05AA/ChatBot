"""
Document chunking orchestrator and CLI.

Coordinates chunking process and provides command-line interface.
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Any
import sys
import argparse

from config import get_settings
from core.logger import setup_logging, get_logger
from ingestion.chunk_models import DocumentChunk, ChunkingResult
from ingestion.chunk_processor import IntelligentChunker

logger = get_logger(__name__)


class ChunkingOrchestrator:
    """
    Orchestrates document chunking process.
    
    Loads documents, applies intelligent chunking, and persists results.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """
        Initialize orchestrator.
        
        Args:
            chunk_size: Target chunk size
            chunk_overlap: Chunk overlap
        """
        self.chunker = IntelligentChunker(chunk_size, chunk_overlap)
        self.all_chunks: List[DocumentChunk] = []

    def chunk_knowledge_base(
        self,
        kb_json_path: Path,
        output_dir: Path,
    ) -> ChunkingResult:
        """
        Chunk entire knowledge base.
        
        Args:
            kb_json_path: Path to knowledge.json
            output_dir: Output directory
            
        Returns:
            ChunkingResult with statistics
        """
        start_time = time.time()
        
        try:
            logger.info("=== Starting Document Chunking ===")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Load knowledge base
            logger.info(f"Loading knowledge base from {kb_json_path}")
            with open(kb_json_path, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            documents = kb_data.get("documents", [])
            logger.info(f"Loaded {len(documents)} documents")
            
            # Process each document
            self.all_chunks = []
            for i, doc in enumerate(documents):
                chunks = self.chunker.chunk(doc)
                self.all_chunks.extend(chunks)
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Chunked {i + 1}/{len(documents)} documents")
            
            # Save chunks
            logger.info(f"Saving {len(self.all_chunks)} chunks")
            output_file = output_dir / "chunks.json"
            self._save_chunks(output_file)
            
            # Generate statistics
            stats = self._generate_statistics(documents)
            
            elapsed = time.time() - start_time
            
            logger.info(f"=== Chunking Complete ({elapsed:.1f}s) ===")
            
            return ChunkingResult(
                total_documents=len(documents),
                total_chunks=len(self.all_chunks),
                avg_chunk_size=stats['avg_size'],
                min_chunk_size=stats['min_size'],
                max_chunk_size=stats['max_size'],
                chunks_with_tables=stats['chunks_with_tables'],
                chunks_with_lists=stats['chunks_with_lists'],
                total_words=stats['total_words'],
                output_file=str(output_file),
                processing_time=elapsed,
            )
        
        except Exception as e:
            logger.error(f"Chunking failed: {e}", exc_info=True)
            raise

    def _save_chunks(self, output_file: Path) -> None:
        """
        Save chunks to JSON file.
        
        Args:
            output_file: Output file path
        """
        try:
            chunk_dicts = [json.loads(c.model_dump_json(default=str)) for c in self.all_chunks]
            
            output_data = {
                "version": "1.0",
                "total_chunks": len(self.all_chunks),
                "chunks": chunk_dicts,
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Saved chunks to {output_file}")
        
        except Exception as e:
            logger.error(f"Error saving chunks: {e}")
            raise

    def _generate_statistics(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate chunking statistics."""
        return self.chunker.get_statistics(self.all_chunks)


def main(args: argparse.Namespace) -> int:
    """CLI entry point."""
    try:
        settings = get_settings()
        setup_logging(
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE,
            is_debug=settings.DEBUG,
        )
        
        logger.info("=== Document Chunking Pipeline ===")
        
        kb_path = Path(args.kb_file) if args.kb_file else Path(settings.PERSIST_DIRECTORY) / "merged" / "knowledge.json"
        output_dir = Path(args.output_dir) if args.output_dir else Path(settings.PERSIST_DIRECTORY) / "chunks"
        
        if not kb_path.exists():
            logger.error(f"Knowledge base file not found: {kb_path}")
            logger.info("Run: python generate_kb.py")
            return 1
        
        orchestrator = ChunkingOrchestrator(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        
        result = orchestrator.chunk_knowledge_base(kb_path, output_dir)
        
        # Print results
        logger.info("\n=== Chunking Results ===")
        logger.info(f"Total Documents: {result.total_documents}")
        logger.info(f"Total Chunks: {result.total_chunks}")
        logger.info(f"Average Chunk Size: {result.avg_chunk_size:.0f} chars")
        logger.info(f"Min/Max: {result.min_chunk_size}/{result.max_chunk_size} chars")
        logger.info(f"Chunks with Tables: {result.chunks_with_tables}")
        logger.info(f"Chunks with Lists: {result.chunks_with_lists}")
        logger.info(f"Total Words: {result.total_words:,}")
        logger.info(f"Processing Time: {result.processing_time:.1f}s")
        logger.info(f"\nOutput: {result.output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunk documents for embedding")
    parser.add_argument("--kb-file", help="Knowledge base JSON file")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap")
    
    args = parser.parse_args()
    sys.exit(main(args))
