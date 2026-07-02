Project Specification
Project Name

College FAQ Chatbot

Objective

Develop a production-grade AI chatbot capable of automatically crawling an entire college website, extracting all meaningful information, generating embeddings, indexing documents into a vector database, and answering user questions with citations while preventing hallucinations.

Functional Requirements
Website Crawling

The crawler shall

Recursive Crawling
Visit every internal page
Link Discovery

Extract

navigation links
footer links
sidebar links
dropdown links
hidden links
Dynamic Rendering

Support

JavaScript
React
Vue
Angular
PDF Crawling

Automatically download

Prospectus
Fee Structure
Academic Calendar
Timetable
Notices

Extract text.

HTML Extraction

Extract

headings
paragraphs
lists
tables
accordions
cards
FAQs
forms
links
Image Metadata

Extract

alt text
captions
image title
Metadata

Every page stores

URL

Title

Description

Keywords

Last Modified

Department

Category

Breadcrumb

Section

Language

Timestamp

Page Depth

Parent Page
Data Cleaning

Remove

ads
scripts
css
duplicate text
cookie banners
popups
empty elements
Markdown Generation

Each page becomes

Heading

Subheading

Content

Tables

Links

Metadata

Source URL
Chunking

Recursive Character Splitter

Chunk Size

500

Overlap

100

Metadata

Page
URL
Section
Heading
Chunk ID
Embeddings

Model

text-embedding-3-small

Dimension

1536

Vector Database

ChromaDB

Persistent

Supports

similarity search
metadata filtering
hybrid retrieval
Retrieval

Top K

5

Supports

semantic search
hybrid search
reranking
Prompt Rules

The chatbot

answers only from context
refuses hallucinations
always cites sources
never fabricates
reports conflicting information
Streamlit Dashboard

Displays

Knowledge Base

pages crawled
chunks
embeddings

Retriever

top k
similarity score

Chat

citations
latency
retrieved chunks

Evaluation

ragas
pass rate
Crawl4AI Configuration
Max Depth : Unlimited (configurable)

Concurrent Workers : 10

Respect Robots.txt : Yes

Retry Failed Pages : Yes

Incremental Crawling : Yes

Extract PDFs : Yes

Render JavaScript : Yes

Extract Tables : Yes

Extract Images : Yes

Extract Metadata : Yes

Markdown Output : Yes

JSON Output : Yes

Cache Enabled : Yes

Duplicate Detection : Yes
Evaluation
Functional
Accurate retrieval
Quality
Faithful answers
Safety
No hallucinations
Security
Prompt Injection Resistance
Robustness
Empty input
Long input
Mixed language
Performance

Latency < 5 seconds

Context

Conversation Memory

RAGAS
Faithfulness
Context Recall
Context Precision
Answer Relevancy
Future Enhancements
Incremental website synchronization
Scheduled crawling
OCR for scanned PDFs
Voice-based chatbot
WhatsApp integration
Mobile application
Multi-language support
Elasticsearch hybrid search
Cross-encoder reranking
Neo4j knowledge graph
Admin dashboard
Analytics dashboard
User feedback learning
Automatic website change detection
Email notifications for new announcements
