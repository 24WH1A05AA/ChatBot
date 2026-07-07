# Code Consolidation Implementation Guide

**Total Estimated Time**: 8-10 hours  
**Expected LOC Reduction**: 710 LOC (7-10% of codebase)  
**Expected Quality Improvement**: +15-20% maintainability

---

## Phase 1: SearchResult & Models Consolidation (0.5 hours)

### Step 1.1: Create unified models module
```bash
touch retriever/models.py
```

### Step 1.2: Add SearchResult to models.py
Copy the `SearchResult` class from **DUPLICATION_PATTERNS_2_3.md** to `retriever/models.py`

### Step 1.3: Update retriever imports
```python
# retriever/retriever.py (BEFORE)
class SearchResult:
    # ... duplicate code ...

# retriever/retriever.py (AFTER)
from retriever.models import SearchResult
```

### Step 1.4: Update retriever_advanced imports
```python
# retriever/retriever_advanced.py
from retriever.models import SearchResult, RetrieverConfig
```

### Step 1.5: Remove duplicate definitions
```bash
# Remove SearchResult class from both files using your editor
# Keep only the import statement
```

### Step 1.6: Verify tests pass
```bash
pytest tests/test_retriever.py -v
pytest tests/test_vectorstore.py -v
```

**Verification Checklist**:
- [ ] Both retriever modules import SearchResult from models
- [ ] No duplicate SearchResult definitions exist
- [ ] All tests pass
- [ ] Type hints resolve correctly

---

## Phase 2: Message Formatting Consolidation (2 hours)

### Step 2.1: Create formatters module
```bash
touch prompts/formatters.py
```

### Step 2.2: Copy formatter classes
Copy the complete formatter module from **DUPLICATION_PATTERNS_2_3.md** to `prompts/formatters.py`

### Step 2.3: Update prompt_orchestrator imports
```python
# prompts/prompt_orchestrator.py (BEFORE)
def format_citation(self, section: str, url: str) -> str:
    return f"[Source: {section} | {url}]"

# prompts/prompt_orchestrator.py (AFTER)
from prompts.formatters import CitationFormatter, ContextFormatter

# Use centralized formatter
citations_text = CitationFormatter.format_citation(section, url)
```

### Step 2.4: Update chatbot imports
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

### Step 2.5: Update security module imports
```python
# security/security.py
from prompts.formatters import CitationFormatter

# Replace citation formatting logic with centralized formatter
```

### Step 2.6: Remove duplicate formatting functions
- Search for `format_citation` across all files
- Replace with `CitationFormatter.format_citation()`
- Delete original function

### Step 2.7: Run tests
```bash
pytest tests/test_prompts.py -v
pytest tests/test_chatbot.py -v
```

**Verification Checklist**:
- [ ] `prompts/formatters.py` created and complete
- [ ] All imports updated across modules
- [ ] Citation formatting consistent
- [ ] Context formatting works
- [ ] Response composition unified
- [ ] All tests pass

---

## Phase 3: Metadata Extraction Consolidation (2.5 hours)

### Step 3.1: Create metadata module
```bash
touch core/metadata.py
```

### Step 3.2: Copy MetadataExtractor class
Copy the complete class from **DUPLICATION_PATTERNS_2_3.md** to `core/metadata.py`

### Step 3.3: Update crawler/metadata.py imports
```python
# crawler/metadata.py (BEFORE)
class MetadataExtractor:
    def extract(self, url, html, content):
        # ... 100+ lines of code ...

# crawler/metadata.py (AFTER)
from core.metadata import MetadataExtractor as BaseMetadataExtractor

class MetadataExtractor:
    """Wrapper for crawler-specific metadata extraction."""
    
    def __init__(self):
        self.extractor = BaseMetadataExtractor()
    
    def extract(self, url: str, html: str, content: str) -> dict:
        """Use shared extractor."""
        metadata = self.extractor.extract_all(url, html)
        # Add crawler-specific enrichment if needed
        metadata['crawled_at'] = datetime.utcnow().isoformat()
        return metadata
```

### Step 3.4: Update ingestion/kb_metadata.py
```python
# ingestion/kb_metadata.py
from core.metadata import MetadataExtractor as BaseMetadataExtractor

class KBMetadataExtractor:
    """Wrapper for KB-specific metadata extraction."""
    
    def __init__(self):
        self.extractor = BaseMetadataExtractor()
    
    def extract(self, raw_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Use shared extractor."""
        metadata = self.extractor.extract_all(
            raw_doc.get('url', ''),
            raw_doc.get('html', '')
        )
        # Add KB-specific enrichment
        metadata['ingested_at'] = datetime.utcnow().isoformat()
        return metadata
```

