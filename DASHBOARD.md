# Professional Streamlit Dashboard Guide

Complete guide to the professional college FAQ chatbot dashboard with dark mode, metrics, and advanced settings.

## Overview

The dashboard provides:
- **Professional UI** - Dark mode, responsive layout
- **Knowledge Base Stats** - Embeddings, model info, storage
- **Retriever Settings** - Top K, similarity threshold, filters
- **Performance Metrics** - Latency, tokens, query count
- **RAGAS Scores** - Quality evaluation metrics
- **Chat Interface** - Real-time conversation
- **Source Display** - Expandable citations with metadata

## Quick Start

```bash
# Start the professional dashboard
streamlit run streamlit_ui/dashboard.py

# Opens at: http://localhost:8501
```

## Interface Components

### Sidebar

**📚 Knowledge Base**
- Total embeddings count
- Embedding model (text-embedding-3-small)
- Metadata field count
- Storage size in MB
- Collection name

**⚙️ Retriever Settings**
- Top K slider (1-20, default 5)
- Similarity threshold slider (0.0-1.0, default 0.3)
- Section filter dropdown
- Department filter dropdown

**📊 Performance Metrics**
- Total queries
- Average latency (end-to-end)
- Total tokens used
- Average retrieval time
- Average LLM time
- Response type distribution chart

**🎯 RAGAS Scores**
- Faithfulness (to retrieved context)
- Context Precision (relevant documents)
- Context Recall (coverage)
- Answer Relevancy (to question)
- Overall quality score

### Main Chat Area

**💬 Chat Interface**
- Conversation history display
- User/assistant message styling
- Typing indicator animation
- Expandable sources section
- Expandable retrieved chunks
- Per-query latency metrics

**📚 Sources Display**
- Expandable source cards
- Section name and number
- Clickable URLs
- Relevance scores (similarity %)

**📖 Retrieved Chunks**
- Chunk heading and content preview
- Section and URL info
- Full expandable content
- Chunk index

**📊 Query Metrics**
- Total latency (end-to-end)
- Retrieval time breakdown
- Tokens used for response

## Features

### Dark Mode Theme

Colors:
- **Primary**: #1f77b4 (Blue)
- **Secondary**: #ff7f0e (Orange)
- **Success**: #2ca02c (Green)
- **Danger**: #d62728 (Red)
- **Background**: #0e1117 (Almost black)
- **Surface**: #161b22 (Dark gray)
- **Border**: #30363d (Subtle gray)

### Responsive Layout

- **Sidebar**: Knowledge base stats, settings, metrics
- **Main**: Chat interface with full-width capability
- **Columns**: Auto-responsive grid layout
- **Mobile**: Works on all screen sizes

### Professional Styling

- Metric cards with hover effects
- Expandable sections for detailed info
- Syntax highlighting for code blocks
- Smooth animations
- Consistent spacing and padding

### Typing Indicator

Animated dots while waiting for LLM response:
```
Thinking ⠋ ⠙ ⠹
```

## Configuration

### Retriever Settings

**Top K Results**
- Range: 1-20
- Default: 5
- Controls number of chunks retrieved
- Adjustable per query

**Similarity Threshold**
- Range: 0.0-1.0
- Default: 0.3
- Minimum relevance score
- Adjustable per query

**Filters**
- Section: All, Admissions, Academics, Campus, Placements, Student Life
- Department: All, General, CS, Electronics, Mechanical
- Optional for each query

### Performance Tracking

Metrics collected per query:
- Query count
- Latency (retrieval + LLM)
- Token usage
- Response type
- Sources retrieved
- Chunks returned

### RAGAS Evaluation

Scores displayed:
- **Faithfulness**: How well response matches retrieved context (target: >0.8)
- **Context Precision**: Precision of retrieved documents (target: >0.75)
- **Context Recall**: Recall of relevant documents (target: >0.8)
- **Answer Relevancy**: How well answer matches question (target: >0.85)

## Usage Examples

### Example 1: Basic Query

```
User: "What is the admission deadline?"

Display:
1. Chat message with response
2. Sources (expandable, showing URL and similarity)
3. Retrieved chunks (expandable, showing content)
4. Metrics (latency breakdown, tokens)
```

### Example 2: Filtered Search

```
Settings:
- Top K: 8
- Similarity Threshold: 0.4
- Section: Admissions
- Department: General

Result:
Only returns relevant chunks from Admissions section
with minimum 0.4 similarity score
```

### Example 3: Multi-Turn Conversation

```
Turn 1: "What is the deadline?"
  → Response with context

Turn 2: "How long before that?"
  → Remembers previous context
  → Provides continuation

Conversation history visible in sidebar
```

## Sidebar Sections

### 📚 Knowledge Base

Shows current state of vector database:
- Embedding count
- Model and dimensions
- Metadata fields count
- Storage usage
- Collection name

Updates when new embeddings are added.

### ⚙️ Retriever Settings

Configure search behavior:
- Adjust Top K dynamically
- Set similarity threshold
- Filter by section/department
- Settings applied to next query

### 📊 Performance Metrics

Real-time performance tracking:
- Query count in session
- Average latencies
- Token consumption
- Response type distribution
- Bottleneck identification

