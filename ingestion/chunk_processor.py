"""
Intelligent document chunker with structure preservation.

Uses RecursiveCharacterTextSplitter with metadata preservation.
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingestion.chunk_models import DocumentChunk
from core.logger import get_logger

logger = get_logger(__name__)


class StructureDetector:
    """
    Detects document structure (headings, tables, lists).
    
    Identifies structural elements to preserve during chunking.
    """

    @staticmethod
    def detect_heading(text: str) -> Optional[Tuple[int, str]]:
        """
        Detect if text starts with a heading.
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (heading_level, heading_text) or None
        """
        match = re.match(r'^(#{1,6})\s+(.+)$', text.strip(), re.MULTILINE)
        if match:
            level = len(match.group(1))
            text_content = match.group(2).strip()
            return (level, text_content)
        return None

    @staticmethod
    def contains_table(text: str) -> bool:
        """Check if text contains markdown table."""
        return bool(re.search(r'\|\s*.*\s*\|', text))

    @staticmethod
    def contains_list(text: str) -> bool:
        """Check if text contains bullet or ordered list."""
        bullet_pattern = r'^\s*[-*+]\s+.+'
        ordered_pattern = r'^\s*\d+\.\s+.+'
        return bool(
            re.search(bullet_pattern, text, re.MULTILINE) or
            re.search(ordered_pattern, text, re.MULTILINE)
        )

    @staticmethod
    def contains_code(text: str) -> bool:
        """Check if text contains code block."""
        return bool(re.search(r'```|<code>|    [^ ]', text))


class IntelligentChunker:
    """
    Intelligent document chunker with structure preservation.
    
    Uses RecursiveCharacterTextSplitter while preserving
    headings, tables, and lists.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Separators for recursive splitting (most important first)
        self.separators = [
            "\n## ",      # H2 headings
            "\n### ",     # H3 headings
            "\n#### ",    # H4 headings
            "\n\n",       # Paragraph breaks
            "\n",         # Line breaks
            " ",          # Word breaks
            "",           # Character level
        ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )
        
        self.detector = StructureDetector()
        self.chunk_counter = 0

    def chunk(
        self,
        document: Dict[str, Any],
    ) -> List[DocumentChunk]:
        """
        Chunk a document while preserving structure.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            content = document.get("content", "")
            if not content.strip():
                logger.warning(f"Empty content for document {document.get('document_id')}")
                return []
            
            # Split using langchain
            text_chunks = self.splitter.split_text(content)
            
            # Create DocumentChunk objects with metadata
            chunks = []
            for i, text in enumerate(text_chunks):
                chunk = self._create_chunk(
                    text=text,
                    document=document,
                    chunk_index=i,
                    total_chunks=len(text_chunks),
                )
                if chunk:
                    chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks from document {document.get('document_id')}")
            return chunks
        
        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            return []

    def _create_chunk(
        self,
        text: str,
        document: Dict[str, Any],
        chunk_index: int,
        total_chunks: int,
    ) -> Optional[DocumentChunk]:
        """
        Create a DocumentChunk with metadata.
        
        Args:
            text: Chunk text
            document: Source document
            chunk_index: Chunk position
            total_chunks: Total chunks in document
            
        Returns:
            DocumentChunk object or None
        """
        try:
            # Calculate character statistics
            char_count = len(text)
            word_count = len(text.split())
            line_count = text.count('\n') + 1
            
            # Detect structure
            heading_info = self.detector.detect_heading(text)
            heading_level = heading_info[0] if heading_info else None
            heading_text = heading_info[1] if heading_info else None
            
            # Create chunk ID
            chunk_id = f"chunk-{uuid.uuid4().hex[:12]}"
            
            # Get start and end character positions
            # (simplified - would need document tracking for accuracy)
            start_char = chunk_index * (self.chunk_size - self.chunk_overlap)
            end_char = start_char + char_count
            
            return DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.get("document_id", ""),
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                content=text,
                source_url=document.get("source_url", ""),
                source_type=document.get("source_type", "webpage"),
                document_title=document.get("title", ""),
                page_title=document.get("page_title", ""),
                section=document.get("section", "general"),
                heading=heading_text,
                heading_level=heading_level,
                character_count=char_count,
                word_count=word_count,
                line_count=line_count,
                contains_table=self.detector.contains_table(text),
                contains_list=self.detector.contains_list(text),
                contains_code=self.detector.contains_code(text),
                start_char=start_char,
                end_char=end_char,
                keywords=document.get("keywords", []),
                tags=document.get("tags", []),
                created_at=datetime.utcnow(),
            )
        
        except Exception as e:
            logger.error(f"Error creating chunk: {e}")
            return None

    def get_statistics(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Generate statistics from chunks.
        
        Args:
            chunks: List of chunks
            
        Returns:
            Statistics dictionary
        """
        try:
            if not chunks:
                return {
                    "total_chunks": 0,
                    "avg_size": 0,
                    "min_size": 0,
                    "max_size": 0,
                }
            
            sizes = [c.character_count for c in chunks]
            
            chunks_with_tables = sum(1 for c in chunks if c.contains_table)
            chunks_with_lists = sum(1 for c in chunks if c.contains_list)
            chunks_with_code = sum(1 for c in chunks if c.contains_code)
            total_words = sum(c.word_count for c in chunks)
            
            return {
                "total_chunks": len(chunks),
                "avg_size": sum(sizes) / len(sizes),
                "min_size": min(sizes),
                "max_size": max(sizes),
                "chunks_with_tables": chunks_with_tables,
                "chunks_with_lists": chunks_with_lists,
                "chunks_with_code": chunks_with_code,
                "total_words": total_words,
                "total_chars": sum(c.character_count for c in chunks),
            }
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
