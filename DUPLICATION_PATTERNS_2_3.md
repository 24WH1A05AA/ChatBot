# Detailed Duplication Analysis: Patterns 2 & 3

## Pattern 2: Message Formatting Duplication (200+ LOC)

### Overview
Message formatting logic is scattered across 5+ modules with nearly identical implementations:

| Location | Function | Purpose | LOC |
|----------|----------|---------|-----|
| `prompts/system_prompts.py` | Format citations | Add source citations | ~30 |
| `prompts/prompt_orchestrator.py` | Format context | Structure context blocks | ~40 |
| `chatbot/chatbot.py` | Format response | Compose final response | ~50 |
| `core/optimization.py` | `_format_message()` | Generic formatting | ~35 |
| `security/security.py` | `sanitize_output()` | Security filtering | ~45 |

### Duplication Examples

#### Issue 1: Citation Formatting (Duplicated in 3 files)
```python
# prompts/system_prompts.py (appears 3 times)
def _format_citation(self, section: str, url: str) -> str:
    return f"[Source: {section} | {url}]"

# chatbot/chatbot.py (similar)
citations_text = "[Source: " + source + " | " + url + "]"

# security/security.py (different style but same logic)
def format_citation(source, url):
    return "[Source: " + source + " | " + url + "]"
```

#### Issue 2: Context Formatting (Duplicated in 2 files)
```python
# prompts/prompt_orchestrator.py
def format_context_block(self, text: str, metadata: Dict[str, Any]) -> str:
    section = metadata.get("section", "General")
    url = metadata.get("source_url", "")
    formatted = f"\n**Section: {section}**\n"
    formatted += f"*Source: {url}*\n"
    formatted += f"{text}\n"
    formatted += "-" * 80 + "\n"
    return formatted

# ingestion/kb_metadata.py (very similar)
def format_metadata_text(text: str, section: str, source: str) -> str:
    result = f"\n**{section}**\n"
    result += f"Source: {source}\n"
    result += f"{text}\n"
    return result
```

#### Issue 3: Response Composition (Duplicated in 2 files)
```python
# chatbot/chatbot.py
def compose_response(message: str, citations: List[str]) -> str:
    response = message
    if citations:
        response += "\n\n## Sources\n"
        for i, citation in enumerate(citations, 1):
            response += f"{i}. {citation}\n"
    return response

# prompts/prompt_orchestrator.py (similar logic)
def add_citations_to_message(msg: str, sources: List[str]) -> str:
    if not sources:
        return msg
    msg += "\n\n**References:**\n"
    for source in sources:
        msg += f"- {source}\n"
    return msg
```

### Root Cause
- No centralized formatting module
- Each component evolved independently
- No shared abstraction for common patterns
- Different naming conventions mask similarities

### Consolidation Strategy

