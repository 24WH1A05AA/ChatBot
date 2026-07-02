"""
Markdown conversion and formatting.

Converts parsed HTML content into clean, well-formatted markdown.
"""

from typing import Dict, List, Any, Optional
import re
from core.logger import get_logger

logger = get_logger(__name__)


class HeadingNormalizer:
    """Normalizes heading levels and formatting."""

    def __init__(self) -> None:
        """Initialize the heading normalizer."""
        pass

    def normalize_headings(self, headings: List[Dict[str, Any]]) -> str:
        """
        Convert headings to markdown format.
        
        Args:
            headings: List of heading objects with level and text
            
        Returns:
            Markdown formatted headings
        """
        try:
            if not headings:
                return ""
            
            markdown = []
            for heading in headings:
                level = int(heading.get("level", 1))
                text = heading.get("text", "").strip()
                
                if text:
                    # Limit heading levels to H6
                    level = min(level, 6)
                    markdown.append(f"{'#' * level} {text}\n")
            
            return "".join(markdown)
        
        except Exception as e:
            logger.warning(f"Error normalizing headings: {e}")
            return ""


class TableConverter:
    """Converts tables to markdown format."""

    def __init__(self) -> None:
        """Initialize the table converter."""
        pass

    def convert_tables(self, tables: List[Dict[str, Any]]) -> str:
        """
        Convert tables to markdown format.
        
        Args:
            tables: List of table objects
            
        Returns:
            Markdown formatted tables
        """
        try:
            if not tables:
                return ""
            
            markdown = []
            for table in tables:
                rows = table.get("rows", [])
                if not rows:
                    continue
                
                markdown.append("\n")
                
                # Process rows
                for i, row in enumerate(rows):
                    # Clean cells
                    cells = [str(cell).strip() for cell in row]
                    markdown.append("| " + " | ".join(cells) + " |\n")
                    
                    # Add separator after header row
                    if i == 0:
                        sep = "| " + " | ".join(["---"] * len(cells)) + " |\n"
                        markdown.append(sep)
                
                markdown.append("\n")
            
            return "".join(markdown)
        
        except Exception as e:
            logger.warning(f"Error converting tables: {e}")
            return ""


class ListConverter:
    """Converts lists to markdown format."""

    def __init__(self) -> None:
        """Initialize the list converter."""
        pass

    def convert_lists(self, lists: List[Dict[str, Any]]) -> str:
        """
        Convert lists to markdown format.
        
        Args:
            lists: List of list objects
            
        Returns:
            Markdown formatted lists
        """
        try:
            if not lists:
                return ""
            
            markdown = []
            for lst in lists:
                list_type = lst.get("type", "ul")
                items = lst.get("items", [])
                
                if not items:
                    continue
                
                markdown.append("\n")
                
                for item in items:
                    if list_type == "ol":
                        markdown.append(f"1. {item}\n")
                    else:  # ul
                        markdown.append(f"- {item}\n")
                
                markdown.append("\n")
            
            return "".join(markdown)
        
        except Exception as e:
            logger.warning(f"Error converting lists: {e}")
            return ""


class LinkConverter:
    """Converts links to markdown format."""

    def __init__(self) -> None:
        """Initialize the link converter."""
        pass

    def convert_links(self, links: List[Dict[str, Any]]) -> str:
        """
        Convert links section to markdown.
        
        Args:
            links: List of link objects
            
        Returns:
            Markdown formatted links section
        """
        try:
            if not links:
                return ""
            
            markdown = ["\n## Related Links\n\n"]
            
            for link in links:
                url = link.get("url", "")
                text = link.get("text", "Link").strip()
                title = link.get("title", "")
                
                if not url:
                    continue
                
                # Skip external social media and tracking links
                if any(domain in url.lower() for domain in 
                       ['facebook.com', 'twitter.com', 'instagram.com', 'analytics', 'tracking']):
                    continue
                
                if title:
                    markdown.append(f"- [{text}]({url}) - {title}\n")
                else:
                    markdown.append(f"- [{text}]({url})\n")
            
            return "".join(markdown) if len(markdown) > 1 else ""
        
        except Exception as e:
            logger.warning(f"Error converting links: {e}")
            return ""


