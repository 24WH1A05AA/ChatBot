# Optimization Implementation Guide

## Quick Wins (2-4 Hours) - 30-40% Performance Gain

### 1. Query Result Caching (1-2 Hours)

**File**: `retriever/retrieval_pipeline.py`

```python
# BEFORE: No caching
class RetrievalPipeline:
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        # Every identical query does full search
        results = self.vector_store.query(...)
        return results

# AFTER: With caching
from core.optimization import cached

class RetrievalPipeline:
    @cached(ttl_seconds=3600, max_size=2000)
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        # Identical queries return cached results (~10ms vs 1000ms)
        results = self.vector_store.query(...)
        return results
```

**Verification**:
```bash
# Before
pytest tests/test_retriever.py -v --durations=10
# Should show ~1000ms per query

# After  
pytest tests/test_retriever.py -v --durations=10
# Should show ~10ms for duplicate queries
```

**Expected Impact**: 30-40% query latency reduction (with typical 30% duplicate rate)

---

### 2. Metadata-Aware ChromaDB Queries (2-3 Hours)

**File**: `vectorstore/vectorstore.py`

```python
# BEFORE: Over-fetching and manual filtering
def query(self, query_embedding, k=5, where=None):
    results = self.collection.query(
        query_embeddings=[query_embedding],
        n_results=20,  # Over-fetch by 4x
        where=None,    # No metadata filtering
    )
    
    # Manual filtering in caller
    filtered = [r for r in results if r.metadata.get("department") == dept]
    return filtered[:5]

# AFTER: Metadata-aware query
def query(self, query_embedding, k=5, where=None):
    results = self.collection.query(
        query_embeddings=[query_embedding],
        n_results=k,   # Exact amount needed
        where=where,   # Push filtering to ChromaDB
    )
    return results
```

**File**: `retriever/retrieval_pipeline.py` - Update callers

```python
# BEFORE
def search_by_department(self, query, department):
    all_results = self.vector_store.query(embedding, k=20)
    return [r for r in all_results if r.metadata['department'] == department]

# AFTER
def search_by_department(self, query, department):
    where_filter = {"department": department} if department else None
    return self.vector_store.query(embedding, k=5, where=where_filter)
```

**Verification**:
```python
# In tests/test_vectorstore.py
def test_metadata_aware_query():
    # Measure memory usage
    import tracemalloc
    tracemalloc.start()
    
    results = store.query(embedding, k=5, where={"department": "CS"})
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Memory used: {peak / 1024 / 1024:.1f}MB")
    tracemalloc.stop()
    
    # Should be ~50% less than before
```

**Expected Impact**: 40% retrieval latency reduction, 50% memory savings

---

### 3. Pre-compile Regex Patterns (1 Hour)

**File**: `ingestion/chunk_processor.py`

```python
# BEFORE: Patterns compiled every call
import re

class StructureDetector:
    @staticmethod
    def contains_list(text: str) -> bool:
        bullet_pattern = r'^\s*[-*+]\s+.+'
        ordered_pattern = r'^\s*\d+\.\s+.+'
        return bool(
            re.search(bullet_pattern, text, re.MULTILINE) or
            re.search(ordered_pattern, text, re.MULTILINE)
        )
    
    @staticmethod
    def contains_table(text: str) -> bool:
        return bool(re.search(r'\|\s*.*\s*\|', text))
    
    @staticmethod
    def contains_code(text: str) -> bool:
        return bool(re.search(r'```|<code>|    [^ ]', text))

# AFTER: Pre-compiled module-level patterns
import re

# Compiled once at module load
_BULLET_PATTERN = re.compile(r'^\s*[-*+]\s+.+', re.MULTILINE)
_ORDERED_PATTERN = re.compile(r'^\s*\d+\.\s+.+', re.MULTILINE)
_TABLE_PATTERN = re.compile(r'\|\s*.*\s*\|')
_CODE_PATTERN = re.compile(r'```|<code>|    [^ ]')
_HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

class StructureDetector:
    @staticmethod
    def contains_list(text: str) -> bool:
        return bool(_BULLET_PATTERN.search(text) or _ORDERED_PATTERN.search(text))
    
    @staticmethod
    def contains_table(text: str) -> bool:
        return bool(_TABLE_PATTERN.search(text))
    
    @staticmethod
    def contains_code(text: str) -> bool:
        return bool(_CODE_PATTERN.search(text))
    
    @staticmethod
    def detect_heading(text: str) -> Optional[Tuple[int, str]]:
        match = _HEADING_PATTERN.match(text.strip())
        if match:
            return (len(match.group(1)), match.group(2).strip())
        return None
```

**Verification**:
```python
# tests/test_chunk_processor.py
import time