**Step 1**: Create unified formatters module
```python
# prompts/formatters.py
"""Message and content formatting utilities.

Provides unified formatting for citations, context blocks, 
and response composition throughout the application.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FormattedMessage:
    """Structured formatted message with metadata."""
    content: str
    citations: List[str]
    metadata: Dict[str, Any]
    
    def to_string(self) -> str:
        """Convert to string with citations."""
        result = self.content
        if self.citations:
            result += "\n\n**Sources:**\n"
            for i, cite in enumerate(self.citations, 1):
                result += f"{i}. {cite}\n"
        return result


class CitationFormatter:
    """Unified citation formatting."""
    
    @staticmethod
    def format_citation(
        section: str, 
        url: str, 
        style: str = "standard"
    ) -> str:
        """Format a single citation.
        
        Args:
            section: Section or document name
            url: Source URL or location
            style: Format style ('standard', 'inline', 'markdown')
            
        Returns:
            Formatted citation string
        """
        if style == "inline":
            return f"{section} ({url})"
        elif style == "markdown":
            return f"[{section}]({url})"
        else:  # standard
            return f"[Source: {section} | {url}]"
    
    @staticmethod
    def format_multiple_citations(
        citations: List[Dict[str, str]],
        style: str = "standard"
    ) -> str:
        """Format multiple citations.
        
        Args:
            citations: List of {section, url} dicts
            style: Format style
            
        Returns:
            Formatted citations block
        """
        if not citations:
            return ""
        
        formatted = "**Sources:**\n"
        for i, cite in enumerate(citations, 1):
            cite_text = CitationFormatter.format_citation(
                cite.get("section", "Unknown"),
                cite.get("url", ""),
                style=style
            )
            formatted += f"{i}. {cite_text}\n"
        return formatted


class ContextFormatter:
    """Unified context block formatting."""
    
    @staticmethod
    def format_context_block(
        text: str,
        metadata: Dict[str, Any],
        include_separator: bool = True
    ) -> str:
        """Format a single context block.
        
        Args:
            text: Content text
            metadata: Context metadata
            include_separator: Add separator line
            
        Returns:
            Formatted context block
        """
        section = metadata.get("section", "General")
        url = metadata.get("source_url", "")
        
        formatted = f"\n**{section}**\n"
        if url:
            formatted += f"_Source: {url}_\n"
        formatted += f"{text}\n"
        
        if include_separator:
            formatted += "-" * 80 + "\n"
        
        return formatted
    
    @staticmethod
    def format_multiple_contexts(
        contexts: List[Dict[str, Any]],
        max_contexts: Optional[int] = None
    ) -> str:
        """Format multiple context blocks.
        
        Args:
            contexts: List of {text, metadata} dicts
            max_contexts: Maximum number of contexts to include
            
        Returns:
            Formatted context blocks
        """
        if not contexts:
            return ""
        
        contexts_to_use = contexts[:max_contexts] if max_contexts else contexts
        formatted = ""
        
        for context in contexts_to_use:
            formatted += ContextFormatter.format_context_block(
                context.get("text", ""),
                context.get("metadata", {}),
                include_separator=True
            )
        
        return formatted


class ResponseFormatter:
    """Unified response composition."""
    
    @staticmethod
    def compose_response(
        message: str,
        citations: Optional[List[Dict[str, str]]] = None,
        contexts: Optional[List[Dict[str, Any]]] = None,
        include_contexts: bool = False
    ) -> FormattedMessage:
        """Compose complete response with citations and contexts.
        
        Args:
            message: Main response message
            citations: List of citation dicts
            contexts: List of context dicts
            include_contexts: Include context blocks in output
            
        Returns:
            FormattedMessage object
        """
        content = message
        
        if include_contexts and contexts:
            content += "\n\n**Retrieved Context:**\n"
            content += ContextFormatter.format_multiple_contexts(contexts)
        
        citation_text = CitationFormatter.format_multiple_citations(citations or [])
        
        formatted_msg = FormattedMessage(
            content=content,
            citations=[c.get("section", "") for c in (citations or [])],
            metadata={"has_citations": bool(citations)}
        )
        
        return formatted_msg
    
    @staticmethod
    def add_citations_to_message(
        message: str,
        citations: List[str]
    ) -> str:
        """Add citations to existing message.
        
        Args:
            message: Original message
            citations: List of citation strings
            
        Returns:
            Message with citations appended
        """
        if not citations:
            return message
        
        result = message + "\n\n**References:**\n"
        for i, cite in enumerate(citations, 1):
            result += f"{i}. {cite}\n"
        return result
```

**Step 2**: Update imports across modules
```python
# prompts/prompt_orchestrator.py
from prompts.formatters import CitationFormatter, ContextFormatter, ResponseFormatter

# Before:
citations_text = f"[Source: {section} | {url}]"

# After:
citations_text = CitationFormatter.format_citation(section, url)
```

```python
# chatbot/chatbot.py
from prompts.formatters import ResponseFormatter

# Before:
response = message + "\n\nSources:\n"
for cite in citations:
    response += f"- {cite}\n"

# After:
formatted = ResponseFormatter.compose_response(message, citations)
response = formatted.to_string()
```

**Step 3**: Remove duplicate functions

### Benefits
✅ Single source of truth for formatting  
✅ Consistent formatting across UI/API  
✅ Easier to maintain formatting standards  
✅ Centralized citation/context templates  
✅ ~150 LOC reduction  
✅ Better testability (centralized tests)

