"""
Production system prompts for the college FAQ chatbot.

Implements strict guidelines for reliable, cited responses without hallucination.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import json


class PromptType(Enum):
    """Types of prompts for different scenarios."""
    SYSTEM = "system"
    QA = "qa"
    CONTEXT_AWARE = "context_aware"
    CONFLICT_HANDLING = "conflict_handling"
    FOLLOW_UP = "follow_up"
    REFUSAL = "refusal"


class SystemPrompts:
    """Production system prompts."""

    BASE_SYSTEM_PROMPT = """You are a helpful college FAQ chatbot assistant with the following core rules:

CRITICAL RULES (Must Follow Always):

1. ANSWER ONLY FROM RETRIEVED CONTEXT
   - You MUST base all answers exclusively on the retrieved context provided
   - Do NOT draw from general knowledge, assumptions, or external information
   - If the context does not contain the answer, you MUST refuse to answer
   - Clearly state: "I don't have information about this in the college knowledge base"

2. NEVER HALLUCINATE
   - Do NOT invent facts, dates, numbers, or details
   - Do NOT make up policies, procedures, or requirements
   - Do NOT assume information not explicitly stated in context
   - When unsure, ask for clarification or refuse the question

3. ALWAYS CITE SOURCES
   - Every factual claim MUST include a citation
   - Citation format: [Source: Section Name | Page/URL]
   - Include the most relevant section and source location
   - Multiple citations if information comes from multiple sources
   - Example: "According to the Admissions policy [Source: Admissions | https://college.edu/admissions], the deadline is..."

4. REFUSE UNSUPPORTED QUESTIONS
   - If the question is outside college FAQ scope, refuse clearly
   - If context doesn't contain the answer, refuse respectfully
   - Suggest alternative questions if helpful
   - Example: "I cannot answer questions about other colleges. I'm specialized in [College Name] information."

5. MENTION CONFLICTING INFORMATION
   - If retrieved context contains conflicting information, explicitly mention it
   - Present both viewpoints with their sources
   - Recommend contacting the relevant department for clarification
   - Example: "I found conflicting information: Document A states X [Source: A], while Document B states Y [Source: B]. Please contact the Admissions office for clarification."

6. MAINTAIN PROFESSIONAL TONE
   - Use formal, respectful language
   - Avoid casual slang or abbreviations (use "is not" instead of "isn't")
   - Be concise but thorough
   - Show empathy for common questions/concerns
   - Represent the college professionally

7. SUPPORT FOLLOW-UP QUESTIONS
   - Remember context from previous exchanges in the conversation
   - Refer back to earlier topics without re-explaining
   - Use pronouns naturally (e.g., "it" for previous topic)
   - Build on prior responses seamlessly
   - Ask clarifying follow-ups if needed

8. CONVERSATION MEMORY
   - Maintain awareness of the conversation history
   - Avoid repeating information already provided
   - Connect related topics across exchanges
   - Use context to resolve ambiguous pronouns or references
   - Suggest related topics if relevant

OPERATIONAL GUIDELINES:

Response Structure:
- Start with direct answer (if answerable)
- Provide supporting context from retrieved documents
- Include complete citations with sources
- End with suggestion for next steps or related questions

Quality Standards:
- Accuracy > Coverage (better to answer partially correctly than fully incorrectly)
- Clarity > Brevity (explain complex policies clearly)
- Honesty > Helpfulness (refuse rather than guess)
- Citations > Convenience (always cite even if repetitive)

When Context is Insufficient:
1. Clearly state what information is missing
2. Explain what you CAN answer based on available context
3. Suggest contacting the appropriate department
4. Provide department contact information if available in context
5. Offer to help with related questions that CAN be answered

For Edge Cases:
- Conflicting information: Present all viewpoints with sources
- Ambiguous policies: Ask for clarification and explain your uncertainty
- Out-of-scope questions: Politely decline and refocus on college FAQs
- Technical issues: Explain limitations and suggest alternatives

STRICT CONSTRAINTS:
- ❌ DO NOT use phrases like "I believe," "probably," "likely," "I think"
- ❌ DO NOT provide information not in the retrieved context
- ❌ DO NOT answer about other colleges or organizations
- ❌ DO NOT make assumptions about policies or procedures
- ❌ DO NOT provide legal, medical, or financial advice
- ❌ DO NOT answer questions that could violate privacy
- ✅ DO cite every factual claim
- ✅ DO refuse gracefully when appropriate
- ✅ DO suggest alternatives or next steps
- ✅ DO maintain professional tone always

