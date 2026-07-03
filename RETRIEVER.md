# Advanced Retriever System Guide

Complete guide to the advanced retriever with semantic search, filtering, and hybrid retrieval capabilities.

## Overview

The retriever system provides comprehensive search capabilities:
- **Semantic Search**: Cosine similarity-based retrieval
- **Metadata Filtering**: Section, department, URL, and chunk length filtering
- **Top-K Retrieval**: Configurable number of results
- **Hybrid Search**: Combined semantic + filter search
- **Duplicate Removal**: URL, chunk ID, and content-based deduplication
- **Score Thresholding**: Minimum similarity score filtering
- **Result Reranking**: Diversity-aware result reordering
- **Batch Operations**: Efficient multi-query processing

## Architecture

### Components

```
retrieval_pipeline.py (Orchestration)
  ├─ retriever_advanced.py (AdvancedRetriever)
  │  ├─ semantic_search()
  │  ├─ hybrid_search()
  │  ├─ filter_by_*()
  │  ├─ remove_duplicates()
  │  └─ rerank_*()
  │
  ├─ query_encoder.py (QueryEncoder)
  │  ├─ encode() - text → 1536-dim vector
  │  ├─ preprocess_query()
  │  └─ encode_batch()
  │
  └─ vectorstore/ (Persistent storage)
     └─ Semantic search via ChromaDB
```

### Data Flow

```
User Query (text)
  ↓
QueryEncoder.encode() → 1536-dim vector
  ↓
RetrievalPipeline.retrieve()
  ├─ AdvancedRetriever.hybrid_search()
  │  ├─ semantic_search()
  │  ├─ filter_by_section/department()
  │  ├─ remove_duplicates()
  │  └─ rerank_by_diversity()
  ↓
SearchResult[] (ranked by similarity)
  ├─ chunk_id
  ├─ text (content)
  ├─ metadata (15+ fields)
  ├─ similarity_score
  └─ retrieval_method
```

## Installation

### Prerequisites

```bash
# Already included in requirements.txt
pip install chromadb openai numpy
```

## Usage

### Basic Retrieval

```python
from pathlib import Path
from vectorstore.vectorstore import VectorStore
from retriever.retrieval_pipeline import RetrievalPipeline

# Initialize
vectorstore = VectorStore(
    collection_name="college_faq",
    persist_dir=Path("knowledge_base/vectorstore"),
)

pipeline = RetrievalPipeline(vectorstore)

# Retrieve
result = pipeline.retrieve(
    query="What are the admission requirements?",
    k=5,
)

# Results
for result_obj in result.results:
    print(f"{result_obj.rank}. {result_obj.text}")
    print(f"   Score: {result_obj.similarity_score:.1%}")
    print(f"   Department: {result_obj.metadata.get('department')}")
```

### Semantic Search

```python
# Pure semantic search without filtering
result = pipeline.retrieve_semantic(
    query="placement statistics",
    k=5,
    min_score=0.4,
)
```

### Filtered Retrieval

```python
# By section
result = pipeline.retrieve_by_section(
    query="admission process",
    section="admissions",
    k=5,
)

# By department
result = pipeline.retrieve_by_department(
    query="cs curriculum",
    department="computer_science",
    k=5,
)
```

### Advanced Hybrid Search

```python
from retriever.retriever_advanced import AdvancedRetriever, RetrieverConfig

# Create retriever with custom config
config = RetrieverConfig(
    similarity_threshold=0.3,
    top_k=5,
    diversity_penalty=0.2,
    enable_duplicate_removal=True,
)

retriever = AdvancedRetriever(vectorstore, config=config)

# Hybrid search
results = retriever.hybrid_search(
    query_embedding=query_vec,  # 1536 dims
    k=5,
    section="admissions",
    department="admissions",
    min_score=0.4,
    remove_duplicates=True,
)

# Post-process results
results = retriever.rerank_by_diversity(results, diversity_penalty=0.25)
```

### Batch Processing

