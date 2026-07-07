# Phase 1: Retriever Consolidation & Core Module Split

**Timeline:** Weeks 1-2  
**Goal:** Reduce 1,261 LOC of duplication, split optimization.py into focused modules  
**Estimated Impact:** -461 LOC duplicated, +40% maintainability

---

## Issue #1: Consolidate Retriever Implementations

### Current State (Problematic)

```
retriever/
├── retriever.py (355 LOC)
│   ├── SearchResult (duplicated)
│   ├── Retriever
│   └── Methods: search(), search_by_section(), filter_by_department()
│
├── retriever_advanced.py (549 LOC)
│   ├── SearchResult (duplicated - different)
│   ├── AdvancedRetriever
│   └── Methods: search_by_section(), filter_by_section() [DUPLICATE NAMES]
│
└── retrieval_pipeline.py (357 LOC)
    ├── RetrievalPipeline
    ├── Duplicates reranking logic
    └── No clear relationship to other retrievers
```

### Code Duplication Example 1: SearchResult Class

**retriever.py (line ~20)**
```python
class SearchResult:
    def __init__(self, chunk_id, text, metadata, similarity_score, rank=0):
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata
        self.similarity_score = similarity_score
        self.rank = rank
```

**retriever_advanced.py (line ~50)**
```python
class SearchResult:
    def __init__(self, chunk_id, text, metadata, score, rank=0, method="semantic"):
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata
        self.score = score  # Different name!
        self.rank = rank
        self.method = method
```

### Code Duplication Example 2: Search Logic

Both files implement `search_by_section()` differently without inheritance relationship.

### Refactoring Solution

**New Structure:**

