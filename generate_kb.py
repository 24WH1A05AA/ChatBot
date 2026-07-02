"""
CLI script to generate knowledge base.

Usage:
    python generate_kb.py
    python generate_kb.py --cleaned-dir ./knowledge_base/cleaned --output-dir ./kb_output
"""

import sys
import argparse
from pathlib import Path

from config import get_settings
from core.logger import setup_logging, get_logger
from ingestion.kb_merger import KnowledgeBaseMerger

logger = get_logger(__name__)


def main(args: argparse.Namespace) -> int:
    """
    Generate knowledge base.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    try:
        settings = get_settings()
        
        # Setup logging
        setup_logging(
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE,
            is_debug=settings.DEBUG,
        )
        
        logger.info("=== Knowledge Base Generator ===")
        
        # Determine directories
        cleaned_dir = Path(args.cleaned_dir) if args.cleaned_dir else Path(settings.PERSIST_DIRECTORY) / "cleaned"
        documents_dir = Path(args.documents_dir) if args.documents_dir else Path(settings.PERSIST_DIRECTORY) / "documents"
        output_dir = Path(args.output_dir) if args.output_dir else Path(settings.PERSIST_DIRECTORY) / "merged"
        
        logger.info(f"Cleaned pages directory: {cleaned_dir}")
        logger.info(f"Documents directory: {documents_dir}")
        logger.info(f"Output directory: {output_dir}")
        
        # Verify cleaned directory exists
        if not cleaned_dir.exists():
            logger.error(f"Cleaned pages directory not found: {cleaned_dir}")
            logger.info("Run: python clean_pages.py")
            return 1
        
        # Run merger
        merger = KnowledgeBaseMerger()
        
        result = merger.merge(
            cleaned_pages_dir=cleaned_dir,
            documents_dir=documents_dir,
            output_dir=output_dir,
            include_documents=args.include_documents,
        )
        
        # Print results
        logger.info("\n=== Generation Results ===")
        logger.info(f"Total Documents: {result.total_documents}")
        logger.info(f"  From Pages: {result.documents_from_pages}")
        logger.info(f"  From Files: {result.documents_from_files}")
        logger.info(f"Total Words: {result.total_words:,}")
        logger.info(f"Total Characters: {result.total_characters:,}")
        logger.info(f"Sections Found: {', '.join(result.sections_found)}")
        logger.info(f"Generation Time: {result.generation_time:.1f} seconds")
        
        logger.info(f"\nGenerated files:")
        logger.info(f"  JSON: {result.json_file}")
        logger.info(f"  Markdown: {result.markdown_file}")
        logger.info(f"  CSV: {result.csv_file}")
        
        logger.info("\nKnowledge base generated successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate knowledge base from cleaned pages and documents"
    )
    
    parser.add_argument(
        "--cleaned-dir",
        type=str,
        help="Directory with cleaned pages (default: knowledge_base/cleaned)",
    )
    
    parser.add_argument(
        "--documents-dir",
        type=str,
        help="Directory with downloaded documents (default: knowledge_base/documents)",
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for knowledge base (default: knowledge_base/merged)",
    )
    
    parser.add_argument(
        "--skip-documents",
        action="store_false",
        dest="include_documents",
        help="Skip downloaded documents",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    exit_code = main(args)
    sys.exit(exit_code)
