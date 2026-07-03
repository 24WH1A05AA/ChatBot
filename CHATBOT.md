# Chatbot Implementation Guide

Complete guide to the production college FAQ chatbot with integrated RAG pipeline.

## Overview

The chatbot implements the complete pipeline:
```
Question → Retriever → Prompt Builder → GPT-4o Mini → Answer + Citations
```

## Pipeline Architecture

### Pipeline Flow

```
User Query
  ↓
[Greeting Check] → Greeting Response (fast path)
  ↓
[Retriever] → Retrieve 5 relevant chunks with similarity scores
  ↓
[Context Builder] → Format chunks into context
  ↓
[Prompt Orchestrator] → Select prompt (default/follow-up/conflict)
  ↓
[System Prompt] → Enforce 8 critical rules
  ↓
[LLM (GPT-4o Mini)] → Generate response with citations
  ↓
[Response Validator] → Check hallucination, citations, facts
  ↓
[Answer] → Return cited response + metadata
  ↓
[Tracking] → Record conversation, metrics, sources
```

### Components

1. **Chatbot** - Main orchestrator
2. **RetrievalPipeline** - Semantic search
3. **PromptOrchestrator** - Prompt selection & building
4. **ResponseHandler** - Response generation & validation
5. **Streamlit UI** - Interactive interface

## Installation & Setup

### Prerequisites

```bash
pip install streamlit openai chromadb loguru
```

### Environment Setup

```bash
# Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# Or in .env
OPENAI_API_KEY=sk-...
```

### Initialize Vector Store

```bash
# First, ensure embeddings are indexed
python index_embeddings.py index
```

## Usage

### Run Chatbot

```bash
# Interactive Streamlit UI
streamlit run streamlit_ui/chat_interface.py

# Opens at: http://localhost:8501
```

### Programmatic Usage

```python
from pathlib import Path
from vectorstore.vectorstore import VectorStore
from chatbot.chatbot import Chatbot

# Initialize
vectorstore = VectorStore(
    collection_name="college_faq",
    persist_dir=Path("knowledge_base/vectorstore"),
)

chatbot = Chatbot(
    vectorstore=vectorstore,
    llm_model="gpt-4o-mini",
    max_conversation_history=20,
    retrieval_k=5,
    temperature=0.0,
)

# Chat
response = await chatbot.chat(
    query="What is the admission deadline?",
    section="Admissions",  # Optional
    department="General",   # Optional
)

print(response["response"])
print(f"Sources: {response['sources']}")
print(f"Latency: {response['metrics']['total_latency_ms']}ms")
```

## Components

### Chatbot Class

Main orchestrator integrating all components.

```python
chatbot = Chatbot(
    vectorstore=vectorstore,
    llm_model="gpt-4o-mini",           # Model to use
    max_conversation_history=20,        # Max turns
    retrieval_k=5,                      # Chunks to retrieve
    temperature=0.0,                    # Deterministic
)
```

**Methods:**

```python
# Chat with query
response = await chatbot.chat(
    query="Your question?",
    section=None,           # Optional filter
    department=None,        # Optional filter
)

# Get conversation history
history = chatbot.get_conversation_history()

# Get metrics
metrics = chatbot.get_metrics()

# Clear conversation
chatbot.clear_conversation()

# Export to file
chatbot.export_conversation("conversation.json")
```

### Chat Response Format

```python
{
    "query": "What is the deadline?",
    "response": "The deadline is March 31 [Source: Admissions]",
    "type": "answered",  # answered, refusal, conflict, etc.
    "sources": [
        {
            "url": "https://college.edu/admissions",
            "section": "Admissions",
            "title": "Application Deadline",
            "similarity_score": 0.95,
        }
    ],
    "retrieved_chunks": [
        {
            "chunk_id": "chunk_123",
            "text": "The application deadline...",
            "metadata": {...},
            "similarity_score": 0.95,
        }
    ],
    "metrics": {
        "total_latency_ms": 2500.0,
        "retrieval_ms": 150.0,
        "llm_ms": 2200.0,
        "tokens_used": 450,
    },
    "validation": {
        "has_citations": True,
        "passes_validation": True,
    },
    "success": True,
}
```

## Features

### 1. Retrieval Pipeline