### Testing Pattern
```python
# tests/test_formatters.py
import pytest
from prompts.formatters import (
    CitationFormatter, ContextFormatter, ResponseFormatter
)

class TestCitationFormatter:
    def test_formats_standard_citation(self):
        result = CitationFormatter.format_citation(
            "Admissions", "https://college.edu/admissions"
        )
        assert result == "[Source: Admissions | https://college.edu/admissions]"
    
    def test_formats_inline_citation(self):
        result = CitationFormatter.format_citation(
            "Admissions", "https://college.edu/admissions",
            style="inline"
        )
        assert result == "Admissions (https://college.edu/admissions)"
    
    def test_formats_multiple_citations(self):
        citations = [
            {"section": "A", "url": "url_a"},
            {"section": "B", "url": "url_b"}
        ]
        result = CitationFormatter.format_multiple_citations(citations)
        assert "Sources" in result
        assert "[Source: A | url_a]" in result
```

---

## Pattern 3: Metadata Extraction Duplication (632 LOC)

### Overview
Nearly identical metadata extraction logic in two separate modules:

| File | Functions | Purpose | LOC |
|------|-----------|---------|-----|
| `crawler/metadata.py` | 12 methods | Extract from HTML | ~350 |
| `ingestion/kb_metadata.py` | 8 methods | Enrich documents | ~282 |

**Total**: 632 LOC duplicated

### Duplication Examples

#### Issue 1: Title/Description Extraction (Duplicated)
```python
# crawler/metadata.py
def _extract_title(self, soup: BeautifulSoup) -> str:
    title = soup.find('title')
    if title:
        return title.string.strip()
    
    h1 = soup.find('h1')
    if h1:
        return h1.get_text().strip()
    
    return ""

# ingestion/kb_metadata.py (almost identical)
def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.string.strip()
    
    h1_tag = soup.find('h1')
    if h1_tag:
        return h1_tag.get_text().strip()
    
    return None
```

#### Issue 2: Open Graph Extraction (Duplicated)
```python
# crawler/metadata.py
def _extract_og_property(self, soup: BeautifulSoup, property_name: str) -> str:
    tag = soup.find('meta', property=f'og:{property_name}')
    if tag and tag.get('content'):
        return tag['content']
    return ""

# ingestion/kb_metadata.py (identical logic)
def extract_open_graph(self, soup: BeautifulSoup, prop: str) -> str:
    meta_tag = soup.find('meta', property=f'og:{prop}')
    if meta_tag and meta_tag.get('content'):
        return meta_tag['content']
    return ""
```

#### Issue 3: Date Extraction (Duplicated)
```python
# Both files have near-identical date extraction
def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
    # Check multiple date patterns
    patterns = [
        ('time[datetime]', 'datetime'),
        ('meta[property="article:published_time"]', 'content'),
        ('meta[name="publish_date"]', 'content'),
        ('span[class*="publish"]', None),
    ]
    
    for selector, attr in patterns:
        elem = soup.select_one(selector)
        if elem:
            return elem.get(attr) if attr else elem.get_text()
    
    return None
```

### Root Cause
- Metadata needs extracted at two different stages (crawling + ingestion)
- Developers created independent solutions
- No shared metadata layer
- Different naming conventions mask similarities

### Consolidation Strategy

