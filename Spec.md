# College FAQ Chatbot - Specification Document

## Overview
A production-ready Retrieval-Augmented Generation (RAG) chatbot that automatically crawls the college website, indexes content into a vector database, and provides accurate, citation-based answers using GPT-4o Mini.

## Project Scope

### Phase 1: Foundation
- [ ] Project structure and configuration setup
- [ ] Logging and error handling infrastructure
- [ ] Environment configuration management
- [ ] Type hints and validation

### Phase 2: Web Crawling
- [ ] Crawl4AI integration
- [ ] Recursive website crawling
- [ ] Sitemap support
- [ ] PDF extraction
- [ ] Metadata extraction
- [ ] Markdown generation

### Phase 3: Knowledge Base
- [ ] Document parsing and cleaning
- [ ] Chunking strategies
- [ ] Embedding generation (text-embedding-3-small)
- [ ] ChromaDB integration

### Phase 4: Retrieval & RAG
- [ ] Semantic search implementation
- [ ] Hybrid search (semantic + metadata filtering)
- [ ] Parent document retrieval
- [ ] Reranking

### Phase 5: Chatbot
- [ ] LangChain integration
- [ ] Prompt engineering
- [ ] Conversation memory
- [ ] Citation generation
- [ ] Prompt injection protection

### Phase 6: Evaluation
- [ ] RAGAS metrics implementation
- [ ] Faithfulness scoring
- [ ] Context precision/recall
- [ ] Answer relevancy
- [ ] Latency tracking

### Phase 7: UI & Dashboard
- [ ] Streamlit chatbot interface
- [ ] Dashboard with metrics
- [ ] Document management
- [ ] Configuration interface

## Technical Requirements

### Architecture
- **Pattern**: Clean Architecture with Dependency Injection
- **Principles**: SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion)
- **Code Style**: PEP 8, Type hints, Comprehensive docstrings

### Data Flow
```
Website → Crawl4AI → Parsing → Markdown Generation → 
Chunking → Embeddings → ChromaDB → Retriever → 
LLM Processing → Response + Citations
```

### Configuration Management
- Environment-based configuration (.env files)
- Config classes with validation (Pydantic)
- Settings per environment (dev, staging, production)

### Error Handling
- Custom exception hierarchy
- Graceful degradation
- Error logging and tracking
- User-friendly error messages

### Performance
- Async I/O for crawling
- Caching for embeddings
- Batch processing
- Latency tracking

## API Specifications

### Crawler Service
- Input: Website URL
- Output: Cleaned markdown documents with metadata
- Error Handling: Invalid URLs, network errors, timeouts

### Ingestion Service
- Input: Raw documents
- Output: Indexed vectors in ChromaDB
- Processes: Chunking, embedding, metadata preservation

### Retriever Service
- Input: Query string
- Output: Top-K relevant documents with metadata
- Supports: Semantic search, metadata filtering, reranking

### Chatbot Service
- Input: User query with conversation history
- Output: Response with citations
- Features: Context awareness, prompt injection protection

### Evaluation Service
- Input: Generated responses with ground truth
- Output: RAGAS scores and metrics
- Metrics: Faithfulness, context precision/recall, relevancy

## Security Considerations

1. **Prompt Injection Protection**
   - Input validation and sanitization
   - System prompt isolation
   - Query filtering

2. **API Keys**
   - Stored in environment variables
   - Never logged or exposed
   - Rotation-ready

3. **Data Privacy**
   - No PII storage without consent
   - Audit logging for access
   - Encryption for sensitive data

## Performance Targets

- Website crawl: < 30 minutes for 500 pages
- Embedding generation: < 2 seconds per document
- Query retrieval: < 500ms
- LLM response: < 3 seconds
- Dashboard load: < 2 seconds

## Deployment

### Development
- Local execution with .env.example
- SQLite/local ChromaDB
- Console logging

### Production
- Docker containerization
- Environment-based configuration
- CloudSQL/managed ChromaDB
- Structured logging (JSON)
- CI/CD integration

## Success Metrics

1. **Quality**
   - RAGAS Faithfulness: > 0.8
   - Context Precision: > 0.75
   - Context Recall: > 0.8

2. **Performance**
   - Average query latency: < 1 second
   - System uptime: > 99.5%
   - Error rate: < 0.1%

3. **User Experience**
   - Citation accuracy: 100%
   - Relevant answers: > 90%
   - User satisfaction: > 4.5/5

## Future Enhancements

- Multi-language support
- Follow-up question refinement
- Feedback loop for model improvement
- Advanced search with filters
- Admin panel for knowledge management
- Integration with college management system
