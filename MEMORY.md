# Conversation Memory System Guide

Complete guide to the advanced conversation memory system with multi-turn support, context awareness, and intelligent token management.

## Overview

The memory system provides:
- **Multi-turn conversations** - Context-aware responses across exchanges
- **Context awareness** - Track departments, sections, topics
- **Pronoun resolution** - "it", "that", "they" → original references
- **Automatic summarization** - Compress history when exceeding token limits
- **Session management** - Create, track, import/export sessions
- **Token management** - Prevent unbounded growth

## Quick Start

```python
from memory.conversation_memory import ConversationMemory, MessageRole

# Create memory
memory = ConversationMemory(max_context_tokens=2000)

# Add messages
memory.add_message(MessageRole.USER, "What is the CS program about?")
memory.add_message(MessageRole.ASSISTANT, "The CS program covers...")

# Get context for LLM
context = memory.get_context_window(k=5)  # Last 5 messages

# Add follow-up
memory.add_message(MessageRole.USER, "What about placements in it?")
# System remembers "it" = CS program

# Get stats
stats = memory.get_session_stats()
print(f"Messages: {stats['total_messages']}")
print(f"Tokens: {stats['total_tokens']}")
```

## Components

### ConversationMessage

Single message with metadata.

```python
msg = ConversationMessage(
    role=MessageRole.ASSISTANT,
    content="The deadline is March 31",
    metadata={"sources": ["Admissions"]},
)

# Properties
msg.role              # MessageRole.ASSISTANT
msg.content           # "The deadline is March 31"
msg.tokens            # Estimated tokens
msg.timestamp         # ISO timestamp
msg.metadata          # Custom metadata
```

### ContextTracker

Tracks conversation context for awareness.

```python
tracker = ContextTracker()

# Extract entities from text
tracker.extract_entities("Tell me about CS admissions")

# Now tracks:
tracker.department_context    # "cs"
tracker.section_context       # "admissions"
tracker.current_topics        # ["cs", "admissions"]

# Resolve pronouns
tracker.mentioned_entities["it"] = "the deadline"
tracker.resolve_pronoun("it")  # "the deadline"

# Get context summary
summary = tracker.get_context_summary()
# "Current department: cs\nCurrent section: admissions"
```

### TokenManager

Prevents unbounded token growth.

```python
manager = TokenManager(
    max_context_tokens=2000,
    summary_threshold=1800,
    preserve_recent=3,
)

# Check if should summarize
if manager.should_summarize(current_tokens):
    # Compress history
    pass

# Get compression needed
ratio = manager.calculate_compression_needed(2500)
# 0.8 = compress to 80%

# Track total tokens
manager.add_tokens(100)
total = manager.get_total_tokens()  # 100
```

### ConversationSummarizer

Summarizes messages to save tokens.

```python
summary = ConversationSummarizer.create_summary(messages)
# "Questions asked: What is...?\nTopics: admissions, cs\nKey points: ..."
```

### ConversationMemory

Main memory class for single conversation.

```python
memory = ConversationMemory(
    max_messages=20,
    max_context_tokens=2000,
    enable_summarization=True,
    session_id="session_abc123",
)

# Add messages
memory.add_message(MessageRole.USER, "Hello")
memory.add_message(MessageRole.ASSISTANT, "Hi there")

# Get recent context (for LLM)
context = memory.get_context_window(k=5)
# Returns: [{"role": "user", "content": "..."}, ...]

# If summary exists, includes it in context

# Get full history
history = memory.get_conversation_history()
# Returns: [{"role": "...", "content": "...", "timestamp": "..."}, ...]

# Context awareness
context_summary = memory.get_context_summary()
# "Current department: cs"

departments = memory.get_mentioned_departments()
# ["Computer Science", "Electronics"]

# Session stats
stats = memory.get_session_stats()
# {
#   "session_id": "...",
#   "total_messages": 10,
#   "total_tokens": 450,
#   "has_summary": False,
#   "mentioned_departments": ["CS"]
# }

# Manage session
memory.clear_history()
memory.export_session("session.json")
memory.import_session("session.json")
```

### MemoryManager

