# Quick Start: Professional Dashboard

Get the college FAQ chatbot dashboard running in under 5 minutes.

## Prerequisites

```bash
pip install streamlit openai chromadb loguru
```

## One-Command Start

```bash
# From project root directory
streamlit run streamlit_ui/dashboard.py
```

The dashboard opens at `http://localhost:8501`

## What You'll See

### Sidebar (Left)

1. **📚 Knowledge Base** - Embedding count, model, storage size
2. **⚙️ Retriever Settings** - Top K, threshold, filters
3. **📊 Metrics** - Query count, latency, tokens
4. **🎯 RAGAS Scores** - Quality metrics

### Main Area (Center)

1. **Chat History** - Your previous messages
2. **Input Field** - Ask your question
3. **Response** - Answer with citations
4. **Sources** - Expandable source links
5. **Chunks** - Retrieved context
6. **Metrics** - Per-query latency

## First Query

1. Click the chat input field
2. Type: "What is the admission deadline?"
3. Hit Enter or click Send
4. Watch the metrics update in sidebar

## Key Features to Try

### 1. Adjust Settings (Sidebar)

- Slide **Top K** from 5 to 10 (get more context)
- Move **Similarity Threshold** from 0.3 to 0.5 (stricter matching)
- Select **Admissions** section filter
- Try department filter

### 2. Expand Sources

- Click "📚 Sources" expandable
- See URL, section, relevance score
- Click URL to visit source

### 3. View Retrieved Chunks

- Click "📖 Retrieved Context" expandable
- See full content preview
- Check section and URL

### 4. Monitor Metrics

- Check **Avg Latency** - how fast is the system?
- Check **Total Tokens** - cost tracking
- Watch **Response Type Distribution** - chart of response types

### 5. Check RAGAS Scores

- **Faithfulness** - accuracy to context
- **Context Precision** - relevance of retrieved docs
- **Context Recall** - coverage of relevant docs
- **Answer Relevancy** - match to question

## Multi-Turn Conversation

1. First query: "What is the admission deadline?"
2. Second query: "How long before that should I apply?"
3. System remembers context from first query
4. Response builds on previous exchange

## Clear History

- Click 🗑️ **Clear History** button (top right)
- Starts fresh conversation
- Metrics reset to 0

## Dark Mode

- Automatically enabled (CSS pre-configured)
- Easy on the eyes
- Professional appearance
- Responsive across devices

## Common Tasks

### Search by Department

```
1. Settings sidebar → Department dropdown
2. Select: Computer Science
3. Enter query about CS programs
4. Results filtered to CS department
```

### Get High-Confidence Results

```
1. Settings sidebar → Similarity Threshold
2. Increase from 0.3 to 0.6
3. Ask question
4. Fewer but higher-confidence results
```

### See More Context

```
1. Settings sidebar → Top K
2. Increase from 5 to 15
3. Ask question
4. More sources retrieved
```

### Monitor Performance

```
1. Look at sidebar → Performance Metrics
2. Check "Avg Latency" (how fast?)
3. Check "Total Tokens" (usage)
4. Check retrieval vs LLM breakdown
```

## Customization (Easy)

### Change Dashboard Title

Edit `streamlit_ui/dashboard.py`:
```python
st.title("🎓 My College ChatBot")  # Change text here
```

### Change Retrieval K Default

```python
st.session_state.top_k = 10  # Default is 5
```

### Add New Filter

```python
custom_filter = st.selectbox("Your Filter", ["Option 1", "Option 2"])
```

### Change Color Scheme

Edit CSS in `configure_page()`:
```python
--primary-color: #00ff00;  # Change to your color
```

## Troubleshooting

### Dashboard won't load
```bash
# Make sure you're in the right directory
cd C:\Users\marut\OneDrive\Documents\VYSHU\TechVestAgenticAIWorkshop\TechVestWorkshop\ChatBot

# Reinstall dependencies
pip install streamlit --upgrade

# Try again
streamlit run streamlit_ui/dashboard.py
```

### No embeddings found
```bash
# First, generate embeddings
python generate_embeddings.py

# Then index them
python index_embeddings.py index

# Then run dashboard
streamlit run streamlit_ui/dashboard.py
```

### Slow responses
- Check sidebar metrics - what's the bottleneck?
- Try reducing Top K (faster search)
- Increase Similarity Threshold (fewer chunks to process)

### API errors
- Check OpenAI API key in .env
- Verify OPENAI_API_KEY is set
- Check rate limits

## What's Under the Hood

The dashboard connects:

1. **Chatbot** - Orchestrates everything
2. **Retriever** - Semantic search via ChromaDB
3. **LLM** - GPT-4o Mini for responses
4. **Prompts** - System prompts with citations
5. **VectorStore** - Persistent embeddings

All integrated into one professional interface.

## Next Steps

1. ✅ Run dashboard
2. ✅ Try first query
3. ✅ Explore settings
4. ✅ Check metrics
5. 🔄 Customize colors/settings
6. 📊 Monitor RAGAS scores
7. 🚀 Share with others

## Performance Tips

- **First query slow?** - System loading components
- **Slow retrieval?** - Increase similarity threshold
- **High tokens?** - Reduce Top K
- **High latency?** - Check network, LLM inference

## Pro Tips

- Expand **Sources** to verify citations
- Check **Metrics** sidebar to understand latency
- Review **RAGAS Scores** for quality
- Use **Filters** for focused searches
- Try **multi-turn** questions for context

## Got Questions?

See documentation:
- `DASHBOARD.md` - Full reference
- `CHATBOT.md` - Pipeline details
- `PROMPTS.md` - Citation rules
- `RETRIEVER.md` - Search features

---

**Ready?** Run this:

```bash
streamlit run streamlit_ui/dashboard.py
```

Then ask: "What is the admission deadline?"

Enjoy! 🎓