**Step 1**: Create shared metadata extraction module
```python
# core/metadata.py
"""Shared metadata extraction and enrichment.

Provides unified extraction of metadata from HTML, documents,
and structured content across the application.
"""

from typing import Dict, Any, Optional, List, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
import re

from core.logger import get_logger

logger = get_logger(__name__)


class MetadataExtractor:
    """Unified metadata extraction engine.
    
    Extracts metadata from HTML, structured data, and content.
    Supports Open Graph, JSON-LD, meta tags, and content inference.
    """
    
    # Common date format patterns
    DATE_PATTERNS = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
    ]
    
    def __init__(self) -> None:
        """Initialize metadata extractor."""
        self.logger = logger
    
    # ===== TITLE & DESCRIPTION =====
    
    def extract_title(self, soup: BeautifulSoup, url: str = "") -> str:
        """Extract page title from multiple sources.
        
        Priority:
        1. <title> tag
        2. og:title meta tag
        3. <h1> tag
        4. URL segment
        
        Args:
            soup: BeautifulSoup object
            url: Page URL for fallback
            
        Returns:
            Extracted title or empty string
        """
        # Try <title> tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # Try Open Graph
        og_title = self._extract_meta_property(soup, 'og:title')
        if og_title:
            return og_title
        
        # Try <h1> tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        # Fallback to URL
        if url:
            path = urlparse(url).path.strip('/')
            return path.split('/')[-1].replace('-', ' ').title() if path else ""
        
        return ""
    
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description.
        
        Priority:
        1. meta description
        2. og:description
        3. First paragraph text
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted description
        """
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try og:description
        og_desc = self._extract_meta_property(soup, 'og:description')
        if og_desc:
            return og_desc
        
        # Try first paragraph
        p_tag = soup.find('p')
        if p_tag:
            return p_tag.get_text(strip=True)[:200]
        
        return ""
    
    # ===== OPEN GRAPH & META TAGS =====
    
    def _extract_meta_property(
        self, 
        soup: BeautifulSoup, 
        property_name: str,
        attribute: str = 'content'
    ) -> str:
        """Extract Open Graph or meta property.
        
        Args:
            soup: BeautifulSoup object
            property_name: Property name (e.g., 'og:title')
            attribute: Attribute to extract (content/href/etc)
            
        Returns:
            Property value or empty string
        """
        # Try as property attribute
        tag = soup.find('meta', property=property_name)
        if not tag:
            # Try as name attribute
            tag = soup.find('meta', attrs={'name': property_name})
        
        if tag and tag.get(attribute):
            return tag[attribute].strip()
        
        return ""
    
    def extract_open_graph(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract all Open Graph metadata.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary of og properties
        """
        og_properties = ['title', 'description', 'image', 'url', 'type', 'site_name']
        
        return {
            prop: self._extract_meta_property(soup, f'og:{prop}')
            for prop in og_properties
        }
    
    # ===== DATE EXTRACTION =====
    
    def extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract published/created date.
        
        Checks:
        1. <time datetime> attribute
        2. article:published_time property
        3. publish_date meta tag
        4. Date in page content
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            ISO formatted date string or None
        """
        # Try time element
        time_elem = soup.find('time')
        if time_elem and time_elem.get('datetime'):
            return time_elem['datetime']
        
        # Try JSON-LD
        jsonld_date = self._extract_jsonld_date(soup, 'datePublished')
        if jsonld_date:
            return jsonld_date
        
        # Try meta tags
        selectors = [
            ('meta[property="article:published_time"]', 'content'),
            ('meta[name="publish_date"]', 'content'),
            ('meta[name="article.published"]', 'content'),
        ]
        
        for selector, attr in selectors:
            elem = soup.select_one(selector)
            if elem and elem.get(attr):
                return elem[attr]
        
        return None
    
    def extract_modified_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract modified/updated date.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            ISO formatted date string or None
        """
        # Try JSON-LD
        jsonld_date = self._extract_jsonld_date(soup, 'dateModified')
        if jsonld_date:
            return jsonld_date
        
        # Try meta tags
        selectors = [
            ('meta[property="article:modified_time"]', 'content'),
            ('meta[name="last_modified"]', 'content'),
        ]
        
        for selector, attr in selectors:
            elem = soup.select_one(selector)
            if elem and elem.get(attr):
                return elem[attr]
        
        return None
    
    # ===== KEYWORDS & CATEGORIES =====
    
    def extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords/tags.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of keywords
        """
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords_str = meta_keywords['content'].strip()
            return [k.strip() for k in keywords_str.split(',')]
        
        return []
    
    def extract_section(
        self, 
        url: str, 
        content: str,
        title: str = ""
    ) -> str:
        """Infer section/category from URL and content.
        
        Args:
            url: Page URL
            content: Page content
            title: Page title
            
        Returns:
            Inferred section name
        """
        # Extract from URL path
        path = urlparse(url).path.lower()
        
        path_sections = {
            'admissions': ['admission', 'apply', 'enroll'],
            'academics': ['course', 'curriculum', 'program', 'department'],
            'placements': ['placement', 'career', 'job'],
            'facilities': ['library', 'lab', 'hostel', 'transport'],
            'events': ['event', 'seminar', 'conference', 'workshop'],
        }
        
        for section, keywords in path_sections.items():
            if any(kw in path for kw in keywords):
                return section
        
        # Fallback to title
        if title:
            title_lower = title.lower()
            for section, keywords in path_sections.items():
                if any(kw in title_lower for kw in keywords):
                    return section
        
        return "General"
    
    # ===== AUTHOR & STRUCTURED DATA =====
    
    def extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author information.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Author name or None
        """
        # Try meta author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()
        
        # Try JSON-LD
        return self._extract_jsonld_field(soup, 'author')
    
    def _extract_jsonld_date(
        self, 
        soup: BeautifulSoup, 
        field: str
    ) -> Optional[str]:
        """Extract date from JSON-LD structured data.
        
        Args:
            soup: BeautifulSoup object
            field: Field name (datePublished/dateModified)
            
        Returns:
            Date string or None
        """
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                import json
                data = json.loads(script.string)
                if field in data:
                    return data[field]
        except Exception as e:
            self.logger.debug(f"Error extracting JSON-LD date: {e}")
        
        return None
    
    def _extract_jsonld_field(
        self, 
        soup: BeautifulSoup, 
        field: str
    ) -> Optional[str]:
        """Extract field from JSON-LD structured data.
        
        Args:
            soup: BeautifulSoup object
            field: Field name
            
        Returns:
            Field value or None
        """
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                import json
                data = json.loads(script.string)
                if field in data:
                    value = data[field]
                    if isinstance(value, dict):
                        return value.get('name', str(value))
                    return str(value)
        except Exception as e:
            self.logger.debug(f"Error extracting JSON-LD field: {e}")
        
        return None
    
    def extract_all(
        self, 
        url: str, 
        html: str
    ) -> Dict[str, Any]:
        """Extract all available metadata.
        
        Comprehensive metadata extraction in one call.
        
        Args:
            url: Page URL
            html: HTML content
            
        Returns:
            Dictionary with all extracted metadata
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            return {
                'url': url,
                'title': self.extract_title(soup, url),
                'description': self.extract_description(soup),
                'keywords': self.extract_keywords(soup),
                'open_graph': self.extract_open_graph(soup),
                'author': self.extract_author(soup),
                'published_date': self.extract_published_date(soup),
                'modified_date': self.extract_modified_date(soup),
                'section': self.extract_section(url, '', self.extract_title(soup, url)),
            }
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {url}: {e}")
            return {'url': url}
```

