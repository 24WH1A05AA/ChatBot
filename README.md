🎓 College FAQ Chatbot
AI Powered College Information Assistant

A production-ready Retrieval-Augmented Generation (RAG) chatbot that automatically crawls the complete college website using Crawl4AI, indexes all website content into a vector database, and provides accurate, citation-based answers using GPT-4o Mini.

Unlike traditional FAQ chatbots that rely on manually created documents, this system continuously builds its knowledge base by recursively crawling the official college website.

Features
🌐 Intelligent Website Crawling
Crawl the entire college website automatically
Recursive crawling
Multi-page discovery
Internal link extraction
Smart duplicate detection
Incremental crawling
Sitemap support
JavaScript rendering
PDF extraction
Image metadata extraction
Markdown generation
HTML preservation
Metadata extraction
📚 Knowledge Base Generation

Automatically extracts

About College
Departments
Faculty
Courses
Placements
Admissions
Fee Structure
Academic Calendar
Notifications
Circulars
Events
Research
Publications
Laboratories
Hostel
Transport
Sports
Library
Scholarships
Contact Information
Gallery captions
Downloadable PDFs
Examination Notices
Results
News
Clubs
Student Chapters

Everything is automatically converted into structured Markdown documents.

🤖 RAG Pipeline
Crawl4AI
LangChain
Recursive Chunking
OpenAI Embeddings
ChromaDB
Hybrid Search
Metadata Filtering
GPT-4o Mini
Citation Generation
🧠 Smart Retrieval

Supports

Semantic Search
Similarity Search
Metadata Filtering
Section Filtering
Parent Document Retrieval
Top-K Retrieval
Hybrid Search
💬 Intelligent Chatbot

The chatbot

Answers only using retrieved context
Never hallucinates
Gives citations
Refuses unsupported questions
Maintains conversation memory
Handles follow-up questions
📈 Evaluation

Uses

RAGAS
Faithfulness
Context Precision
Context Recall
Answer Relevancy
Latency
Eight Dimension Testing
🛡 Prompt Injection Protection

Blocks

Ignore previous instructions
Reveal system prompt
Show vector database
List documents
Jailbreak prompts
📊 Dashboard

Shows

Number of crawled pages
Number of chunks
Vector database size
Embedding model
Latency
Retrieved chunks
RAGAS Scores
Token usage
Tech Stack
Crawling
Crawl4AI
AI
OpenAI GPT-4o Mini
Embeddings
text-embedding-3-small
Framework
LangChain
Vector Database
ChromaDB
UI
Streamlit
Evaluation
RAGAS
Folder Structure
CollegeFAQBot/

│
├── app.py
├── requirements.txt
├── README.md
├── spec.md
│
├── config/
│      settings.py
│
├── crawler/
│      crawl.py
│      sitemap.py
│      parser.py
│      cleaner.py
│      metadata.py
│
├── knowledge_base/
│      raw/
│      markdown/
│      cleaned/
│      embeddings/
│
├── ingestion/
│      loader.py
│      chunker.py
│      embedder.py
│      index.py
│
├── vectorstore/
│      chroma_db/
│
├── retriever/
│      retriever.py
│      reranker.py
│
├── prompts/
│      system_prompt.py
│      evaluation_prompt.py
│
├── chatbot/
│      chatbot.py
│
├── evaluation/
│      ragas.py
│      judge.py
│      report.py
│
├── tests/
│
└── streamlit/
       dashboard.py
Workflow
Website

↓

Crawl4AI

↓

Extract Pages

↓

Extract Metadata

↓

Generate Markdown

↓

Chunk

↓

Embeddings

↓

ChromaDB

↓

Retriever

↓

GPT

↓

Answer + Citation