```python
# retriever/base.py (NEW - 250 LOC)
"""Base retriever interface and common implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from core.abstractions.base import SearchResult as DomainSearchResult
from vectorstore.vectorstore import VectorStore
from core.logger import get_logger

logger = get_logger(__name__)


class RetrievalMethod(Enum):
    """Retrieval method types."""
    SEMANTIC = "semantic"
    BM25 = "bm25"
    HYBRID = "hybrid"
    METADATA = "metadata"


class BaseRetriever(ABC):
    """Abstract base retriever with common interface."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self._cache: Dict[str, List[DomainSearchResult]] = {}
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[DomainSearchResult]:
        """Search knowledge base."""
        pass
    
    def _apply_section_filter(self, results: List[DomainSearchResult], 
                             section: str) -> List[DomainSearchResult]:
        """Common filtering logic."""
        return [r for r in results if r.metadata.section == section]
    
    def _apply_department_filter(self, results: List[DomainSearchResult],
                                department: str) -> List[DomainSearchResult]:
        """Common filtering logic."""
        return [r for r in results if r.metadata.department == department]
    
    def _apply_score_threshold(self, results: List[DomainSearchResult],
                              threshold: float = 0.5) -> List[DomainSearchResult]:
        """Filter by confidence threshold."""
        return [r for r in results if r.similarity_score >= threshold]
    
    def _remove_duplicates(self, results: List[DomainSearchResult]) -> List[DomainSearchResult]:
        """Remove duplicate results based on content similarity."""
        seen = set()
        unique = []
        for result in results:
            if result.chunk_id not in seen:
                unique.append(result)
                seen.add(result.chunk_id)
        return unique


# retriever/semantic.py (REFACTORED - 280 LOC)
"""Semantic retriever using embeddings."""

from typing import List, Optional, Dict, Any
from retriever.base import BaseRetriever, RetrievalMethod
from core.abstractions.base import SearchResult, Metadata
from vectorstore.vectorstore import VectorStore
from embedding.adapters import EmbeddingAdapter
from core.logger import get_logger

logger = get_logger(__name__)


class SemanticRetriever(BaseRetriever):
    """Pure semantic search using embeddings."""
    
    def __init__(self, vector_store: VectorStore, embedding: EmbeddingAdapter):
        super().__init__(vector_store)
        self.embedding = embedding
    
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Semantic search using query embedding.
        
        Args:
            query: User query string
            top_k: Number of results to return
        
        Returns:
            Ranked list of SearchResult objects
        """
        logger.info(f"Semantic search: {query[:50]}...", extra={"query_len": len(query)})
        
        # Generate query embedding
        query_embedding = await self.embedding.embed(query)
        
        # Search vector store
        chunk_ids_with_scores = await self.vector_store.search(
            query_embedding,
            top_k=top_k
        )
        
        # Convert to domain objects
        results = []
        for rank, (chunk_id, score) in enumerate(chunk_ids_with_scores, 1):
            metadata_dict = await self.vector_store.get_metadata(chunk_id)
            metadata = self._dict_to_metadata(metadata_dict)
            chunk_text = await self.vector_store.get_text(chunk_id)
            
            result = SearchResult(
                chunk_id=chunk_id,
                text=chunk_text,
                metadata=metadata,
                similarity_score=score,
                rank=rank,
                retrieval_method=RetrievalMethod.SEMANTIC.value
            )
            results.append(result)
        
        return self._remove_duplicates(results)
    
    async def search_by_section(self, query: str, section: str, 
                               top_k: int = 5) -> List[SearchResult]:
        """Search within specific section."""
        all_results = await self.search(query, top_k=top_k * 2)
        return self._apply_section_filter(all_results, section)[:top_k]
    
    async def search_by_department(self, query: str, department: str,
                                  top_k: int = 5) -> List[SearchResult]:
        """Search within specific department."""
        all_results = await self.search(query, top_k=top_k * 2)
        return self._apply_department_filter(all_results, department)[:top_k]
    
    @staticmethod
    def _dict_to_metadata(data: Dict[str, Any]) -> Metadata:
        """Convert metadata dict to domain object."""
        return Metadata(
            source_url=data.get("source_url", ""),
            source_type=data.get("source_type", "webpage"),
            section=data.get("section", ""),
            department=data.get("department"),
            last_updated=data.get("last_updated"),
            version=data.get("version", "1.0"),
            custom_fields=data.get("custom_fields", {})
        )


# retriever/advanced.py (REFACTORED - 320 LOC)
"""Advanced retriever with hybrid search and reranking."""

from typing import List, Optional, Dict, Any, Tuple
from retriever.base import BaseRetriever, RetrievalMethod
from retriever.semantic import SemanticRetriever
from core.abstractions.base import SearchResult, Metadata
from vectorstore.vectorstore import VectorStore
from embedding.adapters import EmbeddingAdapter
from core.logger import get_logger

logger = get_logger(__name__)


class AdvancedRetriever(SemanticRetriever):
    """Advanced retriever with hybrid search, reranking, and metadata filtering."""
    
    def __init__(self, vector_store: VectorStore, embedding: EmbeddingAdapter,
                 enable_reranking: bool = True, enable_bm25: bool = False):
        super().__init__(vector_store, embedding)
        self.enable_reranking = enable_reranking
        self.enable_bm25 = enable_bm25
    
    async def hybrid_search(self, query: str, top_k: int = 5,
                           semantic_weight: float = 0.7) -> List[SearchResult]:
        """
        Hybrid search combining semantic and BM25.
        
        Args:
            query: User query
            top_k: Results to return
            semantic_weight: Weight for semantic search (0-1)
        """
        # Semantic results
        semantic_results = await self.search(query, top_k=top_k * 2)
        
        if not self.enable_bm25:
            return semantic_results[:top_k]
        
        # BM25 results (if enabled)
        bm25_results = await self._bm25_search(query, top_k=top_k * 2)
        
        # Combine results with weighted scores
        combined = self._combine_results(semantic_results, bm25_results, semantic_weight)
        
        if self.enable_reranking:
            combined = await self._rerank(combined, query)
        
        return combined[:top_k]
    
    async def search_with_filters(self, query: str, top_k: int = 5,
                                 section: Optional[str] = None,
                                 department: Optional[str] = None,
                                 min_score: float = 0.5) -> List[SearchResult]:
        """Search with multiple filters."""
        results = await self.search(query, top_k=top_k * 3)
        
        if section:
            results = self._apply_section_filter(results, section)
        if department:
            results = self._apply_department_filter(results, department)
        
        results = self._apply_score_threshold(results, min_score)
        return results[:top_k]
    
    async def _bm25_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """BM25 search implementation."""
        # TODO: Implement BM25 search
        return []
    
    def _combine_results(self, semantic: List[SearchResult],
                        bm25: List[SearchResult],
                        semantic_weight: float) -> List[SearchResult]:
        """Combine semantic and BM25 results."""
        combined_dict: Dict[str, SearchResult] = {}
        
        # Add semantic results
        for result in semantic:
            combined_dict[result.chunk_id] = result
            result.similarity_score *= semantic_weight
        
        # Add/merge BM25 results
        bm25_weight = 1.0 - semantic_weight
        for result in bm25:
            if result.chunk_id in combined_dict:
                combined_dict[result.chunk_id].similarity_score += result.similarity_score * bm25_weight
            else:
                result.similarity_score *= bm25_weight
                combined_dict[result.chunk_id] = result
        
        # Sort by score
        return sorted(combined_dict.values(), 
                     key=lambda r: r.similarity_score, 
                     reverse=True)
    
    async def _rerank(self, results: List[SearchResult], 
                     query: str) -> List[SearchResult]:
        """Rerank results using cross-encoder (optional)."""
        # TODO: Implement reranking with cross-encoder model
        return results


# retriever/pipeline.py (REFACTORED - 200 LOC)
"""Retrieval pipeline orchestrator."""

from typing import List, Dict, Any, Optional
from retriever.base import BaseRetriever
from retriever.semantic import SemanticRetriever
from retriever.advanced import AdvancedRetriever
from core.abstractions.base import SearchResult
from core.logger import get_logger
from enum import Enum

logger = get_logger(__name__)


class RetrievalPipeline:
    """
    Orchestrator for retrieval operations.
    
    Pure orchestration layer - delegates to retrievers.
    """
    
    def __init__(self, advanced_retriever: AdvancedRetriever):
        self.retriever = advanced_retriever
    
    async def search(self, query: str, top_k: int = 5, 
                    use_hybrid: bool = False) -> List[SearchResult]:
        """Execute search."""
        if use_hybrid:
            return await self.retriever.hybrid_search(query, top_k)
        else:
            return await self.retriever.search(query, top_k)
    
    async def search_with_context(self, query: str, context: Dict[str, Any],
                                 top_k: int = 5) -> List[SearchResult]:
        """Search with contextual filters."""
        section = context.get("section")
        department = context.get("department")
        min_score = context.get("min_score", 0.5)
        
        return await self.retriever.search_with_filters(
            query=query,
            top_k=top_k,
            section=section,
            department=department,
            min_score=min_score
        )
```