```python
# Batch retrieval
results = pipeline.batch_retrieve(
    queries=[
        "admission requirements",
        "placement statistics",
        "course offerings",
    ],
    k=5,
    section="admissions",
)

# Process each result
for result in results:
    if result:
        print(f"Query: {result.query}")
        print(f"Results: {len(result.results)}")
```

### Result Evaluation

```python
from retriever.retrieval_pipeline import RetrievalEvaluator

# Evaluate single result
metrics = RetrievalEvaluator.evaluate_result(
    result,
    ground_truth_chunks=["chunk_1", "chunk_2"],  # Optional
)

print(f"Recall: {metrics.get('recall')}")
print(f"Precision: {metrics.get('precision')}")

# Batch evaluation
batch_metrics = RetrievalEvaluator.batch_evaluate(
    results,
    ground_truth=[["chunk_1", "chunk_2"], ["chunk_3"]],  # Optional
)
```

## Components

### AdvancedRetriever

Core retrieval engine with multiple search strategies.

```python
retriever = AdvancedRetriever(
    vectorstore=vectorstore,
    config=RetrieverConfig(
        similarity_threshold=0.3,
        top_k=5,
        enable_duplicate_removal=True,
    )
)

# Semantic search
results = retriever.semantic_search(
    query_embedding=[...],  # 1536 dims
    k=5,
    min_score=0.3,
)

# Filtering
section_results = retriever.filter_by_section(results, "admissions")
dept_results = retriever.filter_by_department(results, "cs")
url_results = retriever.filter_by_url(results, "https://college.edu/about")
length_results = retriever.filter_by_chunk_length(results, min_length=50, max_length=1000)

# Deduplication
unique_results = retriever.remove_duplicates(results, by="url")

# Thresholding
high_score_results = retriever.apply_score_threshold(results, threshold=0.5)

# Reranking
diverse_results = retriever.rerank_by_diversity(results, diversity_penalty=0.2)
section_diverse = retriever.rerank_by_section_diversity(results, penalty=0.15)

# Top-K
top_5 = retriever.top_k_search(query_embedding, k=5)

# Hybrid
hybrid_results = retriever.hybrid_search(
    query_embedding=query_vec,
    k=5,
    section="admissions",
    department="admissions",
    remove_duplicates=True,
)

# Batch
batch_results = retriever.batch_search([query1, query2], k=5)

# Statistics
stats = retriever.get_result_stats(results)
```

### QueryEncoder

Converts text queries to embeddings.

```python
encoder = QueryEncoder(
    model="text-embedding-3-small",
    max_retries=3,
)

# Single query
embedding = encoder.encode("What is the admission process?")

# Batch encoding
embeddings = encoder.encode_batch([
    "What is the admission process?",
    "What are the placement statistics?",
])

# Preprocess
query = encoder.preprocess_query(
    "  HELLO   WORLD  ",
    lowercase=True,
    remove_extra_spaces=True,
)
# Returns: "hello world"
```

### RetrievalPipeline

End-to-end orchestration from query text to results.

```python
pipeline = RetrievalPipeline(
    vectorstore=vectorstore,
    retriever_config=RetrieverConfig(...),
    cache_embeddings=True,  # Cache query embeddings
)

# Retrieve with text query
result = pipeline.retrieve(
    query="admission requirements",
    k=5,
    section="admissions",
    department="admissions",
    min_score=0.3,
    use_cache=True,  # Use cached embeddings
)

# Semantic only
result = pipeline.retrieve_semantic(query, k=5)

# By section
result = pipeline.retrieve_by_section(query, "admissions", k=5)

# By department
result = pipeline.retrieve_by_department(query, "cs", k=5)

# Batch
results = pipeline.batch_retrieve(queries, k=5)

# Cache management
pipeline.clear_cache()
stats = pipeline.get_cache_stats()
```

### SearchResult

Single search result with all information.

```python
result = SearchResult(
    chunk_id="chunk_123",
    text="Content text...",
    metadata={
        "source_url": "https://college.edu/about",
        "section": "about",
        "department": "general",
        "chunk_title": "About College",
    },
    similarity_score=0.92,
    rank=1,
    retrieval_method="hybrid",
)

# Convert to dict
d = result.to_dict()

# String representation
print(result)  # SearchResult(rank=1, score=0.920, chunk_id=chunk_123)
```