- Semantic search with cosine similarity
- Top-K retrieval (configurable)
- Section & department filtering
- Duplicate removal
- Score thresholding
- Batch processing

**Configuration:**

```python
chatbot.retrieval_k = 5           # Number of chunks
pipeline.retrieve(
    query="...",
    section="Admissions",         # Optional
    department="General",         # Optional
    min_score=0.3,               # Optional threshold
)
```

### 2. Prompt Management

- Base system prompt with 8 critical rules
- Context-aware simplified prompt
- Follow-up prompt for multi-turn
- Conflict handling prompt
- Refusal prompt for graceful failures
- Automatic scenario selection

**Scenarios:**

```python
# Automatic selection based on context
- "default": First query
- "follow_up": Subsequent queries
- "conflict": Multiple conflicting sources
- "refusal": No context available
```

### 3. LLM Integration

- GPT-4o Mini model
- Temperature = 0.0 (deterministic)
- System prompt enforcement
- Rate limiting with exponential backoff
- Error recovery

**Customization:**

```python
chatbot.llm_model = "gpt-4o-mini"
chatbot.temperature = 0.0  # Deterministic
```

### 4. Response Validation

- Hallucination detection
- Citation verification
- Factual claim checking
- Comprehensive validation report
- Response adjustment

### 5. Conversation Management

- Multi-turn conversation tracking
- Configurable history size
- Context-aware follow-ups
- Conversation export/import
- Metric tracking

### 6. Metrics & Monitoring

- Query count
- Latency tracking (retrieval + LLM)
- Token usage
- Response type distribution
- Performance analytics

**Metrics Access:**

```python
metrics = chatbot.get_metrics()

{
    "total_queries": 10,
    "avg_latency_ms": 2345.0,
    "total_tokens": 4500,
    "avg_retrieval_ms": 150.0,
    "avg_llm_ms": 2200.0,
    "response_type_distribution": {
        "answered": 8,
        "refusal": 2,
    },
}
```

## Handling Special Cases

### Greetings

Detected and handled with predefined responses:

```
User: "Hello"
Assistant: "Hello! I'm the college FAQ chatbot. How can I help?"
```

**Greeting triggers:**
- hello, hi, hey, greetings
- good morning, good afternoon, good evening

### Unknown Questions

No relevant context found:

```
User: "What's the capital of France?"
Assistant: "I don't have information about this in the college knowledge base..."
```

### Multi-Turn Conversations

Maintains context across exchanges:

```
User: "What is the admission deadline?"
Assistant: "The deadline is March 31..."

User: "How long before that should I apply?"
Assistant: "As mentioned, the deadline is March 31. Most students apply..."
```

### Error Handling

Graceful error recovery:

```python
try:
    response = await chatbot.chat(query)
except Exception as e:
    return {
        "response": "An error occurred. Please try again.",
        "type": "error",
        "success": False,
    }
```

## Streamlit UI

Interactive web interface built with Streamlit.

### Features

- **Chat Interface** - Real-time conversation
- **Source Display** - Retrieved chunks with metadata
- **Metrics Dashboard** - Performance tracking
- **Conversation History** - Full exchange history
- **Export** - Save conversations to JSON
- **Filters** - Section and department filtering
- **Settings** - Configurable retrieval parameters

### Running

```bash
streamlit run streamlit_ui/chat_interface.py
```

### UI Components

1. **Main Chat Area**
   - Conversation display
   - Input field
   - Real-time response

2. **Sources Sidebar**
   - Retrieved chunks
   - Similarity scores
   - URLs

3. **Settings Sidebar**
   - Section filter
   - Department filter
   - Retrieval K
   - Metrics display

4. **Controls**
   - Clear conversation
   - Export conversation
   - Performance stats

## Performance

### Benchmarks

| Component | Time | Notes |
|-----------|------|-------|
| Greeting check | <1ms | Regex match |
| Retrieval | ~150ms | ChromaDB query |
| Prompt building | ~50ms | Format chunks |
| LLM call | ~2-3s | Network + inference |
| Response validation | ~20ms | Checks |
| **Total** | **~2.5s** | End-to-end |

### Optimization Tips

