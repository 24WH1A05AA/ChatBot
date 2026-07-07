# 🚀 Quick Start Guide - College FAQ Chatbot

## Prerequisites

- **Python**: 3.11 or higher
- **Package Manager**: pip or conda
- **API Key**: OpenAI API key (required for LLM and embeddings)
- **Disk Space**: ~5GB for vector database and knowledge base

## Installation Steps

### 1. Clone & Navigate to Project
```bash
cd "C:\Users\marut\OneDrive\Documents\VYSHU\TechVestAgenticAIWorkshop\TechVestWorkshop\ChatBot"
```

### 2. Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file:
```bash
copy .env.example .env
```

Or on macOS/Linux:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Required: Your OpenAI API Key
OPENAI_API_KEY=your_api_key_here

# Website Configuration
COLLEGE_WEBSITE_URL=https://example.com
CRAWL_DEPTH=5
MAX_PAGES=500

# Optional: Adjust based on your needs
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
LOG_LEVEL=INFO
```

## Running the Project

### Option 1: Run Streamlit Dashboard (Recommended for UI)

```bash
streamlit run streamlit_ui/dashboard.py
```

This opens a professional web interface at `http://localhost:8501` with:
- Chat interface for asking questions
- Real-time conversation history
- RAGAS evaluation metrics
- Knowledge base statistics
- Admin settings and controls

### Option 2: Run Python CLI / API Mode

```bash
python app.py
```

This runs the application backend with:
- REST API for programmatic access
- Optimization engine with caching
- Health checks and monitoring
- Graceful shutdown handling

### Option 3: Use Chatbot Programmatically

```python
from chatbot.chatbot import Chatbot

# Initialize chatbot
chatbot = Chatbot()

# Ask a question
response = chatbot.answer("What are the admission requirements?")

# Get response and citations
print(response["message"])
print(response["citations"])
```

## Full RAG Pipeline Walkthrough

### Step 1: Crawl the Website
```python
from crawler.crawl import CrawlerOrchestrator

crawler = CrawlerOrchestrator()
crawler.crawl("https://example.com")
pages = crawler.get_crawled_pages()
print(f"Crawled {len(pages)} pages")
```

### Step 2: Clean & Process Content
The crawler automatically cleans HTML, extracts text, and converts to Markdown:
- HTML → Markdown conversion
- Metadata extraction (title, URL, category)
- Duplicate detection
- Link extraction

### Step 3: Generate Knowledge Base
```python
from ingestion.kb_generators import KBGenerator

kb_gen = KBGenerator()
kb_gen.generate_knowledge_base()
```

### Step 4: Chunk Documents
```python
from ingestion.chunk_processor import ChunkProcessor

processor = ChunkProcessor()
chunks = processor.process_documents()
print(f"Created {len(chunks)} chunks")
```

### Step 5: Generate Embeddings
```python
from embedding.embedding_orchestrator import EmbeddingOrchestrator

embedder = EmbeddingOrchestrator()
embedder.generate_embeddings()
```

### Step 6: Index to ChromaDB
```python
from vectorstore.vectorstore import VectorStore

vs = VectorStore()
vs.index_documents()
```

### Step 7: Retrieve Relevant Documents
```python
from retriever.retrieval_pipeline import RetrievalPipeline

retriever = RetrievalPipeline()
results = retriever.retrieve("How does admission work?", top_k=5)
```

### Step 8: Generate Response with GPT
```python
from chatbot.chatbot import Chatbot

chatbot = Chatbot()
response = chatbot.answer("How does admission work?")
```

### Step 9: Evaluate with RAGAS
```python
from evaluation.ragas_runner import RagasRunner

evaluator = RagasRunner()
scores = evaluator.evaluate_response(response)
print(f"Faithfulness: {scores['faithfulness']}")
print(f"Context Precision: {scores['context_precision']}")
```