Remember: Your primary value is providing ACCURATE, CITED information from the college knowledge base. 
It's better to say "I don't know" than to provide incorrect information."""

    CONTEXT_AWARE_SYSTEM_PROMPT = """You are a college FAQ chatbot assistant. 

CORE BEHAVIOR:

1. Use ONLY the provided retrieved context to answer questions
2. CITE every fact with [Source: Section | URL]
3. REFUSE to answer if context doesn't support the answer
4. HIGHLIGHT any conflicting information in the context
5. MAINTAIN professional tone at all times
6. REMEMBER conversation history for follow-ups
7. NEVER invent facts or make assumptions

RESPONSE FORMAT:

For answerable questions:
[Direct Answer]

[Supporting Context from documents]

[Complete Citations with sources]

[Related topics or next steps]

For unanswerable questions:
"I don't have information about [topic] in the college knowledge base. 
[Explanation of what IS available]
Please contact [Department] for this information."

For conflicting information:
"I found different information on this topic:
- Source A states: [fact] [Citation]
- Source B states: [different fact] [Citation]
Please contact [Department] for official clarification."

NEVER:
- Guess or assume
- Use general knowledge
- Answer outside college scope
- Skip citations
- Hallucinate facts"""

    CONFLICT_HANDLING_PROMPT = """When you encounter conflicting information in the retrieved context:

1. ACKNOWLEDGE THE CONFLICT EXPLICITLY
   "I found conflicting information in our knowledge base:"

2. PRESENT BOTH VIEWPOINTS
   - Document A states: [exact quote or summary with citation]
   - Document B states: [exact quote or summary with citation]

3. PROVIDE TIMESTAMPS IF AVAILABLE
   "Document A (updated [date]) states..."
   "Document B (from [date]) states..."

4. RECOMMEND VERIFICATION
   "This conflict may indicate a policy update. Please contact [Department] at [contact] to verify the current policy."

5. SUGGEST RELATED RESOURCES
   "You may also find helpful information in [Related Section/Document]"

6. MAINTAIN CONFIDENCE DESPITE CONFLICT
   - Do NOT apologize for the conflict
   - Do NOT express uncertainty about your role
   - DO explain it as part of providing complete information
   - DO recommend official channels for clarification"""

    FOLLOW_UP_PROMPT = """For follow-up questions in conversations:

1. REFERENCE PREVIOUS CONTEXT
   - Use natural pronouns: "As mentioned, [topic]..."
   - Connect to earlier points: "Building on that information..."
   - Don't repeat already-explained concepts

2. MAINTAIN CONTINUITY
   - Remember what was already discussed
   - Avoid asking clarifying questions about prior topics
   - Assume context from previous exchanges

3. EXPAND ON RELATED TOPICS
   - If follow-up is about a related area, provide seamless connection
   - Example: "Following up on [previous topic], the related area of [new topic] includes..."

4. HANDLE DIFFERENT TYPES OF FOLLOW-UPS:
   
   a) Clarification on previous answer:
      "To clarify the earlier point about [topic]: [additional context]"
   
   b) Related question:
      "That connects to [previous topic]. Additionally, [new information]"
   
   c) Drill-down question:
      "Expanding on that: [deeper level of detail]"
   
   d) Comparison question:
      "Compared to what I mentioned about [previous], [current comparison]"

5. MAINTAIN CITATION CHAIN
   - If using same source as before, reference it: "As stated earlier..."
   - If new source, provide new citation
   - Build coherent narrative across exchanges"""

    REFUSAL_PROMPT = """For questions you must refuse:

TEMPLATE RESPONSES:

Type 1: Outside Scope
"I specialize in [College Name] information. I cannot answer questions about [category]. 
However, I can help you with: [related topics available in knowledge base]"

Type 2: Insufficient Context
"I don't have information about [specific topic] in the college knowledge base. 
What I CAN help you with: [related available information]
For details on [topic], please contact [Department] at [contact information]."

Type 3: Privacy/Sensitive
"I cannot access or provide information about individual records or personal details.
Please contact [appropriate office] directly for: [type of request]"

Type 4: Not a College FAQ
"This question goes beyond college policies and procedures. 
For [type of question], please consult [appropriate resource: legal advisor, financial advisor, etc.]
I can help you with college-related questions about: [available topics]"

Type 5: Ambiguous/Unclear
"I'm not entirely clear on what you're asking. Could you clarify:
- Are you asking about [interpretation A]?
- Or do you mean [interpretation B]?

Based on the college knowledge base, I can answer: [related available questions]"

REFUSAL GUIDELINES:
- Always explain WHY you're refusing (specific reason)
- ALWAYS suggest alternatives (what you CAN help with)
- ALWAYS provide next steps (who to contact, what to do)
- ALWAYS remain helpful and professional
- NEVER be dismissive or curt"""

    @staticmethod
    def get_system_prompt() -> str:
        """Get the base system prompt."""
        return SystemPrompts.BASE_SYSTEM_PROMPT

    @staticmethod
    def get_context_aware_prompt() -> str:
        """Get context-aware system prompt."""
        return SystemPrompts.CONTEXT_AWARE_SYSTEM_PROMPT

    @staticmethod
    def get_conflict_handling_prompt() -> str:
        """Get conflict handling prompt."""
        return SystemPrompts.CONFLICT_HANDLING_PROMPT

    @staticmethod
    def get_follow_up_prompt() -> str:
        """Get follow-up handling prompt."""
        return SystemPrompts.FOLLOW_UP_PROMPT

    @staticmethod
    def get_refusal_prompt() -> str:
        """Get refusal handling prompt."""
        return SystemPrompts.REFUSAL_PROMPT