def test_pattern_performance():
    text_samples = [test_chunk for _ in range(1000)]
    
    start = time.time()
    for text in text_samples:
        StructureDetector.contains_list(text)
    elapsed = time.time() - start
    
    print(f"Time for 1000 checks: {elapsed * 1000:.1f}ms")
    # Before: ~100-150ms
    # After: ~2-3ms (50x faster!)
```

**Expected Impact**: 50x faster pattern matching, 100-200ms per document saved

---

### 4. Fix String Concatenation O(n²) Issue (1-2 Hours)

Search for patterns in `prompts/`, `chatbot/`, and response formatting:

```python
# BEFORE: O(n²) concatenation
def format_response(context_chunks):
    response = ""
    for chunk in context_chunks:
        response += f"- {chunk.title}\n"
        response += f"  {chunk.text}\n\n"
    return response

# AFTER: O(n) concatenation
def format_response(context_chunks):
    lines = []
    for chunk in context_chunks:
        lines.append(f"- {chunk.title}")
        lines.append(f"  {chunk.text}")
        lines.append("")
    return "\n".join(lines)
```

**Find all occurrences**:
```bash
grep -r "result\s*+=" --include="*.py" .
grep -r "text\s*+=" --include="*.py" .
grep -r "response\s*+=" --include="*.py" .
```

**Verification**:
```python
def test_string_concat_performance():
    import time
    
    chunks = [f"chunk_{i}" * 100 for i in range(1000)]
    
    # Old way
    start = time.time()
    result = ""
    for c in chunks:
        result += c + "\n"
    old_time = time.time() - start
    
    # New way
    start = time.time()
    result = "\n".join(chunks)
    new_time = time.time() - start
    
    print(f"Old: {old_time*1000:.1f}ms, New: {new_time*1000:.1f}ms")
    print(f"Speedup: {old_time/new_time:.0f}x")
    # Should show 100-500x improvement
```

**Expected Impact**: 100x faster for large responses, 50-100ms latency gain

---

## Medium Effort (4-8 Hours) - 20-30% Additional Improvement

### 5. Batch RAGAS Evaluation (4 Hours)

**File**: `evaluation/ragas_metrics.py`

```python
# BEFORE: Individual metric computation (400 LLM calls for 100 tests)
class RAGASMetrics:
    def compute_all_metrics(self, test_cases):
        results = []
        for test_case in test_cases:  # 100 iterations
            # Each call: 1 LLM call
            faithfulness = self.compute_faithfulness(test_case.answer, test_case.context)
            precision = self.compute_precision(test_case.answer, test_case.context)
            recall = self.compute_recall(test_case.answer, test_case.context)
            relevancy = self.compute_relevancy(test_case.answer, test_case.context)
            
            results.append({
                'faithfulness': faithfulness,
                'precision': precision,
                'recall': recall,
                'relevancy': relevancy,
            })
        
        return results  # Total: 400 LLM calls

# AFTER: Batch metric computation (10 LLM calls for 100 tests)
from core.optimization import BatchProcessor, BatchConfig

class RAGASMetrics:
    def __init__(self):
        config = BatchConfig(batch_size=10)
        self.batch_processor = BatchProcessor(config)
    
    def compute_all_metrics_batch(self, test_cases):
        # Process in batches of 10
        batches = [test_cases[i:i+10] for i in range(0, len(test_cases), 10)]
        
        all_results = []
        for batch in batches:
            batch_results = self._compute_batch_metrics(batch)
            all_results.extend(batch_results)
        
        return all_results
    
    def _compute_batch_metrics(self, batch):
        # Single prompt for whole batch
        prompt = self._format_batch_prompt(batch)
        
        # One LLM call per metric type (4 total for 10 tests!)
        response = self.llm_client.complete(prompt)
        
        # Parse batch response
        return self._parse_batch_response(response, batch)
    
    def _format_batch_prompt(self, test_cases):
        return f"""
        Evaluate the following {len(test_cases)} Q&A pairs:
        
        {json.dumps([asdict(tc) for tc in test_cases], indent=2)}
        
        For each pair, compute:
        1. Faithfulness (0.0-1.0)
        2. Precision (0.0-1.0)
        3. Recall (0.0-1.0)
        4. Relevancy (0.0-1.0)
        
        Return as JSON array.
        """
```

**Verification**:
```python
def test_batch_evaluation_performance():
    test_cases = [generate_test_case() for _ in range(100)]
    
    import time
    start = time.time()
    results = ragas.compute_all_metrics_batch(test_cases)
    elapsed = time.time() - start
    
    print(f"Evaluation time: {elapsed:.1f}s")
    # Before: ~4-6 minutes (240-360s)
    # After: ~20-30 seconds (97% improvement!)
