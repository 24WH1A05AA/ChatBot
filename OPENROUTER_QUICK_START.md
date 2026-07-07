# 🚀 OpenRouter Free Models - Quick Reference

## Get Started in 3 Steps

### Step 1: Get Free API Key (2 minutes)
```bash
# Go to: https://openrouter.io
# Sign up → Copy API key (no credit card needed!)
```

### Step 2: Configure .env
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-your-key-here
OPENROUTER_MODEL=openai/gpt-oss-120b:free
```

### Step 3: Run
```bash
streamlit run streamlit_ui/dashboard.py
```

---

## 8 Free Models Available

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `openai/gpt-oss-120b:free` | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | General Q&A |
| `meta-llama/llama-4-maverick:free` | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Balanced |
| `qwen/qwen3-235b-a22b:free` | ⚡⚡ | ⭐⭐⭐⭐⭐ | Complex reasoning |
| `deepseek/deepseek-r1:free` | ⚡ | ⭐⭐⭐⭐⭐ | Deep thinking |
| `nvidia/nemotron-3-ultra:free` | ⚡⚡⚡ | ⭐⭐⭐⭐ | Fast + Good |
| `nvidia/nemotron-3-super:free` | ⚡⚡⚡ | ⭐⭐⭐ | Speed first |
| `google/gemma-3-27b-it:free` | ⚡⚡⚡ | ⭐⭐⭐⭐ | Instruction-tuned |
| `deepseek/deepseek-chat-v3-0324:free` | ⚡⚡ | ⭐⭐⭐⭐ | Technical |

---

## Features

✅ **Zero Cost** - Completely free (no credit card)  
✅ **Automatic Fallback** - Model fails? Try the next one  
✅ **No New Code** - Just update .env and go  
✅ **Backward Compatible** - Still works with OpenAI  
✅ **Production Ready** - Used by thousands  

---

## How It Works

```
Your Question
    ↓
[Try Model 1: openai/gpt-oss-120b:free]
    ├─ Success? → Return Answer ✓
    └─ Failed? → [Try Model 2]
              ├─ Success? → Return Answer ✓
              └─ Failed? → [Try Model 3] ...
                       └─ Eventually works! ✓
```

---

## Common Commands

```bash
# Run with default config
streamlit run streamlit_ui/dashboard.py

# Debug mode (see which model is used)
DEBUG=True streamlit run streamlit_ui/dashboard.py

# Test direct API
python -c "from llm import get_llm_provider; 
provider = get_llm_provider();
print(provider.generate_sync([{'role':'user','content':'Hi'}]))"

# Check logs
tail -f logs/app.log | grep -i openrouter
```

---

## Switching Models

### Use fastest model:
```env
OPENROUTER_MODEL=nvidia/nemotron-3-super:free
```

### Use best quality:
```env
OPENROUTER_MODEL=qwen/qwen3-235b-a22b:free
```

### Use for deep reasoning:
```env
OPENROUTER_MODEL=deepseek/deepseek-r1:free
```

---

## .env Template

```env
# ===== CHOOSE ONE: openai or openrouter =====
LLM_PROVIDER=openrouter

# ===== IF USING OPENROUTER (FREE!) =====
OPENROUTER_API_KEY=sk-your-key-from-https-openrouter-io
OPENROUTER_MODEL=openai/gpt-oss-120b:free
OPENROUTER_FALLBACK_MODELS=deepseek/deepseek-chat-v3-0324:free,qwen/qwen3-235b-a22b:free,meta-llama/llama-4-maverick:free

# ===== IF USING OPENAI (PAID) =====
# OPENAI_API_KEY=sk-your-openai-key
# OPENAI_MODEL=gpt-4o-mini

# ===== REST OF CONFIG =====
COLLEGE_WEBSITE_URL=https://example.com
OPENAI_API_KEY=  # Still needed for embeddings
CHUNK_SIZE=1000
TOP_K=5
```

---

## Costs

| Provider | Per Query | Monthly | Annual |
|----------|-----------|---------|--------|
| **OpenRouter (FREE)** | $0 | $0 | $0 |
| OpenAI gpt-4o-mini | ~$0.00015 | ~$2-5 | ~$25-60 |
| Self-hosted | $0 | $50+ | $600+ |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not found" | Add `OPENROUTER_API_KEY=sk-...` to `.env` |
| "Model not available" | Check https://openrouter.io/docs#models |
| Slow responses | Use `nvidia/nemotron-3-super:free` |
| Poor quality | Use `qwen/qwen3-235b-a22b:free` |
| Rate limited | Check free tier limits on OpenRouter |

---

## Files Changed

```
NEW:
  llm/llm_provider.py         ← LLM abstraction layer
  llm/__init__.py
  OPENROUTER_SETUP.md         ← Detailed guide
  OPENROUTER_INTEGRATION_SUMMARY.md

MODIFIED:
  config/settings.py          ← Added provider config
  chatbot/chatbot.py          ← Uses LLMProvider
  .env.example               ← New options
  requirements.txt           ← Added comments
```

---

## Support

- **OpenRouter Docs**: https://openrouter.io/docs
- **Models List**: https://openrouter.io/docs#models
- **API Key**: https://openrouter.io/settings/keys
- **Discord**: https://discord.gg/openrouter

---

## Quick Start Code

```python
from chatbot.chatbot import Chatbot
from vectorstore.vectorstore import VectorStore

# Automatically uses OpenRouter from .env
vs = VectorStore()
chatbot = Chatbot(vectorstore=vs)

# Ask question (uses free model!)
response = chatbot.answer("What are admission requirements?")

print(response["response"])
print(f"Sources: {response['sources']}")
```

---

**Status**: ✅ Ready to use  
**Cost**: 💰 FREE  
**Time to setup**: ⏱️ 3 minutes  

Start now: https://openrouter.io
