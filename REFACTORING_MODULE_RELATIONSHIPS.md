# Module Relationships & Dependency Map

**Purpose:** Visualize architecture dependencies and module communications  
**Goal:** Ensure clean separation of concerns and minimal coupling

---

## 1. Dependency Graph (Clean Architecture)

### Layer 0: Core Domain Abstractions (No dependencies outside)

```
core/abstractions/
├── base.py (Interfaces: Repository, VectorStorePort, EmbeddingPort, LLMPort, CrawlerPort)
├── usecases.py (Use case interfaces: DocumentIngestionUseCase, SemanticSearchUseCase, ChatUseCase)
└── entities.py (Domain models: Document, Chunk, Metadata, SearchResult)

DEPENDENCIES: None (except typing, abc)
USED BY: All other layers
```

### Layer 1: Cross-Cutting Concerns (Domain)

```
core/domain/
├── exceptions.py (Domain exceptions)
├── value_objects.py
├── entities.py
├── metadata.py (MetadataExtractor - SINGLE SOURCE OF TRUTH)
└── validation.py (Validator - CENTRALIZED PATTERNS)

core/security/
├── injection_detector.py (PromptInjectionDetector)
├── output_validator.py (LLMOutputValidator)
├── rate_limiter.py (RateLimiter)
└── sanitizer.py

core/caching/
├── strategy.py (CacheStrategy enum)
├── entry.py (CacheEntry dataclass)
├── cache.py (Cache implementation)
├── manager.py (CacheManager)
└── decorators.py (@cached, @retry decorators)

core/logging/
├── structured_logger.py (StructuredLogger)
└── secure_logger.py (SensitiveDataRedactor)

DEPENDENCIES: Only base abstractions + typing
USED BY: All infrastructure and application layers
```

### Layer 2: Infrastructure Adapters (Implement ports)

```
vectorstore/
├── ports.py (VectorStorePort abstract)
├── adapters/
│   └── chroma_adapter.py (implements VectorStorePort)
└── repositories.py (VectorStore repository)

embedding/
├── ports.py (EmbeddingPort abstract)
├── adapters/
│   └── openai_adapter.py (implements EmbeddingPort)
└── cache_manager.py (Embedding cache layer)

llm/
├── ports.py (LLMPort abstract)
├── adapters/
│   └── openai_adapter.py (implements LLMPort)
├── token_counter.py
└── output_validator.py (wraps LLMPort)

crawler/
├── ports.py (CrawlerPort abstract)
├── orchestrator.py (CrawlerOrchestrator)
├── web_crawler.py (implements CrawlerPort)
├── file_handler.py (AsyncFileHandler - UNIFIED FILE OPS)
├── content_processors/ (HTML, PDF, Document processors)
├── metadata/ (MetadataExtractor calls)
└── validators/ (Uses core/domain/validation.py)

DEPENDENCIES: 
  - core/abstractions (implement ports)
  - core/domain (validators, metadata, security)
  - core/caching (cache results)
  - External libraries (openai, chromadb, crawl4ai, etc.)
USED BY: Application layer
```

### Layer 3: Application Services (Orchestration)

```
ingestion/
├── usecases.py (DocumentIngestionUseCaseImpl implements DocumentIngestionUseCase)
├── repositories.py (DocumentRepository)
├── processors/
│   ├── chunker.py
│   ├── metadata_extractor.py (CALLS core/domain/metadata.py)
│   └── validator.py (CALLS core/domain/validation.py)
└── models.py

retrieval/
├── usecases.py (SemanticSearchUseCaseImpl implements SemanticSearchUseCase)
├── base.py (BaseRetriever - orchestrates VectorStorePort, EmbeddingPort)
├── semantic.py (SemanticRetriever extends BaseRetriever)
├── advanced.py (AdvancedRetriever extends SemanticRetriever)
├── reranker.py
└── models.py

chat/
├── usecases.py (ChatUseCaseImpl implements ChatUseCase)
├── message_formatter.py (CALLS prompts/formatter.py for unified formatting)
├── conversation_manager.py
└── response_generator.py (CALLS llm/LLMPort, security for validation)

prompts/
├── formatter.py (MessageFormatter - UNIFIED FOR ALL MODULES)
├── templates/
│   ├── system.py
│   ├── evaluation.py
│   └── retrieval.py
└── prompt_orchestrator.py

evaluation/
├── metrics/ (BaseMetric, RAGASMetrics, CustomMetrics)
├── runner.py
├── report_generator.py
└── (Orchestrates: retrieval/usecases, llm/LLMPort, metrics)

DEPENDENCIES:
  - core/abstractions (implement use case interfaces)
  - core/domain (entities, metadata, validation, security)
  - core/caching (cache expensive operations)
  - Infrastructure layer (ports)
  - Sibling services (chat calls retrieval, etc.)
USED BY: Controllers/Presenters
```