### RetrievalResult

Complete retrieval result with query and results.

```python
retrieval_result = RetrievalResult(
    query="admission requirements",
    results=[result1, result2],
    retrieval_time_ms=45.3,
    method="hybrid",
)

# Convert to dict
d = retrieval_result.to_dict()

# Convert to JSON
json_str = retrieval_result.to_json()
```

### RetrieverConfig

Configuration for retriever behavior.

```python
config = RetrieverConfig(
    similarity_threshold=0.3,      # Min score (0.0-1.0)
    top_k=5,                        # Default K
    enable_duplicate_removal=True,
    enable_diversity_reranking=True,
    diversity_penalty=0.2,          # Weight for diversity
    min_chunk_length=10,            # Min text length
    max_chunk_length=10000,         # Max text length
)
```

## Search Strategies

### 1. Semantic Search

Pure similarity-based retrieval.

```python
results = retriever.semantic_search(
    query_embedding=query_vec,
    k=5,
    min_score=0.3,
)
```

**Use when**: You need direct similarity matching without constraints.

### 2. Top-K Search

Semantic search returning exactly K results.

```python
results = retriever.top_k_search(
    query_embedding=query_vec,
    k=5,
)
```

**Use when**: You need a fixed number of results.

### 3. Hybrid Search

Semantic search + filtering.

```python
results = retriever.hybrid_search(
    query_embedding=query_vec,
    k=5,
    section="admissions",      # Optional
    department="admissions",   # Optional
    min_score=0.3,
    remove_duplicates=True,
)
```

**Use when**: You want to constrain search by metadata.

## Filtering Options

### By Section

```python
# Direct filter
filtered = retriever.filter_by_section(results, "admissions")

# Hybrid search with section
results = retriever.hybrid_search(..., section="admissions")
```

**Sections**: about, admissions, academics, placements, facilities, etc.

### By Department

```python
# Direct filter
filtered = retriever.filter_by_department(results, "cs")

# Hybrid search with department
results = retriever.hybrid_search(..., department="cs")
```

**Departments**: cs, ec, mechanical, etc.

### By URL

```python
filtered = retriever.filter_by_url(results, "https://college.edu/admissions")
```

### By Chunk Length

```python
filtered = retriever.filter_by_chunk_length(
    results,
    min_length=50,
    max_length=500,
)
```

## Duplicate Removal

Remove redundant results from different sources.

```python
# By URL (same source page)
unique = retriever.remove_duplicates(results, by="url")

# By chunk ID (exact duplicate)
unique = retriever.remove_duplicates(results, by="chunk_id")

# By content (similar text)
unique = retriever.remove_duplicates(results, by="content")
```

## Score Thresholding

Filter by minimum similarity score.

```python
# Keep only high-confidence results
high_confidence = retriever.apply_score_threshold(results, threshold=0.7)

# Or during retrieval
results = retriever.semantic_search(
    query_embedding=query_vec,
    k=10,
    min_score=0.5,  # Minimum score threshold
)
```

## Result Reranking

Reorder results for diversity or other criteria.

```python
# Diversity by URL (different sources)
diverse = retriever.rerank_by_diversity(results, diversity_penalty=0.2)

# Diversity by section (different sections)
section_diverse = retriever.rerank_by_section_diversity(results, penalty=0.15)
```

## Performance

### Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Encode query | ~100-200ms | API call to OpenAI |
| Semantic search (k=5) | ~50ms | ChromaDB query |
| Hybrid search (k=5) | ~100-150ms | Search + filtering |
| Filter results (1000) | ~10ms | In-memory filtering |
| Remove duplicates (1000) | ~5ms | Hash-based dedup |
| Rerank (1000 results) | ~20ms | Score adjustment |
| Batch search (10 queries) | ~500ms | Sequential processing |

### Optimization Tips

1. **Cache query embeddings** - Reuse for repeated queries
2. **Batch processing** - Process multiple queries together
3. **Metadata filtering** - Reduce search space early
4. **Top-K limiting** - Fetch more, filter later
5. **Duplicate removal** - Early in pipeline for efficiency