Manages multiple conversation sessions.

```python
manager = MemoryManager(max_sessions=10)

# Create session
session_id = manager.create_session()
# Returns: "a1b2c3d4"

# Add to session
manager.add_message(
    MessageRole.USER,
    "Hello",
    session_id=session_id,
)

# Get context window
context = manager.get_context_window(k=5, session_id=session_id)

# List all sessions
sessions = manager.list_sessions()
# [{
#   "session_id": "a1b2c3d4",
#   "stats": {"total_messages": 5, ...}
# }]

# Get/delete session
session = manager.get_session(session_id)
manager.delete_session(session_id)
```

## Features

### Multi-Turn Conversations

Each message is tracked with full history:

```python
# Turn 1
memory.add_message(MessageRole.USER, "What is the CS program?")
memory.add_message(MessageRole.ASSISTANT, "CS program covers...")

# Turn 2 - System has full context
memory.add_message(MessageRole.USER, "What are the placements?")

# Context window includes:
# - Previous Q&A about CS
# - Department context (CS)
# - Current topic (placements)
```

### Context Awareness

Tracks departments and sections:

```python
memory.add_message(MessageRole.USER, "Tell me about Electronics admissions")

context = memory.get_context_summary()
# Output:
# "Current department: electronics"
# "Current section: admissions"
# "Topics discussed: electronics, admissions"
```

### Pronoun Resolution

Resolves pronouns to original references:

```python
# User: "The CS program is rigorous. What about it?"
# System detects: "it" → "the CS program"
# Response can reference "it" naturally

memory.add_message(MessageRole.USER, "What about the placements?")
# System knows "placements" refers to CS program's placements
```

### Automatic Summarization

Compresses history when exceeding token limits:

```python
memory = ConversationMemory(max_context_tokens=2000)

# Add 50 messages
for i in range(50):
    memory.add_message(MessageRole.USER, f"Message {i}")

# Internally:
# - Summarizes old messages
# - Keeps recent messages
# - Prevents token explosion
# - Preserves context
```

### Token Management

Prevents unbounded growth:

```python
# Configuration
memory = ConversationMemory(
    max_context_tokens=2000,      # Max tokens in context
    enable_summarization=True,     # Auto-summarize
)

# When adding messages:
# 1. Check current tokens
# 2. If > summary_threshold (1800), compress
# 3. If > max_messages (20), trim
# 4. Keep recent messages + summary

# Access tokens
stats = memory.get_session_stats()
print(f"Total tokens: {stats['total_tokens']}")
```

## Usage Patterns

### Pattern 1: Basic Chat

```python
from memory.conversation_memory import ConversationMemory, MessageRole

memory = ConversationMemory()

# Add user query
memory.add_message(MessageRole.USER, "What is the deadline?")

# Get context for LLM
context_messages = memory.get_context_window(k=5)

# Call LLM with context_messages
# response = llm.chat(context_messages)

# Add response
memory.add_message(MessageRole.ASSISTANT, response)
```

### Pattern 2: Multi-Turn with Awareness

```python
# Turn 1
memory.add_message(MessageRole.USER, "Tell me about CS program")
memory.add_message(MessageRole.ASSISTANT, "The CS program...")

# Turn 2 - Uses context
memory.add_message(MessageRole.USER, "What's the placement rate?")

# Context includes:
# - Previous messages about CS
# - Department: CS
# - Topics: program, placements

context = memory.get_context_window()
# LLM knows "placement rate" = CS placement rate
```

### Pattern 3: Session Management

```python
from memory.conversation_memory import MemoryManager

manager = MemoryManager(max_sessions=10)

# Create session
session_id = manager.create_session()

# Chat
manager.add_message(MessageRole.USER, "Hello", session_id=session_id)
context = manager.get_context_window(session_id=session_id)

# Save session
session = manager.get_session(session_id)
session.export_session("user_session.json")

# Later: Load session
new_session = ConversationMemory()
new_session.import_session("user_session.json")
```

### Pattern 4: Token Optimization

