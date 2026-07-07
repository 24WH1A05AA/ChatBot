# Clean Architecture Refactoring Plan - College FAQ Chatbot

**Created:** July 3, 2026  
**Status:** Detailed Architecture Design  
**Target Quality:** 72/100 → 88/100  
**Estimated Timeline:** 4 weeks (4 phases)

---

## Executive Summary

Based on comprehensive code analysis, this document provides a detailed clean architecture refactoring plan addressing:
- **4 major architecture issues** (bloated modules, duplicate retrievers, scattered file-handling, evaluation complexity)
- **4 code duplication patterns** (1,261+ LOC of redundant code)
- **5 performance bottlenecks** (cache optimization, async I/O, query efficiency)
- **5 security vulnerabilities** (prompt injection, API key exposure, rate limiting)
- **Type hints and PEP 8 gaps**

---

## Part 1: Abstraction Layers & Core Interfaces

### 1.1 Domain Layer - Shared Abstractions

Create common interfaces that all modules depend on:

```python
# core/abstractions/base.py
"""Base interfaces for clean architecture."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from dataclasses import dataclass
from datetime import datetime

T = TypeVar("T")
K = TypeVar("K")

# ============================================================================
# DOCUMENT & CHUNK ABSTRACTIONS
# ============================================================================

@dataclass
class Metadata:
    """Unified metadata structure across all layers."""
    source_url: str
    source_type: str  # 'webpage', 'pdf', 'document'
    section: str
    department: Optional[str] = None
    last_updated: Optional[datetime] = None
    version: str = "1.0"
    custom_fields: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_fields is None:
            self.custom_fields = {}


@dataclass
class Document:
    """Unified document representation."""
    id: str
    content: str
    metadata: Metadata
    language: str = "en"
    processed_at: datetime = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now()


@dataclass
class Chunk:
    """Document chunk with embedding reference."""
    id: str
    content: str
    document_id: str
    metadata: Metadata
    position: int  # Position in original document
    embedding_id: Optional[str] = None
    
    
# ============================================================================
# SEARCH RESULT ABSTRACTION (replaces duplicated SearchResult)
# ============================================================================

@dataclass
class SearchResult:
    """Unified search result across all retrievers."""
    chunk_id: str
    text: str
    metadata: Metadata
    similarity_score: float
    rank: int = 0
    retrieval_method: str = "semantic"  # 'semantic', 'bm25', 'hybrid', etc.
    confidence: float = 1.0
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if result meets confidence threshold."""
        return self.confidence >= 0.7 and self.similarity_score >= 0.5


# ============================================================================
# CORE SERVICE INTERFACES
# ============================================================================

class Repository(ABC, Generic[T, K]):
    """Base repository pattern for all data access."""
    
    @abstractmethod
    async def get(self, id: K) -> Optional[T]:
        """Retrieve single item by ID."""
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any] = None) -> List[T]:
        """List items with optional filters."""
        pass
    
    @abstractmethod
    async def save(self, item: T) -> K:
        """Save item, return ID."""
        pass
    
    @abstractmethod
    async def delete(self, id: K) -> bool:
        """Delete item by ID."""
        pass


class VectorStorePort(ABC):
    """Port for vector storage abstraction."""
    
    @abstractmethod
    async def store_embedding(self, chunk_id: str, embedding: List[float], 
                            metadata: Dict[str, Any]) -> None:
        """Store a single embedding."""
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], 
                    top_k: int = 10, 
                    metadata_filter: Dict[str, Any] = None) -> List[Tuple[str, float]]:
        """Search by embedding, return (chunk_id, similarity) pairs."""
        pass
    
    @abstractmethod
    async def delete_embedding(self, chunk_id: str) -> bool:
        """Delete single embedding."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all embeddings."""
        pass


class EmbeddingPort(ABC):
    """Port for embedding generation."""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Dimension of embeddings."""
        pass


class LLMPort(ABC):
    """Port for LLM interactions."""
    
    @abstractmethod
    async def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate text response."""
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str) -> str:
        """Stream text generation."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Current model name."""
        pass


class CrawlerPort(ABC):
    """Port for website crawling."""
    
    @abstractmethod
    async def crawl(self, url: str, depth: int = 0) -> List[Document]:
        """Crawl website and return documents."""
        pass
    
    @abstractmethod
    async def is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        pass


# ============================================================================
# USECASE/ORCHESTRATION INTERFACES
# ============================================================================

class DocumentIngestionUseCase(ABC):
    """Use case: Ingest documents into knowledge base."""
    
    @abstractmethod
    async def ingest(self, documents: List[Document]) -> Dict[str, Any]:
        """Ingest documents. Returns stats."""
        pass


class SemanticSearchUseCase(ABC):
    """Use case: Search knowledge base."""
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Semantic search. Returns ranked results."""
        pass


class ChatUseCase(ABC):
    """Use case: Chat with context."""
    
    @abstractmethod
    async def chat(self, query: str, conversation_id: str) -> Dict[str, Any]:
        """Generate contextual response. Returns message + citations."""
        pass


# ============================================================================
# CONCERN INTERFACES
# ============================================================================

class SecurityService(ABC):
    """Cross-cutting security concern."""
    
    @abstractmethod
    def validate_input(self, text: str, context: str = "general") -> bool:
        """Validate input for injection attacks."""
        pass
    
    @abstractmethod
    def sanitize_output(self, text: str) -> str:
        """Sanitize LLM output."""
        pass


class CacheService(ABC):
    """Cross-cutting caching concern."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set in cache with TTL."""
        pass
    
    @abstractmethod
    def invalidate(self, pattern: str) -> None:
        """Invalidate cache by pattern."""
        pass


class LoggingService(ABC):
    """Cross-cutting logging concern."""
    
    @abstractmethod
    def log_operation(self, operation: str, metadata: Dict[str, Any]) -> None:
        """Log operation with metadata."""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with context."""
        pass
```

