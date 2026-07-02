"""
Document loading and preprocessing.

Loads documents from various sources and formats
with support for metadata preservation.
"""

from typing import Optional, List


class DocumentLoader:
    """
    Loads documents from various sources.
    
    Supports markdown, plain text, and PDF files
    with metadata preservation.
    """

    def __init__(self) -> None:
        """Initialize the document loader."""
        pass

    def load(self, source: str) -> List[dict]:
        """
        Load documents from a source.
        
        Args:
            source: File path or directory
            
        Returns:
            List of loaded documents with content and metadata
        """
        pass

    def load_file(self, file_path: str) -> dict:
        """
        Load a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Document dictionary
        """
        pass

    def load_directory(self, directory: str) -> List[dict]:
        """
        Load all documents from a directory.
        
        Args:
            directory: Directory path
            
        Returns:
            List of loaded documents
        """
        pass
