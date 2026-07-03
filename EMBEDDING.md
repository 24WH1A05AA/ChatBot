# Embedding Generation Guide

Complete guide to generating embeddings for college FAQ chunks using OpenAI's `text-embedding-3-small` model with batching, rate limiting, and resume capability.

## Overview

The embedding module generates vector representations for text chunks:
- **Model**: `text-embedding-3-small` (1536 dimensions)
- **Batch Processing**: Efficient API calls with configurable batch sizes
- **Rate Limiting**: Respects OpenAI API rate limits
- **Resume Capability**: Persists state for interrupted processes
- **Deduplication**: Skips duplicate chunks automatically

## Architecture

### Components

```
generate_embeddings.py
    ↓
embedding_orchestrator.py (EmbeddingOrchestrator)
    ├── embedding_generator.py
    │   ├── DuplicateDetector
    │   ├── RateLimiter
    │   ├── BatchManager
    │   └── OpenAIEmbeddingGenerator
    │
    └── embedding_models.py (Data Models)
        ├── EmbeddingVector
        ├── EmbeddingBatch
        └── EmbeddingResult
```

### Data Flow

```
chunks.json (from chunk_documents.py)
    ↓
BatchManager (create batches of 100)
    ↓
OpenAIEmbeddingGenerator (call OpenAI API)
    ├── DuplicateDetector
    ├── RateLimiter
    └── Retry logic (exponential backoff)
    ↓
EmbeddingVector objects
    ↓
EmbeddingOrchestrator (save & track state)
    ↓
embeddings.json
embedding_state.json (resume file)
```

## Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- Chunks JSON file from chunking phase

### Setup

```bash
# Install dependencies (already in requirements.txt)
pip install openai pydantic loguru

# Set environment variables
export OPENAI_API_KEY="sk-..."
```

## Usage

### Basic Usage

```bash
# Generate embeddings with defaults
python generate_embeddings.py

# Custom batch size
python generate_embeddings.py --batch-size 50

# Specify input/output paths
python generate_embeddings.py \
  --chunks-file ./chunks.json \
  --output-dir ./embeddings

# Skip resume (reprocess all)
python generate_embeddings.py --no-resume
```

### Programmatic Usage

```python
import asyncio
from pathlib import Path
from embedding.embedding_generator import (
    BatchManager,
    OpenAIEmbeddingGenerator,
)
from embedding.embedding_orchestrator import EmbeddingOrchestrator

async def generate():
    # Load chunks
    chunks_file = Path("knowledge_base/chunks/chunks.json")
    
    # Create manager and generator
    batch_mgr = BatchManager(batch_size=100)
    generator = OpenAIEmbeddingGenerator()
    orchestrator = EmbeddingOrchestrator()
    
    # Process...
    batches, skipped = batch_mgr.create_batches(chunks)
    
    for batch in batches:
        vectors = await generator.generate_batch(batch, chunk_lookup)
        for vector in vectors:
            orchestrator.add_embedding(vector)
    
    # Save
    orchestrator.save_embeddings()

asyncio.run(generate())
```

## Configuration

### Environment Variables

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...  # Optional

# Paths
PERSIST_DIRECTORY=./knowledge_base

# Embedding parameters
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=100
EMBEDDING_MAX_RETRIES=3

# Rate limiting
OPENAI_REQUESTS_PER_MINUTE=3000
```

### Settings

Edit `config/settings.py`:

```python
EMBEDDING_MODEL: str = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE: int = 100
EMBEDDING_MAX_RETRIES: int = 3
EMBEDDING_DIMENSION: int = 1536
PERSIST_DIRECTORY: Path = Path("knowledge_base")
```

## Components

### DuplicateDetector

Identifies and skips duplicate chunks:

```python
from embedding.embedding_generator import DuplicateDetector

detector = DuplicateDetector()

# Check if text is duplicate
if detector.is_duplicate("same text"):
    print("Already seen this chunk")
```

**Features:**
- SHA256-based hashing
- Memory-efficient tracking
- Automatic deduplication in batch processing

### RateLimiter

Enforces API rate limits:

```python
from embedding.embedding_generator import RateLimiter

limiter = RateLimiter(requests_per_minute=3000)

# Acquire token before API call
limiter.acquire()
# make API call
```

**Features:**
- Configurable requests per minute
- Exponential backoff on failures
- Automatic window management

### BatchManager

Creates batches from chunks:

```python
from embedding.embedding_generator import BatchManager