```

**Expected Impact**: 97% evaluation time reduction (4 hours → 20 seconds)

---

### 6. Eliminate Redundant Vector Searches (4-6 Hours)

**File**: `retriever/retrieval_pipeline.py`

```python
# BEFORE: 3 separate searches
class RetrievalPipeline:
    def retrieve_advanced(self, query, filters=None):
        # Search 1: Semantic search
        semantic_results = self.vector_store.query(embedding, k=20)
        
        # Search 2: Metadata filtering (redundant!)
        filtered_results = self.vector_store.query(
            embedding, 
            k=20,
            where=filters
        )
        
        # Search 3: Diversity reranking (another query!)
        diverse_results = self.vector_store.query(
            embedding,
            k=20,
        )
        # Then rerank for diversity
        
        return self._merge_results([semantic_results, filtered_results, diverse_results])

# AFTER: Single consolidated query
class RetrievalPipeline:
    def retrieve_advanced(self, query, filters=None):
        # Single query with all filters
        embedding = self.encoder.encode(query)
        
        results = self.vector_store.query(
            embedding,
            k=5,
            where=filters,
        )
        
        # Rerank without additional search
        diverse_results = self._rerank_for_diversity(results)
        
        return diverse_results
    
    def _rerank_for_diversity(self, results):
        # Use cached metadata, don't query again
        reranked = []
        seen_urls = set()
        
        for result in results:
            url = result.metadata.get('source_url')
            if url not in seen_urls:
                reranked.append(result)
                seen_urls.add(url)
        
        return reranked
```

**Verification**:
```python
def test_single_query_performance():
    query = "What is the admission process?"
    
    import time
    start = time.time()
    results = pipeline.retrieve_advanced(query)
    elapsed = time.time() - start
    
    print(f"Retrieval time: {elapsed*1000:.1f}ms")
    # Before: ~900ms (3 searches × 300ms each)
    # After: ~300ms (1 search)
```

**Expected Impact**: 600-700ms reduction per query (2/3 latency saved)

---

### 7. Async I/O with aiofiles (3-4 Hours)

**File**: `embedding/embedding_generator.py` and file operations

```python
# BEFORE: Blocking file operations
def save_embeddings_batch(self, embeddings, file_path):
    with open(file_path, 'w') as f:
        json.dump(embeddings, f)

# AFTER: Async file operations
import aiofiles

async def save_embeddings_batch_async(self, embeddings, file_path):
    async with aiofiles.open(file_path, 'w') as f:
        await f.write(json.dumps(embeddings))

# Usage in async context
async def process_documents(docs):
    tasks = [embed_document_async(doc) for doc in docs]
    embeddings = await asyncio.gather(*tasks)
    
    # Non-blocking save
    await save_embeddings_batch_async(embeddings, "embeddings.json")
```

**Also fix rate limiting**:

```python
# BEFORE: Blocking sleep
for chunk in chunks:
    result = await embed(chunk)
    time.sleep(0.1)  # BLOCKS! ❌

# AFTER: Async sleep
for chunk in chunks:
    result = await embed(chunk)
    await asyncio.sleep(0.01)  # Non-blocking ✓
```

**Verification**:
```python
@pytest.mark.asyncio
async def test_async_io_performance():
    embeddings = [generate_embedding() for _ in range(1000)]
    
    import time
    start = time.time()
    await save_embeddings_batch_async(embeddings, "test.json")
    elapsed = time.time() - start
    
    print(f"Save time: {elapsed*1000:.1f}ms")
    # Both should be similar (I/O is I/O)
    # But now thread pool isn't blocked
```

**Expected Impact**: No individual latency change, but 3-5x higher concurrency

---

## Advanced Optimizations (8+ Hours)

### 8. Pre-compile Module-Level Patterns

Already covered in section 3 above.

### 9. Deduplication-Aware Embedding Cache

```python
# embedding/embedding_generator.py

class SmartEmbeddingCache:
    def __init__(self):
        self._cache = {}  # hash → embedding
        self._duplicate_detector = DuplicateDetector()
    
    def generate_batch_with_dedup(self, chunks):
        """Generate embeddings, reusing for duplicates."""
        unique_chunks = {}
        embeddings = []
        
        for chunk in chunks:
            chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()
            
            if chunk_hash in self._cache:
                # Reuse cached embedding
                embeddings.append(self._cache[chunk_hash])
            else:
                # Mark as new
                unique_chunks[chunk_hash] = chunk
        
        # Only embed new chunks
        if unique_chunks:
            new_embeddings = self.client.create(
                model="text-embedding-3-small",
                input=list(unique_chunks.values()),
            )
            
            for hash_val, emb_data in zip(unique_chunks.keys(), new_embeddings.data):
                self._cache[hash_val] = emb_data['embedding']
        
        return embeddings
```

**Expected Impact**: 10-20% cost savings for duplicate-heavy content

---

## Testing & Verification Checklist

```python
# tests/test_performance_optimizations.py

