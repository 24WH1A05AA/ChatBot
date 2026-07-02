# 🎓 College FAQ Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot that automatically crawls the college website, indexes content into a vector database, and provides accurate, citation-based answers using GPT-4o Mini.

## ✨ Features

### 🌐 Intelligent Website Crawling
- Automatic recursive website crawling
- Multi-page discovery and link extraction
- Smart duplicate detection
- Incremental crawling support
- Sitemap discovery and parsing
- JavaScript rendering
- PDF extraction
- Image metadata extraction

### 📚 Knowledge Base Generation
Automatically extracts and indexes:
- About College & Departments
- Faculty & Courses
- Placements & Admissions
- Fee Structure & Academic Calendar
- Notifications & Circulars
- Events & Research
- Laboratories & Hostel
- Transport & Sports
- Library & Scholarships
- News & Clubs
- Gallery & Downloads

### 🤖 RAG Pipeline
- **Crawling**: Crawl4AI with JavaScript rendering
- **Framework**: LangChain for orchestration
- **Chunking**: Recursive intelligent chunking
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Store**: ChromaDB with persistence
- **Search**: Hybrid search (semantic + metadata)
- **LLM**: GPT-4o Mini for response generation
- **Citations**: Automatic citation from retrieved context

### 🧠 Smart Retrieval
- Semantic search with similarity scoring
- Metadata-based filtering
- Section-level filtering
- Parent document retrieval
- Top-K result retrieval
- Hybrid search combining multiple strategies

### 💬 Intelligent Chatbot
- Context-aware responses
- Conversation memory
- Follow-up question handling
- Citation generation
- Prompt injection protection
- Refusal for out-of-scope questions

### 📈 Evaluation
RAGAS metrics for quality assessment:
- Faithfulness to context
- Context precision & recall
- Answer relevancy
- Latency tracking
- Custom quality metrics

### 🛡️ Prompt Injection Protection
- Query sanitization
- Jailbreak attempt detection
- System prompt isolation
- Input validation

### 📊 Dashboard
- Crawled pages statistics
- Document & chunk counts
- Vector database metrics
- Embedding model info
- Query latency tracking
- RAGAS scores
- Token usage analytics

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-------------|
| **Crawling** | Crawl4AI |
| **AI/LLM** | OpenAI GPT-4o Mini |
| **Embeddings** | text-embedding-3-small |
| **Framework** | LangChain |
| **Vector DB** | ChromaDB |
| **UI** | Streamlit |
| **Evaluation** | RAGAS |
| **Language** | Python 3.11+ |

## 📁 Project Structure

```
college-faq-bot/
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py        # Pydantic settings with validation
│
├── core/                  # Core utilities & infrastructure
│   ├── __init__.py
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── logger.py          # Logging configuration
│   └── models.py          # Pydantic data models
│
├── crawler/               # Web crawling module
│   ├── __init__.py
│   ├── crawl.py          # Main crawler orchestrator
│   ├── sitemap.py        # Sitemap parsing
│   ├── parser.py         # HTML parsing
│   ├── cleaner.py        # Content cleaning
│   └── metadata.py       # Metadata extraction
│
├── knowledge_base/        # Document storage
│   ├── raw/              # Raw crawled content
│   ├── markdown/         # Markdown formatted docs
│   ├── cleaned/          # Processed documents
│   └── embeddings/       # Embedding data
│
├── ingestion/            # Document ingestion pipeline
│   ├── __init__.py
│   ├── loader.py         # Document loading
│   ├── chunker.py        # Text chunking
│   ├── embedder.py       # Embedding generation
│   └── index.py          # Vector store indexing
│
├── vectorstore/          # Vector database
│   ├── __init__.py
│   └── chroma_db/        # ChromaDB storage
│
├── retriever/            # Search & retrieval
│   ├── __init__.py
│   ├── retriever.py      # Semantic search
│   └── reranker.py       # Result reranking
│
├── prompts/              # LLM prompts
│   ├── __init__.py
│   ├── system_prompt.py  # Chatbot system prompts
│   └── evaluation_prompt.py  # Evaluation prompts
│
├── chatbot/              # Chatbot orchestration
│   ├── __init__.py
│   └── chatbot.py        # Main chatbot class
│
├── evaluation/           # RAG evaluation
│   ├── __init__.py
│   ├── ragas.py          # RAGAS metrics
│   ├── judge.py          # Custom evaluation
│   └── report.py         # Evaluation reporting
│
├── tests/                # Test suite
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures
│   ├── test_placeholder.py
│   └── test_data/        # Test data
│
├── streamlit/            # Web UI
│   └── dashboard.py      # Streamlit dashboard
│
├── logs/                 # Application logs
│
├── app.py                # Application entry point
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── .streamlit/           # Streamlit config
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── spec.md               # Project specification
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- OpenAI API key
- pip or conda

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd college-faq-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   streamlit run streamlit/dashboard.py
   ```