### Step 10: View in Streamlit
```bash
streamlit run streamlit_ui/dashboard.py
```

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_chatbot.py -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
```

## Project Structure

```
ChatBot/
├── config/              # Configuration (Pydantic settings)
├── core/                # Core utilities (logger, exceptions, models)
├── crawler/             # Website crawling (Crawl4AI)
├── ingestion/           # Document processing (chunking, KB generation)
├── embedding/           # Embedding generation (OpenAI)
├── vectorstore/         # Vector DB (ChromaDB)
├── retriever/           # Search & retrieval
├── chatbot/             # Main chatbot logic (LangChain)
├── prompts/             # LLM prompts
├── evaluation/          # RAGAS metrics
├── security/            # Input validation & prompt injection protection
├── memory/              # Conversation memory
├── scheduler/           # Automated tasks
├── analytics/           # Metrics collection
├── admin/               # Admin dashboard
├── streamlit_ui/        # Web UI (dashboard)
├── tests/               # Unit & integration tests
├── knowledge_base/      # Stored documents
│   ├── raw/            # Raw crawled content
│   ├── markdown/       # Processed markdown
│   ├── cleaned/        # Cleaned documents
│   └── embeddings/     # Embedding vectors
└── logs/                # Application logs
```

## Common Commands

### Check Project Health
```bash
# Run tests
pytest tests/ -v --tb=short

# Check code quality
flake8 . --max-line-length=120
black --check .
mypy .
```

### Clear Cache
```bash
# Remove ChromaDB vector store
rm -rf vectorstore/chroma_db

# Remove knowledge base
rm -rf knowledge_base/*

# Clear logs
rm -rf logs/*
```

### Debug Mode
```bash
# Run with debug logging
DEBUG=True streamlit run streamlit_ui/dashboard.py

# Or set in .env
LOG_LEVEL=DEBUG
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution:** Make sure `.env` file exists and contains your OpenAI API key:
```env
OPENAI_API_KEY=sk-...
```

### Issue: "ChromaDB connection error"
**Solution:** Ensure directory exists:
```bash
mkdir -p vectorstore/chroma_db
```

### Issue: "Module not found" errors
**Solution:** Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: Streamlit port already in use
**Solution:** Run on different port:
```bash
streamlit run streamlit_ui/dashboard.py --server.port 8502
```

### Issue: Out of memory when crawling
**Solution:** Reduce crawl depth in `.env`:
```env
CRAWL_DEPTH=3
MAX_PAGES=100
```

## Environment Variables Explained

```env
# Required - OpenAI API Key for LLM and embeddings
OPENAI_API_KEY=your_key

# Crawling
COLLEGE_WEBSITE_URL=https://example.com  # Website to crawl
CRAWL_DEPTH=5                             # How deep to follow links
MAX_PAGES=1000                            # Maximum pages to crawl

# Database
CHROMA_DB_PATH=./vectorstore/chroma_db    # Vector DB location
PERSIST_DIRECTORY=./knowledge_base        # Knowledge base location

# Processing
CHUNK_SIZE=1000                           # Characters per chunk
CHUNK_OVERLAP=200                         # Overlap between chunks
TOP_K=5                                   # Search results to return

# Performance
CACHE_ENABLED=True                        # Enable caching
PARALLEL_WORKERS=4                        # Number of parallel workers
BATCH_SIZE=32                             # Batch processing size

# Logging
LOG_LEVEL=INFO                            # DEBUG, INFO, WARNING, ERROR
DEBUG=False                               # Enable debug mode
ENVIRONMENT=production                    # dev, staging, production
```

## Next Steps

1. **Crawl your website**: Customize `COLLEGE_WEBSITE_URL` in `.env`
2. **Ask questions**: Use the Streamlit dashboard to interact with the chatbot
3. **Evaluate performance**: Check RAGAS scores in the dashboard
4. **Optimize**: Adjust chunk size, top_k, and model parameters
5. **Deploy**: See deployment guide for production setup

## Support & Documentation

- **Full Documentation**: See `README.md`
- **Technical Spec**: See `Spec.md`
- **Project Structure**: See `PROJECT_STRUCTURE_ANALYSIS.md`
- **Architecture**: Check module docstrings and code comments
- **Tests**: Run `pytest --help` for testing options

---

**Happy chatbotting! 🚀**
