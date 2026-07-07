"""
OpenRouter Integration Guide - College FAQ Chatbot

This guide explains how to use FREE LLM models from OpenRouter
instead of paid OpenAI API.
"""

# ============================================================================
# QUICK START - Using Free Models with OpenRouter
# ============================================================================

# 1. GET YOUR FREE OPENROUTER API KEY
# ============================================================================
# Go to: https://openrouter.io
# - Sign up (free account)
# - Get your API key from settings
# - You get $5 free trial credit monthly (no credit card needed!)

# 2. SETUP .env FILE
# ============================================================================
# Copy template and update:

"""
# In .env file:
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_from_step_1

# Choose PRIMARY model (recommended for college FAQ):
OPENROUTER_MODEL=openai/gpt-oss-120b:free
# or: deepseek/deepseek-chat-v3-0324:free
# or: meta-llama/llama-4-maverick:free

# FALLBACK models (comma-separated, tried if primary fails):
OPENROUTER_FALLBACK_MODELS=deepseek/deepseek-chat-v3-0324:free,qwen/qwen3-235b-a22b:free,deepseek/deepseek-r1:free,meta-llama/llama-4-maverick:free,nvidia/nemotron-3-super:free,nvidia/nemotron-3-ultra:free,google/gemma-3-27b-it:free

# Keep embedding provider as OpenAI (uses same API key):
EMBEDDING_PROVIDER=openai
"""

# 3. INSTALL DEPENDENCIES
# ============================================================================
"""
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
"""

# 4. RUN THE CHATBOT
# ============================================================================
"""
streamlit run streamlit_ui/dashboard.py
"""

# ============================================================================
# AVAILABLE FREE MODELS
# ============================================================================

AVAILABLE_MODELS = {
    "openai/gpt-oss-120b:free": {
        "provider": "OpenAI",
        "params": "120B",
        "speed": "Fast",
        "quality": "Excellent",
        "best_for": "General questions"
    },
    "deepseek/deepseek-chat-v3-0324:free": {
        "provider": "DeepSeek",
        "params": "Large",
        "speed": "Medium",
        "quality": "Very Good",
        "best_for": "Technical content"
    },
    "qwen/qwen3-235b-a22b:free": {
        "provider": "Alibaba Qwen",
        "params": "235B",
        "speed": "Medium",
        "quality": "Excellent",
        "best_for": "Multilingual, complex reasoning"
    },
    "deepseek/deepseek-r1:free": {
        "provider": "DeepSeek",
        "params": "Large",
        "speed": "Slower",
        "quality": "Excellent",
        "best_for": "Complex reasoning"
    },
    "meta-llama/llama-4-maverick:free": {
        "provider": "Meta Llama",
        "params": "405B",
        "speed": "Fast",
        "quality": "Excellent",
        "best_for": "General purpose"
    },
    "nvidia/nemotron-3-super:free": {
        "provider": "NVIDIA",
        "params": "8B",
        "speed": "Very Fast",
        "quality": "Good",
        "best_for": "Fast responses"
    },
    "nvidia/nemotron-3-ultra:free": {
        "provider": "NVIDIA",
        "params": "Large",
        "speed": "Fast",
        "quality": "Excellent",
        "best_for": "Balanced performance"
    },
    "google/gemma-3-27b-it:free": {
        "provider": "Google Gemma",
        "params": "27B",
        "speed": "Fast",
        "quality": "Very Good",
        "best_for": "Instruction following"
    }
}

# ============================================================================
# HOW IT WORKS - Model Fallback System
# ============================================================================

"""
When you ask a question:

1. Query → Retriever finds relevant context
2. LLM Call → Tries PRIMARY model (openai/gpt-oss-120b:free)
   ├─ SUCCESS? → Return answer ✓
   └─ FAILED? → Try next fallback model
3. Fallback Models → Automatically try each model in list
   ├─ deepseek/deepseek-chat-v3-0324:free
   ├─ qwen/qwen3-235b-a22b:free
   ├─ deepseek/deepseek-r1:free
   ├─ meta-llama/llama-4-maverick:free
   ├─ nvidia/nemotron-3-super:free
   ├─ nvidia/nemotron-3-ultra:free
   └─ google/gemma-3-27b-it:free
4. Answer → Returns response from first working model

This ensures your chatbot keeps working even if one model is overloaded!
"""

# ============================================================================
# SWITCHING BETWEEN OPENAI AND OPENROUTER
# ============================================================================

# To use OpenAI (paid):
"""
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini
"""

# To use OpenRouter (FREE):
"""
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-oss-120b:free
"""

# ============================================================================
# CODE EXAMPLE - Using in Your Application
# ============================================================================

"""
from chatbot.chatbot import Chatbot
from vectorstore.vectorstore import VectorStore

# Initialize (automatically uses provider from .env)
vs = VectorStore()
chatbot = Chatbot(vectorstore=vs)

# Ask question (uses OpenRouter with fallback)
response = chatbot.answer("What are the admission requirements?")
print(response["message"])
print(response["citations"])
"""

# ============================================================================
# MONITORING & DEBUGGING
# ============================================================================

"""
Check which model is being used:
- Logs show: "Model X marked as failed, will use fallback"
- Or: "Trying fallback model: Y"

View real-time model selection in Streamlit dashboard:
- Admin tab shows model status
- Logs display which model answered your question

Enable debug logging:
"""

# In .env:
LOG_LEVEL=DEBUG

# ============================================================================
# COST COMPARISON
# ============================================================================

# OpenRouter Free Models: $0
# - $5 free trial monthly (no credit card!)
# - Each query uses very little credit

# OpenAI gpt-4o-mini: ~$0.15 per 1M input tokens
# - 1000 queries (~100K tokens) ≈ $0.015
# - Still affordable, but not free

# Savings with OpenRouter: 100% free!

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Q: Model not available error
# A: Check OpenRouter status: https://openrouter.io/docs#models
#    Some models may have limited availability. Use fallback models.

# Q: Slow response
# A: Some models are slower. Try nvidia/nemotron-3-super:free for speed
#    Or switch to openai/gpt-oss-120b:free

# Q: Poor quality answers
# A: Try qwen/qwen3-235b-a22b:free or deepseek/deepseek-r1:free
#    They're excellent but slightly slower

# Q: Rate limited
# A: You've hit free tier limits. Switch to fallback model or wait.
#    Limits reset monthly on OpenRouter free tier.

# ============================================================================
# ADVANCED - Custom Model Selection
# ============================================================================

"""
You can programmatically choose models:

from llm import get_llm_provider

provider = get_llm_provider()

# If using OpenRouter, manually set model:
if isinstance(provider, OpenRouterProvider):
    response = provider.generate_sync(
        messages=[{"role": "user", "content": "Hello"}],
        model="deepseek/deepseek-r1:free",  # Force specific model
        temperature=0.0
    )
"""

# ============================================================================
# SUPPORT & RESOURCES
# ============================================================================

"""
OpenRouter Documentation:
- https://openrouter.io/docs

Free Models:
- https://openrouter.io/docs#models

API Key:
- https://openrouter.io/settings/keys

Status & Updates:
- https://openrouter.io/status

Questions:
- Discord: https://discord.gg/openrouter
- Email: support@openrouter.io
"""