1. **Cache query embeddings** - Reuse for similar queries
2. **Batch processing** - Process multiple queries together
3. **Pre-filter chunks** - Use section/department filters early
4. **Limit history** - Keep conversation history manageable
5. **Temperature = 0.0** - Deterministic responses (faster)

## Testing

```bash
# Run chatbot tests
pytest tests/test_chatbot.py -v

# Specific test
pytest tests/test_chatbot.py::TestChatbot::test_is_greeting -v

# With coverage
pytest tests/test_chatbot.py --cov=chatbot
```

## Configuration

### Environment Variables

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Chatbot
CHATBOT_MODEL=gpt-4o-mini
CHATBOT_TEMPERATURE=0.0
CHATBOT_RETRIEVAL_K=5
CHATBOT_MAX_HISTORY=20

# Paths
PERSIST_DIRECTORY=./knowledge_base
VECTORSTORE_COLLECTION=college_faq
```

### Code Configuration

```python
chatbot = Chatbot(
    vectorstore=vectorstore,
    llm_model="gpt-4o-mini",           # LLM model
    max_conversation_history=20,        # Max turns
    retrieval_k=5,                      # Chunks to retrieve
    temperature=0.0,                    # Deterministic
)
```

## Troubleshooting

### LLM Rate Limit

```
Error: Rate limit exceeded
Solution: Wait and retry (exponential backoff implemented)
```

### No Retrieved Context

```
User: "Unknown question"
Chatbot: "I don't have information about this..."
Solution: Ask about college-related topics
```

### Slow Response

```
Issue: Slow LLM response
Solution: 
- Check network connection
- Monitor token usage
- Reduce retrieval_k
- Use temperature=0.0 for speed
```

### Memory Issues

```
Issue: High memory with long conversations
Solution:
- Clear conversation: chatbot.clear_conversation()
- Reduce max_conversation_history
- Export and save conversations
```

## Examples

### Example 1: Simple Question

```python
response = await chatbot.chat(
    query="What is the admission deadline?"
)

print(response["response"])
# Output: "The deadline is March 31 [Source: Admissions]"

print(response["metrics"]["total_latency_ms"])
# Output: 2345.0
```

### Example 2: Filtered Search

```python
response = await chatbot.chat(
    query="Tell me about the CS program",
    section="Academics",
    department="Computer Science",
)
```

### Example 3: Multi-Turn

```python
# Turn 1
r1 = await chatbot.chat("What is the admission deadline?")

# Turn 2 - remembers previous context
r2 = await chatbot.chat("How long before that?")

# Both responses are coherent and connected
```

### Example 4: Conversation Export

```python
# Export entire conversation
chatbot.export_conversation("my_conversation.json")

# View metrics
metrics = chatbot.get_metrics()
print(f"Total queries: {metrics['total_queries']}")
print(f"Avg latency: {metrics['avg_latency_ms']}ms")
```

## API Reference

### Chatbot Class

```python
class Chatbot:
    __init__(
        vectorstore: VectorStore,
        llm_model: str = "gpt-4o-mini",
        max_conversation_history: int = 20,
        retrieval_k: int = 5,
        temperature: float = 0.0,
    )
    
    async def chat(
        query: str,
        section: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]
    
    def get_conversation_history() -> List[Dict]
    
    def get_metrics() -> Dict[str, Any]
    
    def clear_conversation() -> None
    
    def export_conversation(filepath: str) -> None
```

### Response Format

Always returns:

```python
{
    "query": str,                    # User query
    "response": str,                 # Assistant response
    "type": str,                     # answered, refusal, etc.
    "sources": List[Dict],          # Retrieved sources
    "retrieved_chunks": List[Dict],  # Full chunk metadata
    "metrics": Dict,                # Performance metrics
    "validation": Dict,             # Validation results
    "success": bool,                # Operation success
}
```

## Next Steps

- Deploy to cloud (AWS/GCP/Azure)
- Add persistent conversation storage
- Implement user authentication
- Add conversation rating/feedback
- Monitor production metrics
- Scale retrieval for larger KB

## Support

For issues or questions:
1. Check logs: `logs/chatbot.log`
2. Review documentation: `CHATBOT.md`
3. Run tests: `pytest tests/test_chatbot.py -v`
4. Check configuration: Review `.env` and code settings
