# Production System Prompts Guide

Complete guide to production-grade system prompts with strict rules for reliable, cited responses without hallucination.

## Overview

The system prompts enforce:
- **Only retrieved context** - No general knowledge
- **Never hallucinate** - No invented facts
- **Always cite** - Every claim has attribution
- **Refuse unsupported** - Transparent about limitations
- **Mention conflicts** - Explicit about contradictions
- **Professional tone** - Represent college well
- **Follow-ups** - Remember conversation context
- **Conversation memory** - Build coherent dialogues

## System Prompts

### 1. Base System Prompt (Default)

The comprehensive system prompt with all 8 critical rules.

```python
from prompts.system_prompts import SystemPrompts

prompt = SystemPrompts.get_system_prompt()
```

**Key sections:**
- CRITICAL RULES (8 non-negotiable rules)
- OPERATIONAL GUIDELINES
- STRICT CONSTRAINTS (what NOT to do)
- Emergency protocols (edge cases)

**Use when:** General Q&A with standard requirements

### 2. Context-Aware Prompt

Simplified prompt focused on using provided context.

```python
prompt = SystemPrompts.get_context_aware_prompt()
```

**Key sections:**
- Core 5 most critical rules
- Response format specification
- Never/Always constraints

**Use when:** Context-filtered searches where context is most relevant

### 3. Conflict Handling Prompt

Specialized prompt for contradictory information.

```python
prompt = SystemPrompts.get_conflict_handling_prompt()
```

**Key sections:**
- Conflict acknowledgment
- Viewpoint presentation
- Verification recommendations

**Use when:** Conflict detected in retrieved context

### 4. Follow-Up Prompt

Optimized for conversational continuity.

```python
prompt = SystemPrompts.get_follow_up_prompt()
```

**Key sections:**
- Conversation reference techniques
- Continuity maintenance
- Follow-up types and handling

**Use when:** Responding to follow-up questions

### 5. Refusal Prompt

Guidance on graceful refusals.

```python
prompt = SystemPrompts.get_refusal_prompt()
```

**Key sections:**
- 5 refusal types with templates
- Alternative suggestions
- Next step guidance

**Use when:** Question cannot be answered from context

## Prompt Templates

Separate templates for formatting structured content.

### User Message Template

```python
from prompts.system_prompts import PromptTemplates

message = PromptTemplates.format_user_question(
    question="What is the admission deadline?",
    context="The deadline is March 31, 2024...",
    sources="[Source: Admissions | https://...]",
)
```

**Format:**
- Question statement
- Retrieved context
- Source citations
- Response instructions

### Follow-Up Template

```python
message = PromptTemplates.format_follow_up(
    conversation_history="Q1: ... A1: ... Q2: ...",
    current_question="Follow-up question",
    context="Retrieved context",
)
```

**Maintains:**
- Previous exchanges
- Topic continuity
- Conversation context

### Citation Template

```python
citation = PromptTemplates.format_citation(
    section_name="Admissions",
    url="https://college.edu/admissions",
)
# Returns: "[Source: Admissions | https://college.edu/admissions]"
```

### Context Template

```python
context = PromptTemplates.format_context(
    source_name="College Website",
    section="Admissions",
    content="Application deadline...",
    timestamp="2024-01-15T10:30:00",
    score=0.92,
)
```

### Answer Template

```python
answer = PromptTemplates.format_answer(
    answer="The deadline is March 31",
    sources=["Admissions Policy", "College Calendar"],
    related_topics=["Application Process", "Requirements"],
)
```

### Refusal Template

```python
refusal = PromptTemplates.format_refusal(
    reason="This question is outside college scope",
    alternatives=[
        "Information about admissions",
        "Course details",
        "Campus facilities",
    ],
    next_steps=[
        "Contact admissions office",
        "Rephrase your question",
    ],
)
```

## Usage

### Basic Setup

```python
from prompts.system_prompts import SystemPrompts
from prompts.prompt_orchestrator import PromptOrchestrator, ResponseHandler

# Create orchestrator
orchestrator = PromptOrchestrator(enable_validation=True)

# Get appropriate system prompt
system_prompt = orchestrator.select_system_prompt("default")

# Build user message with context
user_message = orchestrator.build_user_message(
    question="What is the admission process?",
    retrieved_chunks=[
        {
            "text": "Step 1: Complete application...",
            "source_url": "https://college.edu/admissions",
            "section": "Admissions",
            "similarity_score": 0.95,
        }
    ]
)
```

### Response Generation