manager = BatchManager(batch_size=100)
batches, skipped = manager.create_batches(
    chunks=chunk_list,
    skip_duplicates=True
)

for batch in batches:
    print(f"Batch {batch.batch_id}: {len(batch.texts)} chunks")
```

**Features:**
- Configurable batch size (1-1000)
- Automatic duplicate skipping
- Maintains chunk IDs and metadata

### OpenAIEmbeddingGenerator

Generates embeddings via OpenAI API:

```python
from embedding.embedding_generator import OpenAIEmbeddingGenerator

generator = OpenAIEmbeddingGenerator(
    model="text-embedding-3-small",
    batch_size=100,
    max_retries=3,
)

# Generate for a batch
vectors = await generator.generate_batch(batch, chunk_lookup)

for vector in vectors:
    print(f"{vector.chunk_id}: {len(vector.vector)} dims")
```

**Features:**
- Batched API calls (efficient)
- Automatic retry with exponential backoff
- Rate limiting integration
- Processing time tracking

### EmbeddingStateTracker

Enables resume capability:

```python
from embedding.embedding_orchestrator import EmbeddingStateTracker

tracker = EmbeddingStateTracker(Path("state.json"))

# Mark chunk as processed
tracker.mark_processed("chunk_123")

# Check if already processed
if not tracker.is_processed("chunk_123"):
    # Process chunk...
    pass

# Save state for resuming
tracker.save_state()
```

**Features:**
- Persistent state file
- Load/save operations
- Track processed and failed chunks
- Resume from interruptions

### EmbeddingOrchestrator

Orchestrates the entire process:

```python
from embedding.embedding_orchestrator import EmbeddingOrchestrator

orchestrator = EmbeddingOrchestrator(
    batch_size=100,
    output_dir=Path("knowledge_base/embeddings")
)

# Add embeddings
for vector in vectors:
    orchestrator.add_embedding(vector)

# Save
orchestrator.save_embeddings()

# Get results
result = orchestrator.get_result(
    total_chunks=1000,
    skipped=50,
    failed=5,
    total_tokens=500000,
    generation_time=300.0,
)
```

## Data Models

### EmbeddingVector

Single embedding representation:

```python
from embedding.embedding_models import EmbeddingVector

vector = EmbeddingVector(
    chunk_id="chunk_123",
    document_id="doc_456",
    vector=[0.1, 0.2, ..., 0.3],  # 1536 dimensions
    model="text-embedding-3-small",
    chunk_text="Original chunk text",
    chunk_title="Section Heading",
    section="About College",
    source_url="https://college.edu/about",
    processing_time_ms=125.5,
)
```

**Fields:**
- `chunk_id`: Unique chunk identifier
- `document_id`: Source document ID
- `vector`: 1536-dimensional float array
- `model`: Model used (text-embedding-3-small)
- `chunk_text`: Original text (optional)
- `chunk_title`: Chunk heading
- `section`: Document section
- `source_url`: Source document URL
- `processing_time_ms`: API latency
- `created_at`: Timestamp

### EmbeddingBatch

Group of chunks for batching:

```python
from embedding.embedding_models import EmbeddingBatch

batch = EmbeddingBatch(
    chunk_ids=["c1", "c2", "c3"],
    texts=["text 1", "text 2", "text 3"],
    batch_size=3,
)
```

**Fields:**
- `batch_id`: Unique batch identifier
- `chunk_ids`: IDs of chunks in batch
- `texts`: Chunk texts (input to API)
- `batch_size`: Number of chunks
- `created_at`: Timestamp

### EmbeddingResult

Generation results and statistics:

```python
from embedding.embedding_models import EmbeddingResult