```python
memory = ConversationMemory(
    max_messages=20,              # Keep 20 recent messages
    max_context_tokens=2000,      # Max 2000 tokens in context
    enable_summarization=True,    # Auto-summarize older messages
)

# Add 100 messages over time
for i in range(100):
    memory.add_message(MessageRole.USER, message)

# Result:
# - First 80 messages → summarized
# - Last 20 messages → kept in full
# - Context: summary + recent messages
# - Total tokens: < 2000
```

## API Reference

### ConversationMemory

```python
class ConversationMemory:
    def add_message(role, content, metadata=None)
    def get_context_window(k=5) -> List[Dict]
    def get_conversation_history() -> List[Dict]
    def get_context_summary() -> str
    def resolve_reference(pronoun) -> str
    def get_mentioned_departments() -> List[str]
    def get_session_stats() -> Dict
    def clear_history()
    def export_session(filepath)
    def import_session(filepath)
```

### MemoryManager

```python
class MemoryManager:
    def create_session() -> str
    def get_session(session_id=None) -> ConversationMemory
    def add_message(role, content, session_id=None, metadata=None)
    def get_context_window(k=5, session_id=None) -> List[Dict]
    def list_sessions() -> List[Dict]
    def delete_session(session_id) -> bool
```

## Performance

### Token Usage

- **Per message**: ~4 tokens per character (estimate)
- **Full context**: Last k messages + summary
- **Auto-summarization**: Triggered at 90% of max_context_tokens
- **Message limit**: Keeps recent messages only

### Memory Usage

- **Per session**: ~1KB per message (metadata + content)
- **Multiple sessions**: Configurable (default: 10 max)
- **Summary**: Stored compressed in memory

## Testing

```bash
# Run memory tests
pytest tests/test_memory.py -v

# Specific test
pytest tests/test_memory.py::TestConversationMemory -v

# With coverage
pytest tests/test_memory.py --cov=memory
```

## Examples

### Example 1: Multi-Turn Conversation

```python
memory = ConversationMemory()

# Turn 1
memory.add_message(MessageRole.USER, "I'm interested in CS")
memory.add_message(MessageRole.ASSISTANT, "The CS program is excellent...")

# Turn 2
memory.add_message(MessageRole.USER, "What about placements?")
context = memory.get_context_window()
# Context includes awareness of CS interest

# Turn 3
memory.add_message(MessageRole.USER, "Tell me more about it")
# "it" = CS program + placements context
```

### Example 2: Department Filtering

```python
memory = ConversationMemory()

messages = [
    "Tell me about CS and Electronics programs",
    "What are CS placements?",
    "Compare CS and Electronics",
]

for msg in messages:
    memory.add_message(MessageRole.USER, msg)

depts = memory.get_mentioned_departments()
# ["Computer Science", "Electronics"]
```

### Example 3: Token Management

```python
memory = ConversationMemory(max_context_tokens=500)

# Add many messages
for i in range(100):
    memory.add_message(MessageRole.USER, f"Message {i}")

# Inspect memory
stats = memory.get_session_stats()
print(f"Messages kept: {stats['total_messages']}")  # ~20
print(f"Has summary: {stats['has_summary']}")       # True
print(f"Total tokens: {stats['total_tokens']}")     # Controlled
```

## Integration

### With Chatbot

```python
from memory.conversation_memory import ConversationMemory, MessageRole

memory = ConversationMemory()

async def chat(query):
    # Add user query
    memory.add_message(MessageRole.USER, query)
    
    # Get context window
    context_messages = memory.get_context_window(k=5)
    
    # Call chatbot with context
    response = await chatbot.chat(query)
    
    # Add response
    memory.add_message(MessageRole.ASSISTANT, response["response"])
    
    return response
```

### With Dashboard

```python
# In Streamlit app
stats = memory.get_session_stats()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Messages", stats['total_messages'])
with col2:
    st.metric("Tokens", stats['total_tokens'])
with col3:
    st.metric("Departments", len(stats['mentioned_departments']))

st.write("Context:", stats['context'])
```

## Next Steps

- Integrate with chatbot for automatic context
- Persist sessions to database
- Implement pronoun resolution with NER
- Add semantic similarity for reference resolution
- Export conversation analytics