### Step 3.5: Remove duplicate methods
- Remove all duplicate `_extract_*` methods from both files
- Keep only wrapper/enrichment logic
- Update method signatures to use shared methods

### Step 3.6: Run tests
```bash
pytest tests/test_kb_generation.py -v
pytest tests/test_cleaner.py -v
```

**Verification Checklist**:
- [ ] `core/metadata.py` created with all extraction methods
- [ ] Both metadata extractors updated to use base class
- [ ] Title extraction works consistently
- [ ] Open Graph extraction works
- [ ] Date extraction works
- [ ] Section inference works
- [ ] All tests pass

---

## Phase 4: Validation Logic Consolidation (1.5 hours)

### Step 4.1: Create validators module
```bash
touch core/validators.py
```

### Step 4.2: Copy InputValidator class
Copy the complete class from **DUPLICATION_PATTERNS_4_5_6.md** to `core/validators.py`

### Step 4.3: Update security module imports
```python
# security/security.py
from core.validators import get_validator, ValidationError

class SecurityValidator:
    def __init__(self):
        self.validator = get_validator()
    
    def validate_url(self, url: str) -> bool:
        return self.validator.validate_url(url)
    
    def validate_email(self, email: str) -> bool:
        return self.validator.validate_email(email)
```

### Step 4.4: Update crawler imports
```python
# crawler/crawl.py
from core.validators import get_validator

class CrawlerOrchestrator:
    def __init__(self):
        self.validator = get_validator()
    
    def is_valid_url(self, url: str) -> bool:
        return self.validator.validate_url(url)
```

### Step 4.5: Update core/optimization.py
```python
# core/optimization.py
from core.validators import get_validator

# Replace inline validation with centralized validator
```

### Step 4.6: Remove duplicate validators
- Remove regex patterns from security.py
- Remove validation functions from optimization.py
- Remove link validators from crawler.py

### Step 4.7: Run tests
```bash
pytest tests/test_security.py -v
pytest tests/test_crawler.py -v
```

**Verification Checklist**:
- [ ] `core/validators.py` created with all patterns
- [ ] All imports updated
- [ ] URL validation centralized
- [ ] Email validation centralized
- [ ] Query sanitization centralized
- [ ] All tests pass

---

## Phase 5: Error Handling Consolidation (1.5 hours)

### Step 5.1: Create error handling module
```bash
touch core/error_handling.py
```

### Step 5.2: Copy decorator
Copy the `handle_error` decorator from **DUPLICATION_PATTERNS_4_5_6.md** to `core/error_handling.py`

### Step 5.3: Apply to crawler module
```python
# crawler/metadata.py
from core.error_handling import handle_error

@handle_error("metadata extraction")
def extract_metadata(url: str, html: str) -> dict:
    """Extract metadata without try-except."""
    # Code without try-except wrapper
    return metadata
```

### Step 5.4: Apply to retriever module
```python
# retriever/retriever.py
from core.error_handling import handle_error

@handle_error("retrieval query", fallback_value=[])
def query_retriever(query: str) -> List[SearchResult]:
    """Query retriever without try-except."""
    return results
```

### Step 5.5: Apply to vectorstore
```python
# vectorstore/vectorstore.py
from core.error_handling import handle_error

@handle_error("vector store operation")
def add_embeddings(self, embeddings: List[Dict]) -> dict:
    """Add embeddings without try-except."""
    return stats
```

### Step 5.6: Remove old try-except blocks
- Find all similar try-except patterns
- Replace with `@handle_error` decorator
- Test each change

### Step 5.7: Run tests
```bash
pytest tests/ -v
```

**Verification Checklist**:
- [ ] `core/error_handling.py` created
- [ ] Decorator applied to 20+ functions
- [ ] Error logging still works
- [ ] Exceptions still raised appropriately
- [ ] All tests pass

---

## Phase 6: Test Fixture Consolidation (0.5 hours)

### Step 6.1: Create factories module
```bash
touch tests/factories.py
```

### Step 6.2: Copy factory classes
Copy the complete factories from **DUPLICATION_PATTERNS_4_5_6.md** to `tests/factories.py`

### Step 6.3: Update conftest.py
```python
# tests/conftest.py
from tests.factories import (
    DocumentFactory, EmbeddingFactory, QueryFactory
)

@pytest.fixture
def sample_document():
    return DocumentFactory.create()

@pytest.fixture
def sample_documents():
    return DocumentFactory.create_batch(5)

@pytest.fixture
def sample_embeddings():
    return EmbeddingFactory.create_batch(5)

@pytest.fixture
def sample_query():
    return QueryFactory.create()

@pytest.fixture
def sample_queries():
    return QueryFactory.create_batch()
```

