"""
File document converter to markdown format.

Converts extracted file content to markdown with metadata.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from crawler.file_extractor import FileExtractor
from core.logger import get_logger

logger = get_logger(__name__)


class FileDocumentConverter:
    """
    Converts downloaded files to markdown format.
    
    Extracts content and creates markdown documents with metadata.
    """

    def __init__(self) -> None:
        """Initialize the file document converter."""
        self.extractor = FileExtractor()

    def convert(
        self,
        file_path: Path,
        file_type: str,
        file_info: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Convert file to markdown.
        
        Args:
            file_path: Path to file
            file_type: File type (pdf, docx, txt, csv)
            file_info: File information dictionary
            
        Returns:
            Dictionary with markdown content and metadata
        """
        try:
            logger.info(f"Converting to markdown: {file_path}")
            
            # Extract content
            content = self.extractor.extract(file_path, file_type)
            if not content:
                logger.warning(f"No content extracted from {file_path}")
                return None
            
            # Extract metadata
            metadata = self.extractor.extract_metadata(file_path, file_type)
            
            # Create markdown
            markdown = self._create_markdown(
                file_info,
                content,
                metadata,
            )
            
            return {
                "url": file_info.get("url"),
                "filename": file_info.get("filename"),
                "file_type": file_type,
                "title": metadata.get("title", file_info.get("filename")),
                "source_page": file_info.get("source_page"),
                "markdown": markdown,
                "metadata": metadata,
                "file_info": file_info,
                "converted_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Error converting file: {e}")
            return None

    def _create_markdown(
        self,
        file_info: Dict[str, Any],
        content: str,
        metadata: Dict[str, Any],
    ) -> str:
        """
        Create markdown from file content.
        
        Args:
            file_info: File information
            content: Extracted content
            metadata: File metadata
            
        Returns:
            Markdown formatted string
        """
        try:
            markdown_parts = []
            
            # Title
            filename = file_info.get("filename", "Document")
            markdown_parts.append(f"# {filename}\n")
            
            # File info
            markdown_parts.append("## Document Information\n")
            
            file_type = file_info.get("file_type", "unknown").upper()
            file_size = self._format_size(file_info.get("file_size", 0))
            markdown_parts.append(f"- **Type:** {file_type}")
            markdown_parts.append(f"- **Size:** {file_size}")
            markdown_parts.append(f"- **URL:** [{file_info.get('url')}]({file_info.get('url')})")
            markdown_parts.append(f"- **Source Page:** [{file_info.get('source_page')}]({file_info.get('source_page')})")
            markdown_parts.append("")
            
            # Metadata section
            if metadata:
                markdown_parts.append("## Document Metadata\n")
                
                if metadata.get("title") and metadata["title"] != filename:
                    markdown_parts.append(f"- **Title:** {metadata['title']}")
                
                if metadata.get("author"):
                    markdown_parts.append(f"- **Author:** {metadata['author']}")
                
                if metadata.get("created"):
                    markdown_parts.append(f"- **Created:** {metadata['created']}")
                
                if metadata.get("modified"):
                    markdown_parts.append(f"- **Modified:** {metadata['modified']}")
                
                if metadata.get("pages"):
                    markdown_parts.append(f"- **Pages:** {metadata['pages']}")
                
                if metadata.get("paragraph_count"):
                    markdown_parts.append(f"- **Paragraphs:** {metadata['paragraph_count']}")
                
                if metadata.get("table_count"):
                    markdown_parts.append(f"- **Tables:** {metadata['table_count']}")
                
                if metadata.get("row_count"):
                    markdown_parts.append(f"- **Rows:** {metadata['row_count']}")
                
                if metadata.get("column_count"):
                    markdown_parts.append(f"- **Columns:** {metadata['column_count']}")
                
                markdown_parts.append("")
            
            # Content section
            markdown_parts.append("## Content\n")
            markdown_parts.append(content)
            
            return "\n".join(markdown_parts)
        
        except Exception as e:
            logger.error(f"Error creating markdown: {e}")
            return ""

    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size for display.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def convert_batch(
        self,
        files: list,
        output_dir: Path,
    ) -> list:
        """
        Convert multiple files to markdown.
        
        Args:
            files: List of file dictionaries with 'local_path' and 'file_type'
            output_dir: Directory to save converted markdown files
            
        Returns:
            List of converted documents
        """
        try:
            converted = []
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for file_info in files:
                file_path = Path(file_info.get("local_path"))
                file_type = file_info.get("file_type")
                
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                # Convert
                doc = self.convert(file_path, file_type, file_info)
                
                if doc:
                    # Save markdown
                    md_filename = file_path.stem + ".md"
                    md_path = output_dir / md_filename
                    
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(doc["markdown"])
                    
                    doc["markdown_path"] = str(md_path)
                    converted.append(doc)
                    
                    logger.info(f"Converted: {md_path}")
            
            return converted
        
        except Exception as e:
            logger.error(f"Error in batch conversion: {e}")
            return []