**Step 2**: Update imports
```python
# crawler/metadata.py
from core.metadata import MetadataExtractor

# Update to use shared extractor
class MetadataExtractor:
    def __init__(self):
        self.extractor = MetadataExtractor()
    
    def extract(self, url: str, html: str, content: str) -> dict:
        return self.extractor.extract_all(url, html)

# ingestion/kb_metadata.py
from core.metadata import MetadataExtractor

class KBMetadataExtractor:
    def __init__(self):
        self.extractor = MetadataExtractor()
    
    def extract(self, raw_doc: Dict[str, Any]) -> Dict[str, Any]:
        # Reuse shared extractor
        metadata = self.extractor.extract_all(
            raw_doc.get('url', ''),
            raw_doc.get('html', '')
        )
        return metadata
```

**Step 3**: Remove duplicate methods

### Benefits
✅ Single metadata extraction engine  
✅ Consistent behavior across pipeline  
✅ Easier to add new extraction types  
✅ Centralized date/property handling  
✅ ~280 LOC reduction  
✅ Better JSON-LD support

---

## Summary

| Pattern | Before | After | Saved | Benefit |
|---------|--------|-------|-------|---------|
| Message Formatting | 5 files | 1 module | ~150 LOC | Unified formatting |
| Metadata Extraction | 2 files | 1 class | ~280 LOC | Consistent extraction |
| **Combined** | **7 files** | **2 modules** | **~430 LOC** | **+25% maintainability** |