---

## Part 2: Dependency Injection & Container

Create a DI container to manage dependencies:

```python
# core/di_container.py
"""Dependency injection container for clean architecture."""

from typing import Any, Callable, Dict, Optional, Type, TypeVar
import asyncio
from abc import ABC

T = TypeVar("T")

class DIContainer:
    """Simple but effective DI container."""
    
    def __init__(self):
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._dependencies: Dict[str, Type] = {}
    
    def register_singleton(self, interface: Type[T], 
                          implementation: T) -> None:
        """Register singleton instance."""
        self._singletons[interface.__name__] = implementation
    
    def register_factory(self, interface: Type[T], 
                        factory: Callable[[], T]) -> None:
        """Register factory function."""
        self._factories[interface.__name__] = factory
    
    def register_dependency(self, interface: Type[T], 
                           implementation: Type[T]) -> None:
        """Register interface to implementation mapping."""
        self._dependencies[interface.__name__] = implementation
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve dependency."""
        name = interface.__name__
        
        # Check singleton
        if name in self._singletons:
            return self._singletons[name]
        
        # Check factory
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance
            return instance
        
        # Check dependency mapping
        if name in self._dependencies:
            impl_class = self._dependencies[name]
            instance = impl_class()
            self._singletons[name] = instance
            return instance
        
        raise ValueError(f"No registration for {interface.__name__}")
    
    async def resolve_async(self, interface: Type[T]) -> T:
        """Resolve async dependency."""
        instance = self.resolve(interface)
        if hasattr(instance, 'initialize'):
            await instance.initialize()
        return instance


# Application Bootstrap
def create_container() -> DIContainer:
    """Create and configure DI container."""
    container = DIContainer()
    
    # Register core services
    from config.settings import Settings
    settings = Settings()
    container.register_singleton(Settings, settings)
    
    # Register repositories
    from ingestion.repositories import DocumentRepository
    container.register_factory(
        DocumentRepository,
        lambda: DocumentRepository()
    )
    
    # Register ports (interfaces to implementations)
    from vectorstore.adapters import ChromaVectorStore
    from core.abstractions.base import VectorStorePort
    container.register_dependency(VectorStorePort, ChromaVectorStore)
    
    from embedding.adapters import OpenAIEmbedding
    from core.abstractions.base import EmbeddingPort
    container.register_dependency(EmbeddingPort, OpenAIEmbedding)
    
    from llm.adapters import OpenAILLM
    from core.abstractions.base import LLMPort
    container.register_dependency(LLMPort, OpenAILLM)
    
    # Register use cases
    from ingestion.usecases import DocumentIngestionUseCaseImpl
    from core.abstractions.base import DocumentIngestionUseCase
    container.register_dependency(
        DocumentIngestionUseCase,
        DocumentIngestionUseCaseImpl
    )
    
    return container
```

---

## Part 3: Layer Architecture

Define clear separation of concerns:

```python
# docs/ARCHITECTURE.md - Layer definitions

# ARCHITECTURE LAYERS (Hexagonal/Onion)
#
# ┌─────────────────────────────────────────────────────────┐
# │                    PRESENTATION LAYER                   │
# │  (streamlit_ui/, admin/) - UI components, routing       │
# └────────────────────┬────────────────────────────────────┘
#                      │
# ┌────────────────────▼────────────────────────────────────┐
# │                   APPLICATION LAYER                     │
# │  (orchestrators, controllers) - Coordinates use cases   │
# └────────────────────┬────────────────────────────────────┘
#                      │
# ┌────────────────────▼────────────────────────────────────┐
# │                      DOMAIN LAYER                       │
# │  (core/abstractions, models) - Core business logic,     │
# │  Use cases, Entities, Value Objects                     │
# └────────────────────┬────────────────────────────────────┘
#                      │
# ┌────────────────────▼────────────────────────────────────┐
# │                   INFRASTRUCTURE LAYER                  │
# │  (adapters, repositories, external services)            │
# │  - Vector Store (ChromaDB)                              │
# │  - Embeddings (OpenAI)                                  │
# │  - LLM (OpenAI)                                          │
# │  - Web Crawler (Crawl4AI)                                │
# └─────────────────────────────────────────────────────────┘
#
# CROSS-CUTTING CONCERNS:
# - core/security: Input validation, injection protection
# - core/caching: Multi-tier cache layer
# - core/logging: Structured logging
# - core/error_handling: Custom exceptions
# - core/monitoring: Health checks, metrics


# MODULE STRUCTURE

root/
├── core/                          # Domain Layer
│   ├── abstractions/
│   │   ├── base.py               # Core interfaces
│   │   ├── ports.py              # External service interfaces
│   │   └── usecases.py           # Use case interfaces
│   ├── domain/
│   │   ├── entities.py           # Domain models
│   │   ├── value_objects.py      # Value objects
│   │   └── exceptions.py         # Domain exceptions
│   ├── security/
│   │   ├── injection_detector.py
│   │   ├── output_validator.py
│   │   └── rate_limiter.py
│   ├── caching/
│   │   ├── cache.py
│   │   ├── strategies.py
│   │   └── decorators.py
│   ├── logging/
│   │   └── structured_logger.py
│   ├── health/
│   │   └── health_check.py
│   ├── error_handling/
│   │   ├── exceptions.py
│   │   └── handlers.py
│   └── di_container.py
│
├── ingestion/                     # Ingestion Use Case
│   ├── usecases.py               # DocumentIngestionUseCase impl
│   ├── repositories.py           # Document repository
│   ├── processors/
│   │   ├── chunker.py
│   │   ├── metadata_extractor.py
│   │   └── validator.py
│   └── models.py
│
├── retrieval/                     # Retrieval Use Case
│   ├── usecases.py               # SemanticSearchUseCase impl
│   ├── base.py                   # BaseRetriever
│   ├── semantic_retriever.py     # SemanticRetriever
│   ├── advanced_retriever.py     # Advanced features
│   ├── reranker.py               # Result reranking
│   └── models.py
│
├── chat/                          # Chat Use Case
│   ├── usecases.py               # ChatUseCase impl
│   ├── message_formatter.py      # Unified formatting
│   ├── conversation_manager.py
│   └── response_generator.py
│
├── crawler/                       # Crawling Use Case
│   ├── orchestrator.py           # Coordinator
│   ├── web_crawler.py            # Main crawler
│   ├── file_handler.py           # Unified file ops
│   ├── content_processors/
│   │   ├── html_processor.py
│   │   ├── pdf_processor.py
│   │   └── document_processor.py
│   ├── metadata/
│   │   └── extractor.py
│   └── validators/
│       └── url_validator.py
│
├── vectorstore/                   # Vector Store Infrastructure
│   ├── ports.py                  # VectorStorePort
│   ├── adapters/
│   │   └── chroma_adapter.py     # ChromaDB adapter
│   └── repositories.py
│
├── embedding/                     # Embedding Infrastructure
│   ├── ports.py                  # EmbeddingPort
│   ├── adapters/
│   │   └── openai_adapter.py     # OpenAI adapter
│   └── cache_manager.py
│
├── llm/                           # LLM Infrastructure
│   ├── ports.py                  # LLMPort
│   ├── adapters/
│   │   └── openai_adapter.py     # OpenAI adapter
│   └── token_counter.py
│
├── evaluation/                    # Evaluation Infrastructure
│   ├── metrics/
│   │   ├── base.py               # BaseMetric
│   │   ├── ragas.py              # RAGAS metrics
│   │   └── custom.py             # Custom metrics
│   ├── runner.py
│   └── report_generator.py
│
├── analytics/                     # Analytics Infrastructure
│   ├── collector.py
│   └── reporters.py
│
├── scheduler/                     # Background Jobs
│   ├── base.py
│   ├── crawler_scheduler.py
│   └── maintenance_scheduler.py
│
├── memory/                        # Conversation Memory
│   ├── storage.py
│   └── managers.py
│
├── prompts/                       # Prompt Templates
│   ├── base.py
│   ├── templates/
│   │   ├── system.py
│   │   ├── evaluation.py
│   │   └── retrieval.py
│   └── formatter.py              # Unified formatting
│
├── application/                   # Application Layer
│   ├── orchestrators/
│   │   ├── ingestion_orchestrator.py
│   │   ├── search_orchestrator.py
│   │   └── chat_orchestrator.py
│   └── services.py
│
├── interfaces/                    # Presentation Layer
│   ├── streamlit/
│   │   ├── pages/
│   │   │   ├── chat.py
│   │   │   ├── admin.py
│   │   │   └── analytics.py
│   │   └── components.py
│   ├── api/
│   │   ├── routes.py
│   │   └── middleware.py
│   └── cli/
│       └── commands.py
│
├── config/                        # Configuration
│   ├── settings.py               # Settings with validation
│   └── constants.py
│
├── tests/                         # Test Suite
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
│
└── app.py                         # Entry point
```

This is Part 1 (Abstractions). Next parts will cover: Dependency Injection, Retriever Consolidation, and Performance/Security fixes.