class ImageConverter:
    """Converts images to markdown format."""

    def __init__(self) -> None:
        """Initialize the image converter."""
        pass

    def convert_images(self, images: List[Dict[str, Any]]) -> str:
        """
        Convert images to markdown format.
        
        Args:
            images: List of image objects
            
        Returns:
            Markdown formatted images
        """
        try:
            if not images:
                return ""
            
            markdown = ["\n## Images\n\n"]
            
            for image in images:
                src = image.get("src", "")
                alt = image.get("alt", "Image")
                title = image.get("title", "")
                
                if not src:
                    continue
                
                if title:
                    markdown.append(f"![{alt}]({src} \"{title}\")\n\n")
                else:
                    markdown.append(f"![{alt}]({src})\n\n")
            
            return "".join(markdown) if len(markdown) > 1 else ""
        
        except Exception as e:
            logger.warning(f"Error converting images: {e}")
            return ""


class MarkdownFormatter:
    """
    Formats parsed content into clean markdown.
    
    Handles heading hierarchy, tables, lists, links, and images.
    """

    def __init__(self) -> None:
        """Initialize the markdown formatter."""
        self.heading_normalizer = HeadingNormalizer()
        self.table_converter = TableConverter()
        self.list_converter = ListConverter()
        self.link_converter = LinkConverter()
        self.image_converter = ImageConverter()

    def format_page(self, page_data: Dict[str, Any]) -> str:
        """
        Format entire page into markdown.
        
        Args:
            page_data: Parsed page data
            
        Returns:
            Complete markdown formatted page
        """
        try:
            markdown_parts = []
            
            # Title
            title = page_data.get("title", "")
            if title:
                markdown_parts.append(f"# {title}\n\n")
            
            # Description
            description = page_data.get("description", "")
            if description:
                markdown_parts.append(f"*{description}*\n\n")
            
            # Keywords
            keywords = page_data.get("keywords", [])
            if keywords:
                markdown_parts.append(f"**Tags:** {', '.join(keywords)}\n\n")
            
            # Breadcrumb
            breadcrumb = page_data.get("breadcrumb", [])
            if breadcrumb:
                markdown_parts.append(f"**Path:** {' > '.join(breadcrumb)}\n\n")
            
            # Main content (body already in markdown)
            body = page_data.get("body", "")
            if body:
                markdown_parts.append(f"{body}\n\n")
            
            # Headings (if not in body)
            headings = page_data.get("headings", [])
            if headings and not body:
                markdown_parts.append(self.heading_normalizer.normalize_headings(headings))
                markdown_parts.append("\n")
            
            # Tables
            tables = page_data.get("tables", [])
            if tables:
                markdown_parts.append(self.table_converter.convert_tables(tables))
            
            # Lists
            lists = page_data.get("lists", [])
            if lists:
                markdown_parts.append(self.list_converter.convert_lists(lists))
            
            # Images
            images = page_data.get("images", [])
            if images:
                markdown_parts.append(self.image_converter.convert_images(images))
            
            # Links
            links = page_data.get("links", [])
            if links:
                markdown_parts.append(self.link_converter.convert_links(links))
            
            # Metadata section
            markdown_parts.append("\n---\n\n")
            markdown_parts.append(self._format_metadata_section(page_data))
            
            result = "".join(markdown_parts)
            
            # Final cleanup
            result = re.sub(r"\n{3,}", "\n\n", result)
            
            return result.strip()
        
        except Exception as e:
            logger.error(f"Error formatting markdown: {e}")
            return ""

    def _format_metadata_section(self, page_data: Dict[str, Any]) -> str:
        """Format metadata section."""
        try:
            metadata = page_data.get("metadata", {})
            metadata_section = ["## Page Metadata\n\n"]
            
            if metadata.get("author"):
                metadata_section.append(f"**Author:** {metadata['author']}\n")
            
            if metadata.get("published_date"):
                metadata_section.append(f"**Published:** {metadata['published_date']}\n")
            
            if metadata.get("modified_date"):
                metadata_section.append(f"**Modified:** {metadata['modified_date']}\n")
            
            if metadata.get("language"):
                metadata_section.append(f"**Language:** {metadata['language']}\n")
            
            if metadata.get("og_title"):
                metadata_section.append(f"**OG Title:** {metadata['og_title']}\n")
            
            if metadata.get("og_description"):
                metadata_section.append(f"**OG Description:** {metadata['og_description']}\n")
            
            return "".join(metadata_section)
        
        except Exception as e:
            logger.warning(f"Error formatting metadata: {e}")
            return ""