import pytest
import time
from core.optimization import cached

class TestPerformanceOptimizations:
    
    def test_query_caching_hit_rate(self):
        """Verify caching reduces repeated queries."""
        pipeline = RetrievalPipeline()
        
        # First query (cache miss)
        start = time.time()
        result1 = pipeline.retrieve("How to apply?")
        miss_time = time.time() - start
        
        # Second query (cache hit)
        start = time.time()
        result2 = pipeline.retrieve("How to apply?")
        hit_time = time.time() - start
        
        assert result1 == result2
        assert hit_time < miss_time / 10  # At least 10x faster
        
        print(f"Cache miss: {miss_time*1000:.1f}ms")
        print(f"Cache hit: {hit_time*1000:.1f}ms")
        print(f"Speedup: {miss_time/hit_time:.0f}x")
    
    def test_metadata_filtering_memory(self):
        """Verify metadata filtering reduces memory."""
        import tracemalloc
        
        # With metadata filtering
        tracemalloc.start()
        store.query(embedding, k=5, where={"dept": "CS"})
        _, peak_with_filter = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Without metadata filtering
        tracemalloc.start()
        results = store.query(embedding, k=20)
        filtered = [r for r in results if r.metadata['dept'] == 'CS']
        _, peak_without_filter = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        assert peak_with_filter < peak_without_filter
        improvement = (peak_without_filter - peak_with_filter) / peak_without_filter
        print(f"Memory improvement: {improvement*100:.1f}%")
    
    def test_batch_ragas_evaluation(self):
        """Verify batching reduces LLM calls."""
        from unittest.mock import patch
        
        ragas = RAGASMetrics()
        test_cases = [generate_test_case() for _ in range(100)]
        
        with patch.object(ragas.llm_client, 'complete') as mock_llm:
            mock_llm.return_value = '{"results": []}'
            
            start = time.time()
            ragas.compute_all_metrics_batch(test_cases)
            elapsed = time.time() - start
            
            # 10 calls instead of 400
            assert mock_llm.call_count <= 40  # 4 metric types × 10 batches
            assert elapsed < 30  # Should be quick
            
            print(f"LLM calls: {mock_llm.call_count}")
            print(f"Time: {elapsed:.1f}s")
    
    def test_string_concatenation_performance(self):
        """Verify O(n²) fix."""
        from prompts.system_prompts import format_response
        
        chunks = [f"Chunk {i}" * 100 for i in range(100)]
        
        start = time.time()
        result = format_response(chunks)
        elapsed = time.time() - start
        
        assert len(result) > 0
        print(f"Format time: {elapsed*1000:.2f}ms (should be < 10ms)")
        assert elapsed < 0.01  # Should be fast

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

---

## Performance Benchmarking Script

```bash
# benchmark_performance.sh
#!/bin/bash

echo "=== Performance Benchmark ==="

echo "1. Query Latency"
python -c "
from retriever.retrieval_pipeline import RetrievalPipeline
import time
pipeline = RetrievalPipeline()

times = []
for i in range(100):
    start = time.time()
    pipeline.retrieve('How to apply?')
    times.append(time.time() - start)

import statistics
print(f'P50: {statistics.median(times)*1000:.1f}ms')
print(f'P95: {sorted(times)[95]*1000:.1f}ms')
print(f'P99: {sorted(times)[99]*1000:.1f}ms')
"

echo "2. Embedding Throughput"
python -c "
from embedding.embedding_generator import EmbeddingGenerator
import time

gen = EmbeddingGenerator()
texts = [f'Sample text {i}' * 10 for i in range(100)]

start = time.time()
embeddings = gen.generate_batch(texts)
elapsed = time.time() - start

print(f'Throughput: {len(texts) / elapsed:.1f} texts/sec')
print(f'Time per text: {elapsed / len(texts) * 1000:.1f}ms')
"

echo "3. Memory Usage"
python -c "
import tracemalloc
from chatbot.chatbot import Chatbot

chatbot = Chatbot()
tracemalloc.start()

for i in range(10):
    chatbot.answer('How to apply?')

current, peak = tracemalloc.get_traced_memory()
print(f'Current: {current / 1024 / 1024:.1f}MB')
print(f'Peak: {peak / 1024 / 1024:.1f}MB')
tracemalloc.stop()
"
```

---

## Success Criteria

- [ ] Query latency reduced by 40% (1200ms → 700ms)
- [ ] Cache hit rate > 30% (measured in logs)
- [ ] Memory usage < 150MB per query (was 250MB)
- [ ] Evaluation time < 30 seconds for 100 test cases
- [ ] Embedding throughput > 1 doc/sec
- [ ] No functional regressions in tests
- [ ] All integration tests pass