```python
# Create response handler
handler = ResponseHandler(enable_validation=True)

# Generate answer
response = handler.generate_answer(
    llm_response="The process includes: [Source: Admissions | https://...]",
    retrieved_chunks=[...],
)

# Response structure:
{
    "type": "answered",
    "response": "The process includes...",
    "sources": ["Admissions Policy"],
    "related_topics": ["Application Requirements"],
    "validation": {
        "has_citations": True,
        "passes_validation": True,
    },
    "success": True,
}
```

### Conversation Management

```python
from prompts.system_prompts import ConversationManager

# Initialize manager
manager = ConversationManager(max_history=10)

# Add exchanges
manager.add_exchange(
    user_question="What is the deadline?",
    assistant_response="The deadline is March 31.",
    context_used=["Admissions Policy"],
)

# Get conversation context
context = manager.get_conversation_context()

# Get related topics from history
topics = manager.get_related_topics()

# Clear when starting new conversation
manager.clear_history()
```

### Response Validation

```python
from prompts.system_prompts import ResponseValidation

# Check for hallucination indicators
indicators = ResponseValidation.check_hallucination_indicators(
    "I believe the deadline is probably around March 31"
)
# Returns: ["Uncertain language: 'I believe'", "Uncertain language: 'probably'"]

# Check for citations
has_citations = ResponseValidation.check_citations(
    "The deadline is March 31 [Source: Admissions]"
)
# Returns: True

# Complete validation
validation = ResponseValidation.validate_response(
    response="The deadline is March 31 [Source: Admissions]",
    context="Deadline: March 31, 2024",
)
# Returns comprehensive validation report
```

## Response Types

### Answered

```python
response = handler.generate_answer(
    llm_response="According to the admissions policy...",
    retrieved_chunks=[...],
)
```

**Characteristics:**
- Type: `answered`
- Includes citations
- Passes validation
- Includes sources and related topics

### Refusal

```python
response = handler.generate_refusal(
    reason="This topic is outside college scope",
    alternatives=["Admissions information", "Academic programs"],
    contact_info="admissions@college.edu",
)
```

**Characteristics:**
- Type: `refusal`
- Explains why refused
- Suggests alternatives
- Provides next steps

**Refusal reasons:**
- Outside scope
- Insufficient context
- Privacy/sensitive
- Not a college FAQ
- Ambiguous/unclear

### Conflict

```python
response = handler.generate_conflict_response(
    info_1="Deadline is March 31",
    citation_1="[Source: Policy A]",
    info_2="Deadline is April 15",
    citation_2="[Source: Policy B]",
    recommendation="Contact admissions office for clarification",
)
```

**Characteristics:**
- Type: `conflict`
- Presents both viewpoints
- Provides sources for each
- Recommends verification

### Clarification Needed

```python
response = handler.generate_clarification_request(
    interpretations=[
        "Are you asking about undergraduate admissions?",
        "Are you asking about graduate programs?",
        "Are you asking about international students?",
    ]
)
```

**Characteristics:**
- Type: `clarification_needed`
- Lists possible interpretations
- Asks for user choice
- Avoids guessing

## Critical Rules

### 1. Answer Only From Context

```python
# ✅ GOOD: Citation with source
"According to the admissions policy [Source: Admissions], 
the deadline is March 31."

# ❌ BAD: General knowledge
"Typically, college deadlines are in the spring."

# ❌ BAD: No source
"The deadline is March 31."
```

### 2. Never Hallucinate

```python
# ✅ GOOD: Exact from context
"The admission requirements include a minimum 3.5 GPA 
[Source: Admissions Requirements | https://...]"

# ❌ BAD: Invented number
"You probably need around a 3.8 GPA"

# ❌ BAD: Uncertain language
"I believe the deadline is probably March 31"
```

### 3. Always Cite

```python
# ✅ GOOD: Every claim cited
"The college offers 50+ undergraduate programs 
[Source: Academic Programs | https://...]
with strong industry connections [Source: Placements | https://...]"

# ❌ BAD: Missing citations
"The college offers 50+ programs with strong placements"

# ❌ BAD: Vague citations
"According to our records, the deadline is March 31"
```

### 4. Refuse Unsupported

```python
# ✅ GOOD: Clear refusal with alternatives
"I don't have information about admissions to other colleges. 
I specialize in [College Name] information. 
I can help you with: admissions requirements, application process, deadlines..."

# ❌ BAD: Guess and provide wrong info
"Most colleges have March deadlines"

# ❌ BAD: Refuse without alternatives
"I can't answer that."
```

### 5. Mention Conflicts