### Layer 4: Presentation Layer

```
interfaces/
├── streamlit_ui/
│   ├── pages/ (chat, admin, analytics)
│   └── components.py
├── api/
│   ├── routes.py (FastAPI routes)
│   └── middleware.py
└── cli/
    └── commands.py

DEPENDENCIES:
  - Application layer (orchestrators, use cases)
  - core/domain (models, exceptions)
  - core/security (rate limiting)
  - External: streamlit, fastapi, typer

USED BY: End users
```

### Layer 5: Bootstrap & Configuration

```
config/
├── settings.py (Settings with validation)
└── constants.py

app.py (Entry point)

core/di_container.py (DI setup)

DEPENDENCIES: All layers (for DI setup)
```

---

## 2. Module Communication Patterns

### Pattern 1: Use Case Flow (Ingestion)

```
User Input (Streamlit UI)
    ↓
interfaces/streamlit_ui/pages/admin.py
    ↓ calls
application/orchestrators/ingestion_orchestrator.py
    ↓ uses
ingestion/usecases.py::DocumentIngestionUseCaseImpl
    ├─ calls
    │  ingestion/repositories.py::DocumentRepository
    │  ingestion/processors/chunker.py
    │  ingestion/processors/validator.py (calls core/domain/validation.py)
    │  ingestion/processors/metadata_extractor.py (calls core/domain/metadata.py)
    │
    └─ delegates to
       vectorstore/adapters/chroma_adapter.py (implements VectorStorePort)
       embedding/adapters/openai_adapter.py (implements EmbeddingPort)
           ├─ caches results via core/caching/cache.py
           └─ validates via core/security/

Result: indexed documents in vectorstore/
```

### Pattern 2: Retrieval Flow

```
User Query (Streamlit UI)
    ↓
interfaces/streamlit_ui/pages/chat.py
    ↓ calls
application/orchestrators/search_orchestrator.py
    ↓ uses
retrieval/usecases.py::SemanticSearchUseCaseImpl
    ├─ uses
    │  retrieval/advanced.py::AdvancedRetriever
    │  retrieval/semantic.py::SemanticRetriever (extends base.py)
    │  retrieval/base.py::BaseRetriever
    │
    ├─ depends on
    │  vectorstore/adapters/chroma_adapter.py (VectorStorePort)
    │  embedding/adapters/openai_adapter.py (EmbeddingPort)
    │
    ├─ caches via
    │  core/caching/cache.py (@cached decorator)
    │
    └─ filters/validates via
       core/domain/metadata.py
       core/security/

Results: List[SearchResult] with citations
```

### Pattern 3: Chat Flow

```
User Message (Streamlit UI)
    ↓
interfaces/streamlit_ui/pages/chat.py
    ↓ calls
core/security/injection_detector.py (validates input)
    ↓ if safe, calls
application/orchestrators/chat_orchestrator.py
    ├─ uses
    │  retrieval/usecases.py (get context)
    │  chat/usecases.py::ChatUseCaseImpl
    │
    ├─ in ChatUseCase:
    │  chat/message_formatter.py (unified formatting - calls prompts/formatter.py)
    │  llm/adapters/openai_adapter.py (LLMPort - generate response)
    │  core/security/output_validator.py (validate LLM output)
    │
    └─ returns
       FormattedMessage with citations

    ├─ caches via
    │  core/caching/cache.py
    │
    └─ logs via
       core/logging/secure_logger.py (with redaction)
```

### Pattern 4: Crawler Integration

```
Admin: "Crawl website" (Streamlit UI)
    ↓
interfaces/streamlit_ui/pages/admin.py
    ↓ calls
scheduler/scheduled_crawler.py
    ├─ uses
    │  crawler/orchestrator.py::CrawlerOrchestrator
    │
    ├─ orchestrator uses
    │  crawler/web_crawler.py (implements CrawlerPort)
    │  crawler/file_handler.py (UNIFIED async file ops)
    │  crawler/content_processors/ (HTML, PDF, Document)
    │  crawler/metadata/extractor.py (calls core/domain/metadata.py)
    │  core/domain/validation.py (URL validation)
    │
    └─ returns List[Document]
        ↓
        ingestion/usecases.py (ingest documents)
```