**LOC Reduction:**
- Before: 1,261 LOC across 3 files
- After: ~850 LOC across 4 files (clearer inheritance)
- **Removed Duplication:** 411 LOC

---

## Issue #2: Split core/optimization.py

### Current State: 2,513 LOC in Single File

```python
# core/optimization.py contains:
# - CacheStrategy, Cache, CacheEntry, CacheManager (~600 LOC)
# - RetryQueue, RetryTask, RetryPolicy (~400 LOC)
# - ParallelExecutor, RateLimiter (~300 LOC)
# - MemoryOptimizer, Compression (~250 LOC)
# - HealthMonitor, HealthCheck, HealthStatus (~200 LOC)
# - ShutdownHandler (~150 LOC)
# - StructuredLogger (~200 LOC)
# - Decorators: cached, retry, timed, log_correlation_id (~200 LOC)
```

### Refactoring Plan

```
core/optimization/
├── __init__.py               # Export API
├── caching/
│   ├── strategy.py          # CacheStrategy enum (30 LOC)
│   ├── entry.py             # CacheEntry dataclass (50 LOC)
│   ├── cache.py             # Cache implementation (280 LOC)
│   ├── manager.py           # CacheManager (150 LOC)
│   └── decorators.py        # @cached decorator (80 LOC)
│
├── retry/
│   ├── task.py              # RetryTask dataclass (40 LOC)
│   ├── policy.py            # RetryPolicy (100 LOC)
│   ├── queue.py             # RetryQueue (200 LOC)
│   └── decorators.py        # @retry decorator (60 LOC)
│
├── parallel/
│   ├── executor.py          # ParallelExecutor (180 LOC)
│   ├── rate_limiter.py      # RateLimiter (120 LOC)
│   └── pool_manager.py      # ThreadPool management (50 LOC)
│
├── memory/
│   ├── optimizer.py         # MemoryOptimizer (150 LOC)
│   └── compression.py       # Compression utils (100 LOC)
│
├── health/
│   ├── status.py            # HealthStatus enum (30 LOC)
│   ├── check.py             # HealthCheck dataclass (50 LOC)
│   └── monitor.py           # HealthMonitor (150 LOC)
│
├── shutdown/
│   └── handler.py           # ShutdownHandler (120 LOC)
│
├── logging/
│   └── structured.py        # StructuredLogger (180 LOC)
│
└── decorators/
    ├── __init__.py          # Re-exports all decorators
    ├── cached.py            # @cached (80 LOC)
    ├── retry.py             # @retry (60 LOC)
    ├── timed.py             # @timed (50 LOC)
    └── correlation_id.py    # @log_correlation_id (40 LOC)
```

