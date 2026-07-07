# Detailed Duplication Analysis: Patterns 4, 5 & 6

## Pattern 4: Validation Logic Duplication (180 LOC)

### Overview
Input validation and sanitization logic scattered across 3 locations with regex duplication:

| Location | Functions | Purpose | LOC |
|----------|-----------|---------|-----|
| `security/security.py` | 5 validators | Security validation | ~80 |
| `core/optimization.py` | 3 validators | Input cleaning | ~50 |
| `crawler/crawl.py` | 2 validators | Link validation | ~50 |

**Total**: 180 LOC with 40+ regex patterns

### Duplication Examples

#### Issue 1: URL Validation (Duplicated in 2 files)
```python
# security/security.py
def validate_url(self, url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+$'
    return bool(re.match(pattern, url))

# crawler/crawl.py (similar logic)
def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    url_pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+$'
    return bool(re.match(url_pattern, url))
```

#### Issue 2: Email Validation (Duplicated in 2 files)
```python
# security/security.py
def validate_email(self, email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# core/optimization.py (similar logic)
def is_valid_email(email: str) -> bool:
    """Check email validity."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))
```

#### Issue 3: Query Sanitization (Duplicated in multiple places)
```python
# security/security.py
def sanitize_query(self, query: str) -> str:
    """Remove potentially harmful patterns."""
    # Remove SQL patterns
    query = re.sub(r'(union|select|insert|delete|drop)\s*\(', '', query, flags=re.IGNORECASE)
    # Remove script tags
    query = re.sub(r'<script[^>]*>.*?</script>', '', query, flags=re.IGNORECASE)
    return query

# core/optimization.py (similar logic)
def sanitize_input(text: str) -> str:
    """Clean input text."""
    # Remove SQL patterns
    text = re.sub(r'(union|select|insert|delete)\s*\(', '', text, flags=re.IGNORECASE)
    # Remove HTML/script
    text = re.sub(r'<[^>]+>', '', text)
    return text
```

### Root Cause
- Validation rules defined independently
- Similar regex patterns written multiple times
- No shared validation layer
- Different naming conventions
- Inconsistent validation standards

### Consolidation Strategy

**Step 1**: Create unified validators module
```python
# core/validators.py
"""Unified input validation and sanitization.

Provides centralized validation for URLs, emails, queries,
and other input types with consistent regex patterns.
"""

import re
from typing import Optional, List, Pattern
from enum import Enum

from core.logger import get_logger

logger = get_logger(__name__)


class ValidationError(ValueError):
    """Raised when validation fails."""
    pass


class PatternType(Enum):
    """Common validation patterns."""
    URL = "url"
    EMAIL = "email"
    DOMAIN = "domain"
    QUERY = "query"
    FILENAME = "filename"
    SLUG = "slug"


class RegexPatterns:
    """Centralized regex patterns to eliminate duplication."""
    
    # Standard patterns (RFC-compliant where applicable)
    PATTERNS: dict[PatternType, str] = {
        PatternType.URL: (
            r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+'
            r'(?:[?#][a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]*)?$'
        ),
        PatternType.EMAIL: (
            r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+'
            r'@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
            r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        ),
        PatternType.DOMAIN: (
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
            r'[a-zA-Z]{2,}(?:\:[0-9]{1,5})?$'
        ),
        PatternType.SLUG: r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
        PatternType.FILENAME: r'^[a-zA-Z0-9\._\-]+$',
        PatternType.QUERY: None,  # Custom validation
    }
    
    # Harmful patterns to detect and remove
    SQL_KEYWORDS = r'\b(union|select|insert|delete|drop|create|alter|exec|execute)\s*\('
    SCRIPT_TAGS = r'<script[^>]*>.*?</script>'
    HTML_TAGS = r'<[^>]+>'
    INJECTION_PATTERNS = r'[;\'"`]|--'
    
    @classmethod
    def get_pattern(cls, pattern_type: PatternType) -> Optional[str]:
        """Get regex pattern for type."""
        return cls.PATTERNS.get(pattern_type)
    
    @classmethod
    def compile_pattern(cls, pattern_type: PatternType) -> Optional[Pattern]:
        """Get compiled regex pattern for efficiency."""
        pattern = cls.get_pattern(pattern_type)
        if pattern:
            return re.compile(pattern, re.IGNORECASE)
        return None