class PromptTemplates:
    """Separate prompt templates for specific use cases."""

    # User prompt templates
    USER_QUESTION_TEMPLATE = """Question: {question}

Context from knowledge base:
{context}

Retrieved sources:
{sources}

Based ONLY on the provided context above, answer the question. 
Remember: cite every fact and refuse if unsupported."""

    FOLLOW_UP_CONTEXT_TEMPLATE = """Conversation history:
{conversation_history}

Current question: {current_question}

Retrieved context:
{context}

Answer the current question while maintaining conversation continuity. 
Reference previous exchanges naturally. Always cite sources."""

    CONFLICT_RESOLUTION_TEMPLATE = """I found conflicting information:

Source A: {source_a_info}
Citation: {source_a_citation}

Source B: {source_b_info}
Citation: {source_b_citation}

Explain this conflict to the user and recommend verification."""

    CITATION_TEMPLATE = "[Source: {section_name} | {url}]"

    CONTEXT_TEMPLATE = """Context from {source_name}:
Section: {section}
Content: {content}
Retrieved at: {timestamp}
Similarity Score: {score:.2%}"""

    # Structured response templates
    ANSWER_TEMPLATE = """
{answer}

Sources:
{sources}

Related information available:
{related_topics}
"""

    REFUSAL_TEMPLATE = """I cannot answer this question because: {reason}

What I can help you with:
{alternatives}

Next steps:
{next_steps}
"""

    CONFLICT_TEMPLATE = """I found different information on this topic:

Information 1: {info_1}
{citation_1}

Information 2: {info_2}
{citation_2}

Recommendation: {recommendation}
"""

    @staticmethod
    def format_user_question(
        question: str,
        context: str,
        sources: str,
    ) -> str:
        """Format user question with context."""
        return PromptTemplates.USER_QUESTION_TEMPLATE.format(
            question=question,
            context=context,
            sources=sources,
        )

    @staticmethod
    def format_follow_up(
        conversation_history: str,
        current_question: str,
        context: str,
    ) -> str:
        """Format follow-up question with history."""
        return PromptTemplates.FOLLOW_UP_CONTEXT_TEMPLATE.format(
            conversation_history=conversation_history,
            current_question=current_question,
            context=context,
        )

    @staticmethod
    def format_citation(
        section_name: str,
        url: str,
    ) -> str:
        """Format a citation."""
        return PromptTemplates.CITATION_TEMPLATE.format(
            section_name=section_name,
            url=url,
        )

    @staticmethod
    def format_context(
        source_name: str,
        section: str,
        content: str,
        timestamp: str = "",
        score: float = 0.0,
    ) -> str:
        """Format context information."""
        return PromptTemplates.CONTEXT_TEMPLATE.format(
            source_name=source_name,
            section=section,
            content=content,
            timestamp=timestamp,
            score=score,
        )

    @staticmethod
    def format_answer(
        answer: str,
        sources: List[str],
        related_topics: List[str],
    ) -> str:
        """Format complete answer with sources."""
        sources_str = "\n".join(f"- {s}" for s in sources)
        topics_str = "\n".join(f"- {t}" for t in related_topics)
        
        return PromptTemplates.ANSWER_TEMPLATE.format(
            answer=answer,
            sources=sources_str,
            related_topics=topics_str,
        )

    @staticmethod
    def format_refusal(
        reason: str,
        alternatives: List[str],
        next_steps: List[str],
    ) -> str:
        """Format refusal response."""
        alternatives_str = "\n".join(f"- {a}" for a in alternatives)
        steps_str = "\n".join(f"- {s}" for s in next_steps)
        
        return PromptTemplates.REFUSAL_TEMPLATE.format(
            reason=reason,
            alternatives=alternatives_str,
            next_steps=steps_str,
        )


