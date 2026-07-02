"""
Knowledge base format generators (JSON, Markdown, CSV).

Generates knowledge base in multiple formats.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any

from core.logger import get_logger

logger = get_logger(__name__)


class JSONKnowledgeBaseGenerator:
    """Generates knowledge base in JSON format."""

    def generate(self, documents: List[Dict[str, Any]], output_path: Path) -> bool:
        """
        Generate JSON knowledge base.
        
        Args:
            documents: List of knowledge base documents
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Generating JSON knowledge base with {len(documents)} documents")
            
            # Prepare output structure
            kb_data = {
                "version": "1.0",
                "generated_at": str(__import__('datetime').datetime.utcnow().isoformat()),
                "total_documents": len(documents),
                "documents": documents,
            }
            
            # Write JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(kb_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Generated JSON knowledge base: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            return False


class MarkdownKnowledgeBaseGenerator:
    """Generates knowledge base in Markdown format."""

    def generate(self, documents: List[Dict[str, Any]], output_path: Path) -> bool:
        """
        Generate Markdown knowledge base.
        
        Args:
            documents: List of knowledge base documents
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Generating Markdown knowledge base with {len(documents)} documents")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("# College FAQ Chatbot Knowledge Base\n\n")
                f.write(f"**Total Documents:** {len(documents)}\n")
                f.write(f"**Generated:** {__import__('datetime').datetime.utcnow().isoformat()}\n\n")
                
                # Table of contents by section
                sections = {}
                for doc in documents:
                    section = doc.get("section", "general")
                    if section not in sections:
                        sections[section] = []
                    sections[section].append(doc)
                
                f.write("## Table of Contents\n\n")
                for section in sorted(sections.keys()):
                    f.write(f"- [{section.title()}](#section-{section})\n")
                f.write("\n---\n\n")
                
                # Documents by section
                for section in sorted(sections.keys()):
                    f.write(f"## Section: {section.title()}\n\n")
                    
                    for doc in sections[section]:
                        self._write_document_markdown(f, doc)
                    
                    f.write("\n---\n\n")
            
            logger.info(f"Generated Markdown knowledge base: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error generating Markdown: {e}")
            return False

    def _write_document_markdown(self, f, doc: Dict[str, Any]) -> None:
        """Write single document in markdown format."""
        # Document header
        f.write(f"### {doc.get('title', 'Untitled')}\n\n")
        
        # Metadata
        f.write(f"**ID:** `{doc.get('document_id', 'N/A')}`\n")
        f.write(f"**URL:** [{doc.get('source_url', '#')}]({doc.get('source_url', '#')})\n")
        f.write(f"**Type:** {doc.get('document_type', 'content')}\n")
        f.write(f"**Section:** {doc.get('section', 'general')}\n")
        
        if doc.get('department'):
            f.write(f"**Department:** {doc.get('department')}\n")
        
        if doc.get('author'):
            f.write(f"**Author:** {doc.get('author')}\n")
        
        f.write(f"**Crawled:** {doc.get('crawled_at', 'N/A')}\n\n")
        
        # Content
        if doc.get('content'):
            f.write(doc['content'])
        f.write("\n\n")


class CSVKnowledgeBaseGenerator:
    """Generates knowledge base in CSV format."""

    def generate(self, documents: List[Dict[str, Any]], output_path: Path) -> bool:
        """
        Generate CSV knowledge base.
        
        Args:
            documents: List of knowledge base documents
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Generating CSV knowledge base with {len(documents)} documents")
            
            # Prepare rows
            rows = []
            for doc in documents:
                row = {
                    "document_id": doc.get("document_id", ""),
                    "title": doc.get("title", ""),
                    "page_title": doc.get("page_title", ""),
                    "source_url": doc.get("source_url", ""),
                    "source_type": doc.get("source_type", ""),
                    "section": doc.get("section", ""),
                    "subsection": doc.get("subsection", ""),
                    "department": doc.get("department", ""),
                    "document_type": doc.get("document_type", ""),
                    "keywords": ";".join(doc.get("keywords", [])),
                    "tags": ";".join(doc.get("tags", [])),
                    "content_length": doc.get("content_length", 0),
                    "word_count": doc.get("word_count", 0),
                    "created_at": doc.get("created_at", ""),
                    "crawled_at": doc.get("crawled_at", ""),
                    "last_modified": doc.get("last_modified", ""),
                    "quality_score": doc.get("quality_score", ""),
                    "author": doc.get("author", ""),
                    "language": doc.get("language", "en"),
                }
                rows.append(row)
            
            # Write CSV
            if rows:
                fieldnames = rows[0].keys()
                
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            
            logger.info(f"Generated CSV knowledge base: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            return False