### Example: Cache Module After Split

```python
# core/optimization/caching/strategy.py
from enum import Enum

class CacheStrategy(Enum):
    """Cache eviction strategy."""
    LRU = "lru"
    MRU = "mru"
    FIFO = "fifo"
    TTL = "ttl"


# core/optimization/caching/entry.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    ttl: Optional[timedelta] = None
    access_count: int = 0
    
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return datetime.now() - self.created_at > self.ttl
    
    def update_access(self) -> None:
        self.last_accessed = datetime.now()
        self.access_count += 1


# core/optimization/caching/cache.py (280 LOC - focused)
from typing import Dict, Optional, Any
from collections import OrderedDict
from datetime import timedelta
from .strategy import CacheStrategy
from .entry import CacheEntry
from core.logger import get_logger

logger = get_logger(__name__)

class Cache:
    """Multi-tier cache with configurable eviction."""
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.LRU):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            return None
        
        entry.update_access()
        # Move to end for LRU
        if self.strategy == CacheStrategy.LRU:
            self.cache.move_to_end(key)
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        entry = CacheEntry(key=key, value=value, ttl=ttl)
        self.cache[key] = entry
        
        if len(self.cache) > self.max_size:
            self._evict()
    
    def _evict(self) -> None:
        """Evict entry based on strategy."""
        if self.strategy == CacheStrategy.LRU:
            evicted_key = next(iter(self.cache))  # First (oldest) item
        elif self.strategy == CacheStrategy.FIFO:
            evicted_key = next(iter(self.cache))
        elif self.strategy == CacheStrategy.MRU:
            # Most recently used at end
            evicted_key = next(reversed(self.cache))
        else:  # TTL
            evicted_key = next(iter(self.cache))
        
        del self.cache[evicted_key]
        logger.debug(f"Evicted cache entry: {evicted_key}")


# core/optimization/caching/decorators.py
import functools
from typing import Callable, Any, Optional
from datetime import timedelta
from .cache import Cache
from core.logger import get_logger

logger = get_logger(__name__)
_global_cache = Cache(max_size=5000)

def cached(ttl: Optional[timedelta] = None):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name + args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache hit
            cached_result = _global_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_result
            
            # Cache miss - compute and store
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
```

**Benefits:**
- Each module focused on single concern
- Easier to test individual components
- Clearer imports and dependencies
- Can swap implementations (e.g., Redis cache instead of in-memory)
- **LOC: 2,513 → ~1,800** (organized and modular)

---

## Implementation Order

1. **Week 1:**
   - Create `core/abstractions/` interfaces
   - Create `core/di_container.py`
   - Split `core/optimization.py` into 8 modules
   - Update all imports

2. **Week 2:**
   - Consolidate retrievers (4 files)
   - Add type hints to all new modules
   - Run type checking
   - Update tests for new structure

---

## Validation Checklist

- [ ] All tests pass with new structure
- [ ] No circular imports
- [ ] All interfaces properly documented
- [ ] Type hints on 100% of new code
- [ ] Reduction in LOC verified
- [ ] Performance benchmarks maintained