class InputValidator:
    """Unified input validation engine."""
    
    def __init__(self) -> None:
        """Initialize validator with compiled patterns."""
        self.patterns: dict[PatternType, Pattern] = {}
        for ptype in PatternType:
            compiled = RegexPatterns.compile_pattern(ptype)
            if compiled:
                self.patterns[ptype] = compiled
        
        # Compile harmful patterns
        self.sql_pattern = re.compile(RegexPatterns.SQL_KEYWORDS, re.IGNORECASE)
        self.script_pattern = re.compile(RegexPatterns.SCRIPT_TAGS, re.IGNORECASE)
        self.html_pattern = re.compile(RegexPatterns.HTML_TAGS)
        self.injection_pattern = re.compile(RegexPatterns.INJECTION_PATTERNS)
    
    # ===== BASIC VALIDATORS =====
    
    def validate_url(
        self, 
        url: str, 
        raise_on_error: bool = False
    ) -> bool:
        """Validate URL format.
        
        Args:
            url: URL string to validate
            raise_on_error: Raise exception if invalid
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If raise_on_error=True and invalid
        """
        if not url or not isinstance(url, str):
            if raise_on_error:
                raise ValidationError(f"Invalid URL: {url}")
            return False
        
        if self.patterns[PatternType.URL].match(url.strip()):
            return True
        
        if raise_on_error:
            raise ValidationError(f"URL format invalid: {url}")
        return False
    
    def validate_email(
        self, 
        email: str, 
        raise_on_error: bool = False
    ) -> bool:
        """Validate email address.
        
        Args:
            email: Email string to validate
            raise_on_error: Raise exception if invalid
            
        Returns:
            True if valid, False otherwise
        """
        if not email or not isinstance(email, str):
            if raise_on_error:
                raise ValidationError(f"Invalid email: {email}")
            return False
        
        if self.patterns[PatternType.EMAIL].match(email.strip()):
            return True
        
        if raise_on_error:
            raise ValidationError(f"Email format invalid: {email}")
        return False
    
    def validate_domain(
        self, 
        domain: str, 
        raise_on_error: bool = False
    ) -> bool:
        """Validate domain name.
        
        Args:
            domain: Domain string to validate
            raise_on_error: Raise exception if invalid
            
        Returns:
            True if valid, False otherwise
        """
        if not domain or not isinstance(domain, str):
            if raise_on_error:
                raise ValidationError(f"Invalid domain: {domain}")
            return False
        
        if self.patterns[PatternType.DOMAIN].match(domain.strip()):
            return True
        
        if raise_on_error:
            raise ValidationError(f"Domain format invalid: {domain}")
        return False
    
    def validate_slug(
        self, 
        slug: str, 
        raise_on_error: bool = False
    ) -> bool:
        """Validate URL slug format.
        
        Args:
            slug: Slug string to validate
            raise_on_error: Raise exception if invalid
            
        Returns:
            True if valid, False otherwise
        """
        if not slug or not isinstance(slug, str):
            if raise_on_error:
                raise ValidationError(f"Invalid slug: {slug}")
            return False
        
        if self.patterns[PatternType.SLUG].match(slug.strip()):
            return True
        
        if raise_on_error:
            raise ValidationError(f"Slug format invalid: {slug}")
        return False
    
    # ===== QUERY & TEXT VALIDATORS =====
    
    def validate_query(
        self, 
        query: str, 
        min_length: int = 3,
        max_length: int = 500,
        raise_on_error: bool = False
    ) -> bool:
        """Validate search query.
        
        Args:
            query: Query string to validate
            min_length: Minimum length requirement
            max_length: Maximum length requirement
            raise_on_error: Raise exception if invalid
            
        Returns:
            True if valid, False otherwise
        """
        if not query or not isinstance(query, str):
            if raise_on_error:
                raise ValidationError("Query cannot be empty")
            return False
        
        query = query.strip()
        
        if len(query) < min_length:
            if raise_on_error:
                raise ValidationError(f"Query too short (min {min_length} chars)")
            return False
        
        if len(query) > max_length:
            if raise_on_error:
                raise ValidationError(f"Query too long (max {max_length} chars)")
            return False
        
        return True
    
    def validate_text_length(
        self, 
        text: str, 
        min_length: int = 0,
        max_length: int = None,
        raise_on_error: bool = False
    ) -> bool:
        """Validate text length.
        
        Args:
            text: Text to validate
            min_length: Minimum length
            max_length: Maximum length (None = unlimited)
            raise_on_error: Raise exception if invalid
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(text, str):
            if raise_on_error:
                raise ValidationError("Text must be string")
            return False
        
        if len(text) < min_length:
            if raise_on_error:
                raise ValidationError(f"Text too short (min {min_length} chars)")
            return False
        
        if max_length and len(text) > max_length:
            if raise_on_error:
                raise ValidationError(f"Text too long (max {max_length} chars)")
            return False
        
        return True
    
    # ===== SANITIZATION =====
    
    def sanitize_query(
        self, 
        query: str, 
        remove_sql: bool = True,
        remove_scripts: bool = True,
        remove_html: bool = True
    ) -> str:
        """Sanitize search query.
        
        Removes potentially harmful patterns while preserving intent.
        
        Args:
            query: Query to sanitize
            remove_sql: Remove SQL injection patterns
            remove_scripts: Remove script tags
            remove_html: Remove HTML tags
            
        Returns:
            Sanitized query
        """
        if not isinstance(query, str):
            return ""
        
        result = query.strip()
        
        if remove_sql:
            result = self.sql_pattern.sub('', result)
        
        if remove_scripts:
            result = self.script_pattern.sub('', result, flags=re.IGNORECASE)
        
        if remove_html:
            result = self.html_pattern.sub('', result)
        
        # Remove excessive whitespace
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize URL by removing dangerous patterns.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
        """
        if not isinstance(url, str):
            return ""
        
        # Remove javascript: protocol
        url = re.sub(r'^javascript:', '', url, flags=re.IGNORECASE)
        
        # Remove data: protocol
        url = re.sub(r'^data:', '', url, flags=re.IGNORECASE)
        
        # Remove script tags in parameters
        url = self.script_pattern.sub('', url, flags=re.IGNORECASE)
        
        return url.strip()
    
    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML by removing script tags.
        
        Args:
            html: HTML to sanitize
            
        Returns:
            Sanitized HTML (scripts removed)
        """
        if not isinstance(html, str):
            return ""
        
        # Remove script tags and content
        html = self.script_pattern.sub('', html, flags=re.IGNORECASE)
        
        # Remove event handlers
        html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        html = re.sub(r'\s*on\w+\s*=[^\s>]*', '', html, flags=re.IGNORECASE)
        
        return html
    
    def sanitize_text(self, text: str, preserve_newlines: bool = False) -> str:
        """Sanitize general text input.
        
        Args:
            text: Text to sanitize
            preserve_newlines: Keep newline characters
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove HTML tags
        text = self.html_pattern.sub('', text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters (except newline/tab)
        if not preserve_newlines:
            text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        else:
            text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        
        return text
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Safe filename
        """
        if not isinstance(filename, str):
            return "file"
        
        # Remove path components
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove special characters
        filename = re.sub(r'[^a-zA-Z0-9._\-]', '', filename)
        
        # Ensure not empty
        return filename if filename else "file"
    
    def contains_injection_patterns(self, text: str) -> bool:
        """Check if text contains injection patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if injection patterns found
        """
        if not isinstance(text, str):
            return False
        
        return bool(self.injection_pattern.search(text))


# Singleton instance for easy access
_validator = None

def get_validator() -> InputValidator:
    """Get singleton validator instance."""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator

```

**Step 2**: Update imports across modules
```python
# security/security.py
from core.validators import get_validator, ValidationError

class SecurityValidator:
    def __init__(self):
        self.validator = get_validator()
    
    def validate_user_query(self, query: str) -> bool:
        """Use centralized validator."""
        return self.validator.validate_query(query)

# crawler/crawl.py
from core.validators import get_validator

class CrawlerOrchestrator:
    def __init__(self):
        self.validator = get_validator()
    
    def is_valid_url(self, url: str) -> bool:
        """Use centralized validator."""
        return self.validator.validate_url(url)
```

**Step 3**: Remove duplicate validators

### Benefits
✅ Single source of truth for validation  
✅ Centralized regex patterns  
✅ Consistent validation behavior  
✅ Easy to audit security patterns  
✅ ~100 LOC reduction  
✅ Better error handling

---

## Pattern 5: Error Handling Patterns

### Overview
Repetitive try-except patterns across 47 files with 530+ matches:

### Duplication Examples

#### Issue: Identical try-except wrappers (50+ instances)
```python
# Pattern repeated across many files
try:
    result = perform_operation()
except Exception as e:
    logger.error(f"Error in {context}: {e}")
    raise CustomException(f"Operation failed: {e}")

# Same pattern with slight variations in 50+ locations
try:
    value = some_function()
except Exception as e:
    logger.error(f"Failed: {e}")
    raise
```

### Consolidation Strategy

**Step 1**: Create error handling decorator
```python
# core/error_handling.py
"""Unified error handling patterns."""

import functools
from typing import Callable, TypeVar, Any, Optional, Type, List
from core.logger import get_logger
from core.exceptions import AppException

logger = get_logger(__name__)

T = TypeVar("T")


def handle_error(
    context: str,
    exception_type: Type[Exception] = AppException,
    log_level: str = "error",
    reraise: bool = True,
    fallback_value: Any = None
) -> Callable:
    """Decorator for unified error handling.
    
    Args:
        context: Context for error message
        exception_type: Exception type to raise
        log_level: Logging level (debug/info/warning/error/critical)
        reraise: Reraise exception after logging
        fallback_value: Return value if error occurs
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log at appropriate level
                log_msg = f"Error in {context} ({func.__name__}): {e}"
                getattr(logger, log_level)(log_msg)
                
                # Raise or return fallback
                if reraise:
                    raise exception_type(log_msg) from e
                return fallback_value
        
        return wrapper
    return decorator


# Usage examples:
@handle_error("database operation", exception_type=DatabaseError)
def fetch_data():
    pass

@handle_error("API call", log_level="warning", fallback_value=[])
def get_external_data():
    pass
```

**Step 2**: Apply decorator to functions
```python
# Before
def extract_metadata(url: str) -> dict:
    try:
        soup = BeautifulSoup(html, "html.parser")
        return extract_fields(soup)
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        raise

# After
@handle_error("metadata extraction")
def extract_metadata(url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    return extract_fields(soup)
```

### Benefits
✅ Standardized error handling  
✅ Consistent logging  
✅ Reduced boilerplate  
✅ Easier to audit error paths  
✅ ~80 LOC reduction

---

## Pattern 6: Test Fixture Duplication (120 LOC)

### Overview
Similar test setup patterns repeated across 8 test files:

| Test File | Mock Fixtures | Setup LOC |
|-----------|---------------|----------|
| `test_retriever.py` | Document, embeddings, results | ~25 |
| `test_vectorstore.py` | Embeddings, queries | ~20 |
| `test_chatbot.py` | Document, query, response | ~20 |
| `test_embedding.py` | Mock data, vectors | ~18 |
| `test_evaluation.py` | Test cases, metrics | ~25 |
| Others | Various | ~12 |

### Duplication Examples

#### Issue: Repeated fixture setup (4+ files)
```python
# test_retriever.py
@pytest.fixture
def sample_embeddings():
    return [
        {"embedding_id": f"emb_{i}", "vector": [0.1 + i*0.01] * 1536}
        for i in range(5)
    ]

# test_vectorstore.py (nearly identical)
@pytest.fixture
def embeddings_fixture():
    return [
        {"embedding_id": f"emb_{i}", "vector": [0.1 + i*0.01] * 1536}
        for i in range(5)
    ]

# test_chatbot.py (same pattern)
@pytest.fixture
def mock_embeddings():
    embeddings = []
    for i in range(5):
        embeddings.append({
            "embedding_id": f"emb_{i}",
            "vector": [0.1 + i*0.01] * 1536
        })
    return embeddings
```

### Consolidation Strategy

**Step 1**: Create centralized fixture factories
```python
# tests/factories.py
"""Test data factories to eliminate fixture duplication."""

import pytest
from typing import List, Dict, Any
from datetime import datetime


class DocumentFactory:
    """Factory for creating test documents."""
    
    @staticmethod
    def create(
        doc_id: str = "doc_1",
        title: str = "Test Document",
        content: str = "Test content",
        url: str = "https://example.com/test",
        section: str = "admissions"
    ) -> Dict[str, Any]:
        """Create a test document."""
        return {
            "id": doc_id,
            "title": title,
            "content": content,
            "url": url,
            "section": section,
            "metadata": {"category": section},
            "created_at": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def create_batch(count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple test documents."""
        return [
            DocumentFactory.create(
                doc_id=f"doc_{i}",
                title=f"Document {i}",
                content=f"Content for document {i}"
            )
            for i in range(count)
        ]


class EmbeddingFactory:
    """Factory for creating test embeddings."""
    
    @staticmethod
    def create(
        embedding_id: str = "emb_1",
        chunk_id: str = "chunk_1",
        vector: List[float] = None
    ) -> Dict[str, Any]:
        """Create a test embedding."""
        if vector is None:
            vector = [0.1] * 1536
        
        return {
            "embedding_id": embedding_id,
            "chunk_id": chunk_id,
            "vector": vector,
            "chunk_text": "Test text",
            "section": "admissions",
            "source_url": "https://example.com",
        }
    
    @staticmethod
    def create_batch(count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple embeddings."""
        return [
            EmbeddingFactory.create(
                embedding_id=f"emb_{i}",
                chunk_id=f"chunk_{i}",
                vector=[0.1 + i*0.01] * 1536
            )
            for i in range(count)
        ]


class QueryFactory:
    """Factory for creating test queries."""
    
    @staticmethod
    def create(query: str = "What are admission requirements?") -> str:
        """Create a test query."""
        return query
    
    @staticmethod
    def create_batch() -> List[str]:
        """Create multiple test queries."""
        return [
            "What are the admission requirements?",
            "What is the placement rate?",
            "What facilities are available?",
            "How much are the fees?",
            "What is the hostel facility?",
        ]


# Pytest fixtures that use factories
@pytest.fixture
def sample_document():
    """Provide a sample document."""
    return DocumentFactory.create()


@pytest.fixture
def sample_documents():
    """Provide multiple sample documents."""
    return DocumentFactory.create_batch(5)


@pytest.fixture
def sample_embeddings():
    """Provide sample embeddings."""
    return EmbeddingFactory.create_batch(5)


@pytest.fixture
def sample_query():
    """Provide a sample query."""
    return QueryFactory.create()


@pytest.fixture
def sample_queries():
    """Provide multiple sample queries."""
    return QueryFactory.create_batch()
```

**Step 2**: Update test imports
```python
# tests/test_retriever.py
from tests.factories import EmbeddingFactory, DocumentFactory

class TestRetriever:
    def test_retrieves_embeddings(self):
        embeddings = EmbeddingFactory.create_batch(10)
        # Use embeddings in test

# tests/test_vectorstore.py
from tests.factories import EmbeddingFactory

class TestVectorStore:
    def test_adds_embeddings(self):
        embeddings = EmbeddingFactory.create_batch(5)
        # Use embeddings in test
```

### Benefits
✅ DRY test data creation  
✅ Consistent test fixtures  
✅ Easy to extend factories  
✅ Better test maintainability  
✅ ~60 LOC reduction

---

## Implementation Summary

| Pattern | Type | Severity | Impact | Effort |
|---------|------|----------|--------|--------|
| **1** | SearchResult | HIGH | 40 LOC | 0.5h |
| **2** | Message Formatting | HIGH | 150 LOC | 2h |
| **3** | Metadata Extraction | HIGH | 280 LOC | 2.5h |
| **4** | Validation Logic | MEDIUM | 100 LOC | 1.5h |
| **5** | Error Handling | MEDIUM | 80 LOC | 1.5h |
| **6** | Test Fixtures | LOW | 60 LOC | 0.5h |
| **TOTAL** | | | **710 LOC** | **8.5h** |

---

## Quick Reference: Consolidation Checklist

### Phase 1 (Immediate - 5 hours)
- [ ] Create `retriever/models.py`
- [ ] Create `prompts/formatters.py`
- [ ] Create `core/metadata.py`
- [ ] Update all imports
- [ ] Run test suite
- [ ] Remove duplicates

### Phase 2 (Short-term - 3 hours)
- [ ] Create `core/validators.py`
- [ ] Create `core/error_handling.py`
- [ ] Refactor error handling with decorators
- [ ] Update security module imports

### Phase 3 (Optional - 0.5 hours)
- [ ] Create `tests/factories.py`
- [ ] Update test fixtures
- [ ] Clean up conftest.py