```python
# ✅ GOOD: Explicit conflict statement
"I found conflicting information:
- Document A (updated 2024) states the deadline is March 31 [Source: A]
- Document B (from 2023) states the deadline is April 15 [Source: B]
Please contact admissions office to verify the current deadline."

# ❌ BAD: Hide the conflict
"The deadline is March 31" (but context also has April 15)

# ❌ BAD: Guess which is correct
"The deadline is probably March 31"
```

### 6. Professional Tone

```python
# ✅ GOOD: Formal and helpful
"The college's admission process is comprehensive and considers 
multiple factors [Source: Admissions Process | https://...]"

# ❌ BAD: Casual
"Yeah, they look at a bunch of stuff for admissions..."

# ❌ BAD: Unprofessional language
"Honestly, their requirements are kinda strict"
```

### 7. Follow-Up Support

```python
# First exchange
User: "What is the admission deadline?"
Assistant: "The deadline is March 31 [Source: Admissions]"

# Follow-up (GOOD - remember context)
User: "How long before that should I apply?"
Assistant: "Most students apply 2-3 months before the March 31 deadline 
[Source: Application Timeline]"

# Follow-up (BAD - forget context)
User: "How long before that should I apply?"
Assistant: "When is the deadline?" (should remember March 31)
```

### 8. Conversation Memory

```python
# Track conversation
manager = ConversationManager()

# Exchange 1
manager.add_exchange(
    "What is the deadline?",
    "March 31 [Source: Admissions]",
    ["Admissions Policy"]
)

# Exchange 2 - use context
history = manager.get_conversation_context()
# Can now reference: "As mentioned earlier, the deadline is March 31..."

# Related topics from history
topics = manager.get_related_topics()
# Can suggest: "You might also be interested in application requirements..."
```

## Configuration Examples

### Conservative (High Precision)

```python
from prompts.system_prompts import SystemPrompts
from prompts.prompt_orchestrator import PromptOrchestrator

orchestrator = PromptOrchestrator(enable_validation=True)
```

**Behavior:**
- Strict validation enabled
- All claims verified
- Citations mandatory
- Refuses uncertain questions
- Flags hallucination indicators

### Balanced (Recommended)

```python
orchestrator = PromptOrchestrator(enable_validation=True)
```

**Behavior:**
- Validates responses
- Requires citations
- Flags conflicts
- Maintains professionalism
- Supports follow-ups

### Validation Workflow

```python
# 1. Generate response
response = handler.generate_answer(llm_response, chunks)

# 2. Validate
validation = response.get("validation", {})
if not validation.get("passes_validation"):
    logger.warning("Response validation failed")
    logger.warning(f"Issues: {validation.get('hallucination_indicators')}")

# 3. Adjust if needed
validated_response = handler.validate_and_adjust(response, chunks)
```

## Error Handling

### Missing Citations

```python
if not ResponseValidation.check_citations(response):
    # Regenerate with citations
    logger.warning("Response missing citations, regenerating...")
```

### Hallucination Detection

```python
indicators = ResponseValidation.check_hallucination_indicators(response)
if indicators:
    logger.warning(f"Hallucination indicators: {indicators}")
    # May need to regenerate without uncertain language
```

### Insufficient Context

```python
if not retrieved_chunks:
    response = handler.generate_refusal(
        reason="No relevant information found in knowledge base",
        alternatives=["Try rephrasing your question"],
        contact_info="help@college.edu",
    )
```

## Testing

```bash
# Run prompt tests
pytest tests/test_prompts.py -v

# Specific test
pytest tests/test_prompts.py::TestSystemPrompts -v

# Coverage
pytest tests/test_prompts.py --cov=prompts
```

## Next Steps

1. **Integration with LLM**: Use system prompt with GPT-4o Mini
2. **Retrieval Integration**: Pass retrieved chunks to handler
3. **Conversation Tracking**: Use ConversationManager for multi-turn
4. **Response Validation**: Enable validation for quality assurance
5. **Citation Generation**: Format citations properly for UI display

## Reference

### Files
- `prompts/system_prompts.py`: Core prompts and templates
- `prompts/prompt_orchestrator.py`: Orchestration and response handling
- `tests/test_prompts.py`: Comprehensive tests

### Validation Checklist

Before deploying a response:
- [ ] Has citations for every factual claim
- [ ] No hallucination indicators present
- [ ] No general knowledge (only from context)
- [ ] Professional tone maintained
- [ ] Conversation memory preserved
- [ ] Conflicts explicitly mentioned if present
- [ ] Graceful refusal if unsupported
- [ ] Validation passes (if enabled)