### 🎯 RAGAS Scores

Quality evaluation dashboard:
- Individual component scores
- Overall system quality
- Visual metric cards
- Performance targets

## Dark Mode

### Color Scheme

Text:
- Primary text: #c9d1d9 (Light gray)
- Secondary text: #8b949e (Medium gray)
- Accent text: #1f77b4 (Blue)

Backgrounds:
- Main: #0e1117 (Very dark)
- Surface: #161b22 (Dark)
- Hover: #0d1117 (Slightly darker)

Borders:
- Default: #30363d (Subtle)
- Accent: #1f77b4 (Blue)

### Visual Elements

- Chat messages: Color-coded by role
- Metric cards: Dark background with blue text
- Source badges: Subtle borders, organized layout
- Expandable sections: Smooth animations
- Buttons: Hover effects on dark background

## Responsive Layout

### Desktop (Wide)

```
┌─────────────────────────────────────┐
│  Header + Controls                  │
├──────────────┬──────────────────────┤
│   Sidebar    │  Chat Interface      │
│              │  (Full width)        │
│ KB Stats     │  - Messages          │
│ Settings     │  - Sources           │
│ Metrics      │  - Chunks            │
│ RAGAS        │  - Metrics           │
└──────────────┴──────────────────────┘
```

### Tablet (Medium)

```
┌─────────────────────────────────────┐
│  Header + Controls                  │
├─────────────────────────────────────┤
│  Chat Interface (Full Width)        │
├─────────────────────────────────────┤
│  Sidebar Tabs (Collapsible)         │
└─────────────────────────────────────┘
```

### Mobile (Narrow)

```
┌─────────────────────────────────────┐
│  Header (Compact)                   │
├─────────────────────────────────────┤
│  Chat Interface                     │
│  (Stacked Layout)                   │
├─────────────────────────────────────┤
│  Sidebar (Hidden/Drawer)            │
└─────────────────────────────────────┘
```

## Advanced Features

### Citation Expansion

Click expandable sections to see:
- Full URLs (clickable links)
- Similarity scores as percentages
- Source section information
- Metadata details

### Chunk Preview

Expandable chunks show:
- Chunk heading
- Content preview (300 chars)
- Section information
- Source URL
- Full content on expansion

### Metrics Breakdown

Per-query metrics display:
- End-to-end latency
- Retrieval time (ChromaDB)
- LLM inference time
- Tokens used
- Comparison to averages

### Session Statistics

Sidebar metrics show:
- Cumulative query count
- Average latencies
- Token consumption
- Response distribution
- Quality scores

## Performance Optimization

### Frontend

- Lazy loading of messages
- Expandable sections reduce rendering
- Efficient re-renders
- Minimal CSS calculations

### Backend

- Caching of vectorstore stats
- Batch metrics collection
- Efficient chunk filtering
- Rate-limited API calls

## Troubleshooting

### Slow Response

- Check retrieval time in metrics
- Reduce Top K setting
- Increase similarity threshold
- Check network latency

### High Token Usage

- Shorter queries use fewer tokens
- Fewer retrieved chunks = fewer tokens
- Check LLM response length in metrics

### Quality Issues

- Check RAGAS scores in sidebar
- Verify similarity threshold
- Check retrieved chunks relevance
- Review source metadata

## Customization

### Colors

Edit CSS in `configure_page()`:
```python
--primary-color: #1f77b4;      # Change color
--secondary-color: #ff7f0e;
--success-color: #2ca02c;
```

### Layout

Modify column widths:
```python
col1, col2 = st.columns([3, 1])  # 75/25 split
col1, col2, col3 = st.columns(3) # Equal split
```

### Settings

Adjust defaults in sidebar:
```python
top_k = st.slider(..., value=5)           # Default K
threshold = st.slider(..., value=0.3)     # Default threshold
```

## API Integration

The dashboard integrates with:

**Chatbot** (chatbot.py)
- `chat()` - Process queries
- `get_metrics()` - Retrieve metrics
- `clear_conversation()` - Reset history

**VectorStore** (vectorstore.py)
- `get_statistics()` - KB stats
- `query()` - Semantic search

**RetrievalPipeline** (retrieval_pipeline.py)
- `retrieve()` - Get chunks with context

**PromptOrchestrator** (prompt_orchestrator.py)
- `select_system_prompt()` - Pick prompt
- `build_user_message()` - Format message

## Performance Targets

- Dashboard load: < 2 seconds
- Query response: < 3 seconds
- Metric update: < 100ms
- Sidebar rendering: < 500ms

## Next Steps

1. Run dashboard:
   ```bash
   streamlit run streamlit_ui/dashboard.py
   ```

2. Test functionality:
   - Ask questions
   - Adjust filters
   - Monitor metrics
   - Review RAGAS scores

3. Customize:
   - Adjust colors
   - Change layout
   - Add filters
   - Modify metrics

4. Deploy:
   - Docker container
   - Cloud hosting
   - Load balancer
   - Monitoring

## Support

- Check sidebar for KB stats
- Review metrics for performance
- Check RAGAS scores for quality
- Monitor latency for bottlenecks
- Review retrieved chunks for relevance