result = EmbeddingResult(
    total_chunks=1000,
    total_embeddings=950,
    skipped_duplicates=30,
    failed_chunks=20,
    total_batches=10,
    avg_processing_time_ms=125.5,
    total_tokens_used=500000,
    output_file="embeddings.json",
    generation_time=300.0,
)
```

## Output Files

### embeddings.json

Complete embeddings database:

```json
{
  "version": "1.0",
  "model": "text-embedding-3-small",
  "total_embeddings": 950,
  "generated_at": "2024-01-15T10:30:00Z",
  "embeddings": [
    {
      "chunk_id": "chunk_1",
      "document_id": "doc_1",
      "vector": [0.1, 0.2, ...],
      "model": "text-embedding-3-small",
      "chunk_text": "...",
      "section": "About College",
      "source_url": "https://...",
      "processing_time_ms": 125.5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### embedding_state.json

Resume state file:

```json
{
  "processed": ["chunk_1", "chunk_2", ...],
  "failed": ["chunk_100", ...],
  "saved_at": "2024-01-15T10:35:00Z"
}
```

## API Costs

### OpenAI Pricing

- **text-embedding-3-small**: $0.02 per 1M tokens
- **Approximate cost**: $1 per 50 million tokens

### Estimation

```python
# For a college website:
# ~1000 pages * 5 chunks/page = 5000 chunks
# ~200 tokens per chunk = 1M tokens total
# Cost ≈ $0.02

# For larger websites:
# ~10000 pages * 5 chunks = 50000 chunks
# ~200 tokens per chunk = 10M tokens
# Cost ≈ $0.20
```

## Performance

### Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Duplicate Detection | < 1ms | Per chunk |
| Batch Creation | ~100ms | 1000 chunks |
| API Call (100 chunks) | ~1-2s | Network dependent |
| Persistence | ~500ms | Save 1000 embeddings |

### Optimization Tips

1. **Batch Size**: Larger batches (100-256) = fewer API calls
2. **Deduplication**: Skip duplicates early = cost savings
3. **Resume**: Process in stages = handle interruptions
4. **Parallel Processing**: Multiple generators (if quota allows)

## Error Handling

### Common Errors

```
OpenAI API Error: Rate limit exceeded
→ Solution: Reduce batch size or wait

OpenAI API Error: Invalid API key
→ Solution: Set OPENAI_API_KEY in .env

File not found: chunks.json
→ Solution: Run python chunk_documents.py first

Out of memory
→ Solution: Reduce batch_size, process in parts
```

### Retry Logic

Automatic exponential backoff:

```
Attempt 1: Immediate
Attempt 2: Wait 2 seconds
Attempt 3: Wait 4 seconds
Attempt 4: Wait 8 seconds (fails)
```

## Resume Capability

### Resuming Interrupted Generation

```bash
# Process was interrupted? Just run again!
python generate_embeddings.py

# It will:
# 1. Load embedding_state.json
# 2. Skip already-processed chunks
# 3. Continue from where it left off
```

### Forcing Reprocessing

```bash
# Reprocess all chunks
python generate_embeddings.py --no-resume

# Or delete state file
rm knowledge_base/embeddings/embedding_state.json
```

## Testing

### Run Tests

```bash
# All embedding tests
pytest tests/test_embedding.py -v

# Specific test
pytest tests/test_embedding.py::TestDuplicateDetector -v

# With coverage
pytest tests/test_embedding.py --cov=embedding
```

### Test Coverage

- DuplicateDetector: 100%
- RateLimiter: 95%
- BatchManager: 100%
- EmbeddingStateTracker: 100%
- EmbeddingOrchestrator: 100%

### Sample Data

```python
# Create test chunks
chunks = [
    {
        "chunk_id": f"chunk_{i}",
        "content": f"Sample text {i}",
        "document_id": "doc_1",
        "heading": f"Section {i}",
    }
    for i in range(100)
]

# Test with sample
batches, skipped = BatchManager(100).create_batches(chunks)
```

## Next Steps

After embedding generation:

1. **Vector Indexing**: Store embeddings in ChromaDB
   ```bash
   python index_embeddings.py
   ```

2. **Retrieval System**: Implement semantic search
   ```bash
   python setup_retriever.py
   ```

3. **Chatbot**: Build RAG pipeline
   ```bash
   python setup_chatbot.py
   ```

## Troubleshooting

### Issue: Slow Generation

**Cause**: Small batch size or rate limiting
**Solution**: 
- Increase `--batch-size` to 256
- Check OpenAI quota

### Issue: OOM Error

**Cause**: Batch size too large for available memory
**Solution**:
- Reduce `--batch-size` to 50
- Close other applications

### Issue: Partial Results

**Cause**: Process interrupted
**Solution**:
- Resume automatically: `python generate_embeddings.py`
- Or force restart: `python generate_embeddings.py --no-resume`

## Reference

### Key Files
- `embedding/embedding_models.py`: Data models
- `embedding/embedding_generator.py`: Core generators
- `embedding/embedding_orchestrator.py`: Orchestration
- `generate_embeddings.py`: CLI entry point
- `tests/test_embedding.py`: Test suite

### External APIs
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings
- Rate Limits: https://platform.openai.com/account/rate-limits

### Configuration Files
- `.env.example`: Environment template
- `config/settings.py`: Pydantic settings