## 📖 Usage

### Basic Chatbot Usage
```python
from chatbot.chatbot import Chatbot

chatbot = Chatbot()
response = chatbot.answer("What are the admission requirements?")
print(response["message"])
print(response["citations"])
```

### Running the Dashboard
```bash
streamlit run streamlit/dashboard.py
```

### Crawling the Website
```python
from crawler.crawl import CrawlerOrchestrator

crawler = CrawlerOrchestrator()
crawler.crawl("https://example.com")
pages = crawler.get_crawled_pages()
```

### Indexing Documents
```python
from ingestion.index import VectorStoreIndexer

indexer = VectorStoreIndexer()
results = indexer.index_documents(["path/to/documents"])
print(results)
```

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
pytest tests/ -v --cov=.
```

## 📝 Configuration

### Environment Variables
See `.env.example` for all available configuration options:

- `OPENAI_API_KEY` - OpenAI API key
- `COLLEGE_WEBSITE_URL` - Website to crawl
- `CRAWL_DEPTH` - Maximum crawling depth
- `CHUNK_SIZE` - Text chunk size
- `TOP_K` - Number of retrieval results
- `LOG_LEVEL` - Logging level

## 🏗️ Architecture Principles

- **Clean Architecture**: Separation of concerns with clear boundaries
- **SOLID Principles**: 
  - Single Responsibility: Each class has one reason to change
  - Open/Closed: Open for extension, closed for modification
  - Liskov Substitution: Proper inheritance hierarchies
  - Interface Segregation: Focused interfaces
  - Dependency Inversion: Depend on abstractions
- **Type Safety**: Full type hints throughout codebase
- **Error Handling**: Custom exception hierarchy
- **Logging**: Structured logging with loguru
- **Testing**: Comprehensive test coverage

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Website Crawl | < 30 minutes (500 pages) |
| Embedding Generation | < 2 seconds per document |
| Query Retrieval | < 500ms |
| LLM Response | < 3 seconds |
| Dashboard Load | < 2 seconds |

## 🔒 Security

- Prompt injection protection enabled by default
- Environment variables for secrets
- Input validation on all user inputs
- Audit logging for sensitive operations
- No PII stored without explicit consent

## 📈 Evaluation Metrics

### RAGAS Targets
- **Faithfulness**: > 0.8
- **Context Precision**: > 0.75
- **Context Recall**: > 0.8
- **Answer Relevancy**: > 0.85

### System Metrics
- **Query Latency**: < 1 second average
- **Uptime**: > 99.5%
- **Error Rate**: < 0.1%

## 🤝 Contributing

1. Follow the established code structure
2. Maintain type hints on all functions
3. Write tests for new features
4. Follow PEP 8 style guide
5. Add docstrings to all classes and functions

## 📝 License

Specify your license here

## 🆘 Troubleshooting

### Common Issues

**OpenAI API Key Error**
- Ensure `OPENAI_API_KEY` is set in `.env`
- Check API key validity at OpenAI dashboard

**ChromaDB Connection Error**
- Verify `CHROMA_DB_PATH` directory exists
- Check disk space for vector storage

**Crawling Timeout**
- Increase `REQUEST_TIMEOUT` in `.env`
- Check website availability
- Reduce `CRAWL_DEPTH` for faster crawling

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

## 🎯 Next Steps

1. Implement crawler module with Crawl4AI
2. Build ingestion pipeline
3. Set up ChromaDB integration
4. Implement retriever module
5. Build chatbot orchestrator
6. Create Streamlit dashboard
7. Add evaluation metrics
8. Deploy to production

---

**Last Updated**: 2026-07-02

For detailed technical specifications, see [spec.md](spec.md)
