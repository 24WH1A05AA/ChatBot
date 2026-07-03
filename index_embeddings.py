"""
CLI for indexing embeddings into ChromaDB.

Usage:
    python index_embeddings.py
    python index_embeddings.py --embeddings-file ./embeddings.json
    python index_embeddings.py --stats-file ./index_stats.json
"""

import sys
import time
import json
import argparse
from pathlib import Path

from config import get_settings
from core.logger import setup_logging, get_logger
from vectorstore.indexing import IndexingOrchestrator, IndexStatistics

logger = get_logger(__name__)


def index_embeddings(
    embeddings_file: Path,
    vectorstore_dir: Path,
    batch_size: int = 100,
    collection_name: str = "college_faq",
) -> int:
    """
    Index embeddings into ChromaDB.
    
    Args:
        embeddings_file: Path to embeddings JSON file
        vectorstore_dir: Vector store directory
        batch_size: Batch size for indexing
        collection_name: Collection name
        
    Returns:
        Exit code
    """
    try:
        logger.info("=== Starting Embedding Indexing ===")
        start_time = time.time()
        
        if not embeddings_file.exists():
            logger.error(f"Embeddings file not found: {embeddings_file}")
            logger.info("Run: python generate_embeddings.py")
            return 1
        
        # Create orchestrator
        orchestrator = IndexingOrchestrator(
            collection_name=collection_name,
            vectorstore_dir=vectorstore_dir,
            embeddings_file=embeddings_file,
        )
        
        # Index embeddings
        logger.info(f"Indexing embeddings from {embeddings_file}")
        stats = orchestrator.index_embeddings(
            batch_size=batch_size,
        )
        
        elapsed = time.time() - start_time
        
        # Print results
        logger.info("\n=== Indexing Complete ===")
        logger.info(f"Indexed: {stats.get('added', 0)}")
        logger.info(f"Skipped (duplicates): {stats.get('skipped', 0)}")
        logger.info(f"Failed: {stats.get('failed', 0)}")
        logger.info(f"Total: {stats.get('total', 0)}")
        logger.info(f"Indexing Time: {elapsed:.1f}s")
        
        # Get and display statistics
        index_stats = orchestrator.get_index_statistics()
        logger.info(f"\nIndex Statistics:")
        logger.info(f"Total Embeddings: {index_stats.get('total_embeddings', 0)}")
        logger.info(f"Metadata Fields: {', '.join(index_stats.get('metadata_fields', []))}")
        logger.info(f"Index Size: {index_stats.get('index_persist_size_mb', 0):.1f} MB")
        logger.info(f"Embeddings File Size: {index_stats.get('embeddings_file_size_mb', 0):.1f} MB")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def reload_index(
    vectorstore_dir: Path,
    collection_name: str = "college_faq",
) -> int:
    """
    Reload index from disk without rebuilding.
    
    Args:
        vectorstore_dir: Vector store directory
        collection_name: Collection name
        
    Returns:
        Exit code
    """
    try:
        logger.info("=== Reloading Index from Disk ===")
        
        orchestrator = IndexingOrchestrator(
            collection_name=collection_name,
            vectorstore_dir=vectorstore_dir,
        )
        
        orchestrator.reload_from_disk()
        
        # Display statistics
        stats = orchestrator.get_index_statistics()
        logger.info(f"Loaded Collection: {stats.get('collection_name')}")
        logger.info(f"Total Embeddings: {stats.get('total_embeddings', 0)}")
        logger.info(f"Metadata Fields: {', '.join(stats.get('metadata_fields', []))}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def export_statistics(
    vectorstore_dir: Path,
    output_file: Path,
    collection_name: str = "college_faq",
) -> int:
    """
    Export index statistics.
    
    Args:
        vectorstore_dir: Vector store directory
        output_file: Output file path
        collection_name: Collection name
        
    Returns:
        Exit code
    """
    try:
        logger.info("=== Exporting Index Statistics ===")
        
        orchestrator = IndexingOrchestrator(
            collection_name=collection_name,
            vectorstore_dir=vectorstore_dir,
        )
        
        orchestrator.export_statistics(output_file)
        logger.info(f"Statistics exported to {output_file}")
        
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
        
        embeddings_file = Path(args.embeddings_file) if args.embeddings_file else Path(settings.PERSIST_DIRECTORY) / "embeddings" / "embeddings.json"
        vectorstore_dir = Path(args.vectorstore_dir) if args.vectorstore_dir else Path(settings.PERSIST_DIRECTORY) / "vectorstore"
        output_file = Path(args.stats_file) if args.stats_file else vectorstore_dir / "index_statistics.json"
        
        # Handle different commands
        if args.command == "index":
            return index_embeddings(
                embeddings_file=embeddings_file,
                vectorstore_dir=vectorstore_dir,
                batch_size=args.batch_size,
                collection_name=args.collection_name,
            )
        
        elif args.command == "reload":
            return reload_index(
                vectorstore_dir=vectorstore_dir,
                collection_name=args.collection_name,
            )
        
        elif args.command == "stats":
            return export_statistics(
                vectorstore_dir=vectorstore_dir,
                output_file=output_file,
                collection_name=args.collection_name,
            )
        
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Index embeddings into ChromaDB vector store"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index embeddings into vector store")
    index_parser.add_argument("--embeddings-file", help="Path to embeddings JSON file")
    index_parser.add_argument("--vectorstore-dir", help="Vector store directory")
    index_parser.add_argument("--batch-size", type=int, default=100, help="Batch size for indexing")
    index_parser.add_argument("--collection-name", default="college_faq", help="Collection name")
    
    # Reload command
    reload_parser = subparsers.add_parser("reload", help="Reload index from disk")
    reload_parser.add_argument("--vectorstore-dir", help="Vector store directory")
    reload_parser.add_argument("--collection-name", default="college_faq", help="Collection name")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Generate index statistics")
    stats_parser.add_argument("--vectorstore-dir", help="Vector store directory")
    stats_parser.add_argument("--stats-file", help="Output statistics file")
    stats_parser.add_argument("--collection-name", default="college_faq", help="Collection name")
    
    # Default to index command if no subcommand
    args = parser.parse_args()
    if not args.command:
        args.command = "index"
        args.embeddings_file = None
        args.vectorstore_dir = None
        args.batch_size = 100
        args.collection_name = "college_faq"
    
    sys.exit(main(args))