---

## 3. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
│  (streamlit_ui/, api/, cli/)                                    │
└──────────────┬──────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                   APPLICATION ORCHESTRATION                      │
│  (application/orchestrators/)                                   │
└──────────────┬──────────────────────────────────────────────────┘
               │
       ┌───────┴───────┬──────────┐
       │               │          │
   ┌───▼────┐  ┌──────▼──┐  ┌───▼───────┐
   │Ingestion│  │Retrieval│  │   Chat    │
   │UseCase  │  │UseCase  │  │  UseCase  │
   └───┬────┘  └──────┬──┘  └───┬───────┘
       │              │          │
       ├──────────────┼──────────┤
       │              │          │
       │         ┌────▼──────┐   │
       │         │ Prompts   │   │
       │         │ Formatter │   │
       │         └───────────┘   │
       │                         │
   ┌───▼──────────────────────────▼──────────────────────┐
   │         DOMAIN SERVICES (Cross-Cutting)             │
   ├───────────────────────────────────────────────────┤
   │ ├─ Security (injection detector, rate limiter)    │
   │ ├─ Caching (multi-tier cache)                     │
   │ ├─ Logging (structured, secure)                   │
   │ ├─ Validation (centralized patterns)              │
   │ └─ Metadata (unified extraction)                  │
   └───┬──────────────────────────────────────────────────┘
       │
       ├──────────────┬─────────────────┬──────────────────┐
       │              │                 │                  │
   ┌───▼──┐      ┌────▼──┐        ┌────▼──┐        ┌────▼──┐
   │Vector │      │Embedding│      │  LLM  │        │Crawler │
   │Store  │      │Service  │      │Service│        │Service │
   │Adapter│      │Adapter  │      │Adapter│        │Adapter │
   └───┬──┘      └────┬──┘        └────┬──┘        └────┬──┘
       │              │                 │                  │
       └──────────────┼─────────────────┼──────────────────┘
                      │
                ┌─────▼─────────┐
                │  External APIs │
                │  - ChromaDB    │
                │  - OpenAI      │
                │  - Crawl4AI    │
                └────────────────┘
```

---

## 4. Coupling Analysis

### Low Coupling (Good ✅)

```
core/abstractions/ → Nothing (foundation)
core/domain/ → core/abstractions, typing
core/security/ → core/domain
core/caching/ → core/domain
vectorstore/adapters/ → core/abstractions (implements port)
embedding/adapters/ → core/abstractions (implements port)
```

### Medium Coupling (Acceptable)

```
ingestion/usecases/ → retrieval/usecases (for context in some cases)
chat/usecases/ → retrieval/usecases (must get context)
retrieval/advanced → retrieval/semantic (inheritance)
```

### High Coupling (To Eliminate)

```
BEFORE: Multiple retriever files with circular references
AFTER: Single inheritance chain (base → semantic → advanced)

BEFORE: File handling in 8 different modules
AFTER: crawler/file_handler.py (single source)

BEFORE: Metadata extraction duplicated
AFTER: core/domain/metadata.py (single source)

BEFORE: Message formatting in 5+ places
AFTER: prompts/formatter.py (single source)
```

---

## 5. Migration Strategy

### Step 1: Create Foundation (Week 1)

```bash
# Phase 1a: Create abstractions
mkdir -p core/abstractions
touch core/abstractions/{__init__.py,base.py,usecases.py,entities.py}

# Phase 1b: Create domain layer
mkdir -p core/domain
touch core/domain/{__init__.py,metadata.py,validation.py,exceptions.py}

# Phase 1c: Create DI container
touch core/di_container.py

# Verify: No imports from infrastructure yet
```

### Step 2: Build Infrastructure (Week 1-2)

```bash
# Create adapters that implement ports
mkdir -p vectorstore/adapters embedding/adapters llm/adapters
mkdir -p crawler/{content_processors,metadata,validators}