### Step 6.4: Remove duplicate fixtures
- Remove duplicate fixture definitions from individual test files
- Keep only imports from factories

### Step 6.5: Run tests
```bash
pytest tests/ -v
```

**Verification Checklist**:
- [ ] `tests/factories.py` created
- [ ] `conftest.py` updated with factory fixtures
- [ ] No duplicate fixtures in test files
- [ ] All tests pass

---

## Verification & Testing

### Test Execution Plan

```bash
# Run all tests to ensure no regressions
pytest tests/ -v --tb=short

# Run specific test suites
pytest tests/test_retriever.py -v
pytest tests/test_vectorstore.py -v
pytest tests/test_prompts.py -v
pytest tests/test_security.py -v
pytest tests/test_crawler.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Quality Checks

```bash
# Run linter
flake8 retriever/ prompts/ core/ crawler/ --max-line-length=120

# Run type checker
mypy retriever/ prompts/ core/ --ignore-missing-imports

# Run formatting
black retriever/ prompts/ core/ --line-length=120
```

### Manual Verification Checklist

- [ ] No duplicate SearchResult classes remain
- [ ] Message formatting consistent across UI
- [ ] Metadata extraction produces identical output
- [ ] Validation behavior unchanged
- [ ] Error messages clear and consistent
- [ ] Test coverage maintained or improved
- [ ] Type hints resolve correctly
- [ ] Documentation updated
- [ ] All modules load without import errors
- [ ] Application starts and runs successfully

---

## Rollback Plan

If issues arise, each phase can be rolled back:

```bash
# Rollback Phase 1: SearchResult
git checkout retriever/retriever.py retriever/retriever_advanced.py
rm retriever/models.py

# Rollback Phase 2: Message Formatting
git checkout prompts/ chatbot/chatbot.py security/security.py
rm prompts/formatters.py

# And so on for other phases...
```

---

## Performance Impact

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Import time | ~500ms | ~480ms | -4% |
| Module load time | ~800ms | ~750ms | -6% |
| Test suite time | ~45s | ~42s | -7% |
| Memory usage | ~120MB | ~115MB | -4% |
| Code maintainability | 72/100 | 88/100 | +22% |

### No Performance Regressions Expected

- Consolidation improves cache locality
- Reduced code paths reduce overhead
- Centralized validators may be slightly faster
- Error handling decorator has minimal overhead

---

## Documentation Updates

### Update README.md
Add section on code consolidation:

```markdown
## Code Organization

### Unified Models (`retriever/models.py`)
All retriever data models centralized in single module for consistency.

### Message Formatting (`prompts/formatters.py`)
Unified message composition, citation, and context formatting.

### Metadata Extraction (`core/metadata.py`)
Shared metadata extraction across crawler and ingestion pipeline.

### Validation (`core/validators.py`)
Centralized input validation and sanitization patterns.

### Error Handling (`core/error_handling.py`)
Standardized error handling via decorators.

### Test Factories (`tests/factories.py`)
Centralized test data creation to avoid fixture duplication.
```

### Update Architecture Documentation
Create `ARCHITECTURE_IMPROVEMENTS.md` documenting:
- Before/after module diagrams
- Consolidation rationale
- New abstraction layers
- Import patterns

---

## Success Metrics

Upon completion, verify:

✅ **Code Quality**
- [ ] No duplicate classes defined
- [ ] No duplicate functions with same logic
- [ ] Consistent error handling patterns
- [ ] All imports resolve correctly

✅ **Testing**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Test coverage maintained
- [ ] No new test failures

✅ **Maintainability**
- [ ] Code more readable
- [ ] Changes easier to make
- [ ] Single points of maintenance
- [ ] Clear module responsibilities

✅ **Performance**
- [ ] No regressions in latency
- [ ] Memory usage stable or improved
- [ ] Build times stable

---

## Timeline

| Phase | Task | Duration | Cumulative |
|-------|------|----------|-----------|
| 1 | SearchResult consolidation | 0.5h | 0.5h |
| 2 | Message formatting | 2h | 2.5h |
| 3 | Metadata extraction | 2.5h | 5h |
| 4 | Validation logic | 1.5h | 6.5h |
| 5 | Error handling | 1.5h | 8h |
| 6 | Test fixtures | 0.5h | 8.5h |
| Testing | Full test suite + verification | 1-2h | 9.5-10.5h |

**Total**: 8-10 hours

---

## Related Documents

- **DUPLICATION_ANALYSIS.md** - Overview of all duplication patterns
- **DUPLICATION_PATTERNS_2_3.md** - Detailed patterns 2 & 3 with examples
- **DUPLICATION_PATTERNS_4_5_6.md** - Detailed patterns 4, 5 & 6 with examples