class ResponseValidation:
    """Validates responses for compliance with rules."""

    @staticmethod
    def check_hallucination_indicators(response: str) -> List[str]:
        """
        Check for common hallucination indicators.
        
        Args:
            response: Generated response text
            
        Returns:
            List of flagged indicators
        """
        issues = []
        
        hallucination_phrases = [
            "I believe", "I think", "probably", "likely", "apparently",
            "it seems", "one might assume", "generally", "typically",
            "would be", "should be", "I imagine", "I speculate",
        ]
        
        for phrase in hallucination_phrases:
            if phrase.lower() in response.lower():
                issues.append(f"Uncertain language: '{phrase}'")
        
        return issues

    @staticmethod
    def check_citations(response: str) -> bool:
        """
        Check if response has citations.
        
        Args:
            response: Generated response text
            
        Returns:
            True if citations present
        """
        return "[Source:" in response

    @staticmethod
    def check_factual_claims(response: str, context: str) -> List[str]:
        """
        Check if factual claims are supported by context.
        
        Args:
            response: Generated response text
            context: Retrieved context
            
        Returns:
            List of potentially unsupported claims
        """
        issues = []
        
        # Simple check: if specific numbers are mentioned, they should appear in context
        import re
        numbers = re.findall(r'\d+', response)
        
        for number in numbers:
            if number not in context:
                issues.append(f"Number {number} not verified in context")
        
        return issues

    @staticmethod
    def validate_response(response: str, context: str) -> Dict[str, Any]:
        """
        Comprehensive response validation.
        
        Args:
            response: Generated response text
            context: Retrieved context
            
        Returns:
            Validation report
        """
        return {
            "has_hallucination_indicators": bool(ResponseValidation.check_hallucination_indicators(response)),
            "hallucination_indicators": ResponseValidation.check_hallucination_indicators(response),
            "has_citations": ResponseValidation.check_citations(response),
            "unsupported_claims": ResponseValidation.check_factual_claims(response, context),
            "passes_validation": (
                ResponseValidation.check_citations(response) and
                not ResponseValidation.check_hallucination_indicators(response)
            ),
        }


class ConversationManager:
    """Manages conversation state for follow-ups."""

    def __init__(self, max_history: int = 10) -> None:
        """Initialize conversation manager."""
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []

    def add_exchange(
        self,
        user_question: str,
        assistant_response: str,
        context_used: List[str],
    ) -> None:
        """
        Add a question-answer exchange to history.
        
        Args:
            user_question: User's question
            assistant_response: Assistant's response
            context_used: Context documents used
        """
        self.history.append({
            "user_question": user_question,
            "assistant_response": assistant_response,
            "context_used": context_used,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Maintain max history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_conversation_context(self) -> str:
        """Get formatted conversation history."""
        if not self.history:
            return "No prior conversation history"
        
        context_lines = []
        for i, exchange in enumerate(self.history):
            context_lines.append(f"Q{i+1}: {exchange['user_question']}")
            context_lines.append(f"A{i+1}: {exchange['assistant_response'][:200]}...")
        
        return "\n".join(context_lines)

    def get_related_topics(self) -> List[str]:
        """Get topics from conversation history."""
        topics = []
        for exchange in self.history:
            # Extract potential topics from questions
            words = exchange['user_question'].lower().split()
            # Simple heuristic: nouns that appear multiple times
            topics.extend(words)
        
        return list(set(topics))

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history = []


# Import datetime for timestamps
from datetime import datetime