# Key: These ONLY implement abstract ports
# These CAN depend on external libraries
```

### Step 3: Implement Application Layer (Week 2-3)

```bash
# Create orchestrators
mkdir -p application/orchestrators
touch application/orchestrators/{ingestion,search,chat}_orchestrator.py

# Create unified modules (replaces duplicates)
touch prompts/formatter.py
touch crawler/file_handler.py

# Key: These orchestrate adapters and ports
# These depend only on abstractions and domain
```

### Step 4: Update Presentation (Week 3-4)

```bash
# Update all UI to use orchestrators
# Update all old imports to use new modules

# Verify clean separation:
# UI -> Orchestrators -> Use Cases -> Domain -> Adapters -> External
```

---

## 6. Import Guidelines

### ❌ PROHIBITED IMPORTS

```python
# From infrastructure back to domain
from llm.adapters import OpenAILLM  # In domain layer
from vectorstore.adapters import ChromaDB  # In domain layer

# Circular imports
from chat.usecases import ChatUseCase
from retrieval.usecases import SearchUseCase

# From sibling use cases
from ingestion.usecases import DocumentIngestionUseCase
from retrieval.usecases import SemanticSearchUseCase  # Can't cross-import

# From presentation to infrastructure (skip orchestration)
from streamlit_ui.pages import chat
from vectorstore.adapters import ChromaDB  # Must go through app layer
```

### ✅ ALLOWED IMPORTS

```python
# Domain imports domain
from core.abstractions.base import SearchResult, VectorStorePort
from core.domain.metadata import MetadataExtractor
from core.domain.validation import Validator

# Infrastructure implements domain
from core.abstractions.base import VectorStorePort
class ChromaVectorStore(VectorStorePort): ...

# Application orchestrates
from ingestion.usecases import DocumentIngestionUseCaseImpl
from retrieval.usecases import SemanticSearchUseCaseImpl
from core.security.injection_detector import PromptInjectionDetector

# Presentation calls application
from application.orchestrators.chat_orchestrator import ChatOrchestrator
from core.security.rate_limiter import RateLimiter
```

---

## 7. Validation Tests

```python
# tests/test_architecture.py
"""Verify architecture boundaries."""

def test_no_circular_imports():
    """Ensure no circular dependencies."""
    # Import all modules and verify no circular refs
    pass

def test_domain_independence():
    """Ensure core/domain has no infra deps."""
    import importlib
    core_domain = importlib.import_module('core.domain')
    # Assert no references to 'openai', 'chromadb', 'streamlit'
    pass

def test_adapter_implementation():
    """Ensure adapters implement ports."""
    from core.abstractions.base import VectorStorePort
    from vectorstore.adapters.chroma_adapter import ChromaVectorStore
    
    assert issubclass(ChromaVectorStore, VectorStorePort)

def test_orchestrator_communication():
    """Test proper use of orchestrators."""
    from application.orchestrators.chat_orchestrator import ChatOrchestrator
    from retrieval.usecases import SemanticSearchUseCaseImpl
    
    # Orchestrator should coordinate use cases
    orchestrator = ChatOrchestrator()
    assert orchestrator.search_use_case is not None
```

---

## 8. Dependency Resolution Table

| Component | Should Know About | Should NOT Know About |
|-----------|-------------------|----------------------|
| **core/domain/** | typing, enums | External libs, adapters, UI |
| **core/security/** | core/domain | LLM details, UI specifics |
| **core/caching/** | core/domain | Specific data types |
| **Adapters** | core/abstractions, external libs | Other adapters, UI |
| **Use Cases** | core/abstractions, core/domain, adapters | UI, external libs directly |
| **Orchestrators** | Use cases, core/security | Implementation details |
| **UI** | Orchestrators, models | Adapters, databases |

---

## 9. Completeness Checklist

- [ ] All ports defined in `core/abstractions/`
- [ ] All adapters implement exactly one port
- [ ] No direct imports from adapters in application layer
- [ ] All use cases implement use case interfaces
- [ ] Message formatting unified in `prompts/formatter.py`
- [ ] Metadata extraction unified in `core/domain/metadata.py`
- [ ] Validation patterns centralized in `core/domain/validation.py`
- [ ] File handling unified in `crawler/file_handler.py`
- [ ] DI container in `core/di_container.py`
- [ ] Security validators used consistently
- [ ] No circular dependencies detected
- [ ] Type hints 100% on new modules
- [ ] All tests passing
- [ ] Architecture documented in `ARCHITECTURE.md`
