"""
Knowledge base orchestrator - main merger and generator.

Coordinates loading, merging, and generating knowledge base.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ingestion.kb_models import KnowledgeBaseDocument, KnowledgeBaseMergeResult
from ingestion.kb_loader import DocumentLoader
from ingestion.kb_metadata import MetadataExtractor
from ingestion.kb_generators import (
    JSONKnowledgeBaseGenerator,
    MarkdownKnowledgeBaseGenerator,
    CSVKnowledgeBaseGenerator,
)
from core.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseMerger:
    """
    Merges cleaned pages and documents into unified knowledge base.
    
    Orchestrates loading, enrichment, and generation in multiple formats.
    """

    def __init__(self) -> None:
        """Initialize the knowledge base merger."""
        self.loader = DocumentLoader()
        self.metadata_extractor = MetadataExtractor()
        
        self.json_generator = JSONKnowledgeBaseGenerator()
        self.markdown_generator = MarkdownKnowledgeBaseGenerator()
        self.csv_generator = CSVKnowledgeBaseGenerator()

    def merge(
        self,
        cleaned_pages_dir: Path,
        documents_dir: Optional[Path] = None,
        output_dir: Path = Path("knowledge_base/merged"),
        include_documents: bool = True,
    ) -> KnowledgeBaseMergeResult:
        """
        Merge cleaned pages and documents into knowledge base.
        
        Args:
            cleaned_pages_dir: Directory with cleaned pages
            documents_dir: Directory with downloaded documents
            output_dir: Output directory
            include_documents: Whether to include downloaded documents
            
        Returns:
            Merge result with statistics
        """
        start_time = time.time()
        
        try:
            logger.info("=== Starting Knowledge Base Generation ===")
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Load documents
            logger.info("Loading cleaned pages...")
            cleaned_pages = self.loader.load_cleaned_pages(cleaned_pages_dir)
            
            logger.info(f"Loading downloaded documents...")
            downloaded_docs = []
            if include_documents and documents_dir and documents_dir.exists():
                downloaded_docs = self.loader.load_downloaded_documents(documents_dir)
            
            # Merge documents
            all_raw_docs = cleaned_pages + downloaded_docs
            logger.info(f"Total documents to process: {len(all_raw_docs)}")
            
            # Enrich with metadata
            logger.info("Enriching metadata...")
            documents = self._enrich_documents(all_raw_docs)
            
            # Generate outputs
            logger.info("Generating output formats...")
            json_path = output_dir / "knowledge.json"
            markdown_path = output_dir / "knowledge.md"
            csv_path = output_dir / "knowledge.csv"
            
            self.json_generator.generate(documents, json_path)
            self.markdown_generator.generate(documents, markdown_path)
            self.csv_generator.generate(documents, csv_path)
            
            # Calculate statistics
            stats = self._calculate_statistics(documents)
            
            elapsed = time.time() - start_time
            
            logger.info(f"=== Knowledge Base Generation Complete ({elapsed:.1f}s) ===")
            logger.info(f"Total documents: {len(documents)}")
            logger.info(f"Total words: {stats['total_words']}")
            logger.info(f"Sections: {', '.join(stats['sections'])}")
            
            return KnowledgeBaseMergeResult(
                total_documents=len(documents),
                documents_from_pages=len(cleaned_pages),
                documents_from_files=len(downloaded_docs),
                json_file=str(json_path),
                markdown_file=str(markdown_path),
                csv_file=str(csv_path),
                total_words=stats['total_words'],
                total_characters=stats['total_characters'],
                sections_found=stats['sections'],
                generation_time=elapsed,
            )
        
        except Exception as e:
            logger.error(f"Error during merge: {e}", exc_info=True)
            raise

    def _enrich_documents(self, raw_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich raw documents with metadata.
        
        Args:
            raw_docs: Raw documents from loader
            
        Returns:
            Enriched documents
        """
        try:
            enriched = []
            
            for i, raw_doc in enumerate(raw_docs):
                try:
                    # Extract metadata
                    metadata = self.metadata_extractor.extract(raw_doc)
                    
                    # Get content
                    content = self.loader.get_document_text(raw_doc)
                    headings = self.loader.extract_headings(raw_doc)
                    
                    # Create enriched document
                    enriched_doc = {
                        **metadata,
                        "content": content,
                        "headings": headings,
                    }
                    
                    enriched.append(enriched_doc)
                    
                    if (i + 1) % 50 == 0:
                        logger.debug(f"Enriched {i + 1}/{len(raw_docs)} documents")
                
                except Exception as e:
                    logger.warning(f"Error enriching document {i}: {e}")
                    continue
            
            logger.info(f"Successfully enriched {len(enriched)} documents")
            return enriched
        
        except Exception as e:
            logger.error(f"Error in enrichment: {e}")
            return []

    def _calculate_statistics(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for knowledge base.
        
        Args:
            documents: List of enriched documents
            
        Returns:
            Statistics dictionary
        """
        try:
            total_words = sum(d.get("word_count", 0) for d in documents)
            total_chars = sum(d.get("content_length", 0) for d in documents)
            
            sections = set()
            for doc in documents:
                section = doc.get("section", "general")
                if section:
                    sections.add(section)
            
            return {
                "total_words": total_words,
                "total_characters": total_chars,
                "sections": sorted(list(sections)),
                "avg_document_size": total_chars / max(len(documents), 1),
                "avg_word_count": total_words / max(len(documents), 1),
            }
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {
                "total_words": 0,
                "total_characters": 0,
                "sections": [],
            }
