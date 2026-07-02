"""
Document loader for knowledge base generation.

Loads cleaned pages and downloaded documents.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.logger import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    """
    Loads documents from cleaned pages and downloaded files.
    
    Reads all available cleaned content and converts to knowledge base format.
    """

    def __init__(self) -> None:
        """Initialize the document loader."""
        pass

    def load_cleaned_pages(self, cleaned_dir: Path) -> List[Dict[str, Any]]:
        """
        Load all cleaned pages.
        
        Args:
            cleaned_dir: Directory with cleaned pages
            
        Returns:
            List of cleaned page dictionaries
        """
        try:
            documents = []
            json_files = list(cleaned_dir.glob("*.json"))
            
            logger.info(f"Loading {len(json_files)} cleaned pages from {cleaned_dir}")
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                        
                        # Add source indicator
                        doc['_source'] = 'cleaned_page'
                        doc['_file'] = json_file.name
                        
                        documents.append(doc)
                
                except Exception as e:
                    logger.warning(f"Error loading {json_file}: {e}")
            
            logger.info(f"Loaded {len(documents)} cleaned pages")
            return documents
        
        except Exception as e:
            logger.error(f"Error loading cleaned pages: {e}")
            return []

    def load_downloaded_documents(self, documents_dir: Path) -> List[Dict[str, Any]]:
        """
        Load all downloaded documents.
        
        Args:
            documents_dir: Directory with downloaded documents
            
        Returns:
            List of document dictionaries
        """
        try:
            documents = []
            
            if not documents_dir.exists():
                logger.debug(f"Documents directory not found: {documents_dir}")
                return []
            
            json_files = list(documents_dir.glob("*.json"))
            
            logger.info(f"Loading {len(json_files)} documents from {documents_dir}")
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                        
                        # Add source indicator
                        doc['_source'] = 'downloaded_document'
                        doc['_file'] = json_file.name
                        
                        documents.append(doc)
                
                except Exception as e:
                    logger.warning(f"Error loading {json_file}: {e}")
            
            logger.info(f"Loaded {len(documents)} downloaded documents")
            return documents
        
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []

    def get_document_text(self, doc: Dict[str, Any]) -> str:
        """
        Extract full text from document.
        
        Args:
            doc: Document dictionary
            
        Returns:
            Full text content
        """
        try:
            # Try markdown field first (cleaned pages)
            if 'markdown' in doc:
                return doc['markdown']
            
            # Try body field
            if 'body' in doc:
                return doc['body']
            
            # Try content field
            if 'content' in doc:
                return doc['content']
            
            return ""
        
        except Exception:
            return ""

    def extract_headings(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract headings from document.
        
        Args:
            doc: Document dictionary
            
        Returns:
            List of heading dictionaries
        """
        try:
            if 'headings' in doc and doc['headings']:
                return doc['headings']
            
            return []
        
        except Exception:
            return []