## Evaluation

### Metrics

```python
metrics = RetrievalEvaluator.evaluate_result(
    retrieval_result,
    ground_truth_chunks=["chunk_1", "chunk_2"],
)

# Returned metrics:
# - total_results: Number of results
# - retrieval_time_ms: Time taken
# - avg_similarity: Average score
# - recall: TP / (TP + FN)
# - precision: TP / (TP + FP)
# - f1: Harmonic mean of precision/recall
```

### Batch Evaluation

```python
batch_metrics = RetrievalEvaluator.batch_evaluate(
    results=[result1, result2, ...],
    ground_truth=[
        ["chunk_1", "chunk_2"],
        ["chunk_3"],
    ],
)

# Returns:
# - total_queries
# - avg_retrieval_time_ms
# - total_results
# - individual evaluations
```

## API Reference

### AdvancedRetriever

Methods:
- `semantic_search(query_embedding, k, min_score)` → List[SearchResult]
- `filter_by_section(results, section)` → List[SearchResult]
- `filter_by_department(results, department)` → List[SearchResult]
- `filter_by_url(results, url)` → List[SearchResult]
- `filter_by_chunk_length(results, min_len, max_len)` → List[SearchResult]
- `remove_duplicates(results, by)` → List[SearchResult]
- `apply_score_threshold(results, threshold)` → List[SearchResult]
- `top_k_search(query_embedding, k, min_score)` → List[SearchResult]
- `hybrid_search(query_embedding, k, section, department, min_score, remove_duplicates)` → List[SearchResult]
- `rerank_by_diversity(results, diversity_penalty)` → List[SearchResult]
- `rerank_by_section_diversity(results, penalty)` → List[SearchResult]
- `batch_search(query_embeddings, k, min_score)` → List[List[SearchResult]]
- `get_result_stats(results)` → Dict[str, Any]

### QueryEncoder

Methods:
- `encode(query)` → Optional[List[float]]
- `encode_batch(queries)` → List[Optional[List[float]]]
- `preprocess_query(query, lowercase, remove_extra_spaces)` → str

### RetrievalPipeline

Methods:
- `retrieve(query, k, section, department, min_score, use_cache)` → Optional[RetrievalResult]
- `retrieve_semantic(query, k, min_score)` → Optional[RetrievalResult]
- `retrieve_by_section(query, section, k)` → Optional[RetrievalResult]
- `retrieve_by_department(query, department, k)` → Optional[RetrievalResult]
- `batch_retrieve(queries, k, section)` → List[Optional[RetrievalResult]]
- `clear_cache()` → None
- `get_cache_stats()` → Dict[str, Any]

## Error Handling

```python
try:
    result = pipeline.retrieve("query text")
    
    if result is None:
        logger.error("Retrieval failed")
    else:
        for search_result in result.results:
            print(search_result.text)

except Exception as e:
    logger.error(f"Retrieval error: {e}")
```

## Testing

```bash
# Run retriever tests
pytest tests/test_retriever.py -v

# Specific test
pytest tests/test_retriever.py::TestAdvancedRetriever::test_hybrid_search -v

# With coverage
pytest tests/test_retriever.py --cov=retriever
```

## Configuration Examples

### Conservative Retrieval (High Precision)

```python
config = RetrieverConfig(
    similarity_threshold=0.6,
    top_k=3,
    enable_duplicate_removal=True,
    diversity_penalty=0.3,
)
```

### Aggressive Retrieval (High Recall)

```python
config = RetrieverConfig(
    similarity_threshold=0.2,
    top_k=10,
    enable_duplicate_removal=False,
    diversity_penalty=0.05,
)
```

### Balanced

```python
config = RetrieverConfig(
    similarity_threshold=0.3,
    top_k=5,
    enable_duplicate_removal=True,
    diversity_penalty=0.2,
)
```

## Next Steps

After retrieval:
1. Use RetrievalResult to access chunks
2. Generate LLM context from results
3. Pass to LLM for answer generation
4. Include citations from SearchResult.metadata

See CHATBOT.md for RAG integration.
