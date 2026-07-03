"""
Advanced conversation memory system with context awareness and token management.

Supports multi-turn conversations, pronoun resolution, summarization, and context compression.
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import hashlib
from datetime import datetime
from collections import defaultdict
from enum import Enum

from core.logger import get_logger

logger = get_logger(__name__)


class MessageRole(Enum):
    """Message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage:
    """Single conversation message with metadata."""

    def __init__(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize message."""
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.tokens = self._estimate_tokens(content)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens in text (~4 chars per token)."""
        return max(1, len(text) // 4)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "tokens": self.tokens,
        }


class ContextTracker:
    """Tracks conversation context for pronoun and reference resolution."""

    def __init__(self) -> None:
        """Initialize context tracker."""
        self.mentioned_entities: Dict[str, str] = {}  # pronoun -> entity
        self.current_topics: List[str] = []
        self.department_context: Optional[str] = None
        self.section_context: Optional[str] = None
        self.named_references: Dict[str, str] = {}  # name -> full reference

    def extract_entities(self, text: str) -> None:
        """Extract entities from text."""
        # Simple extraction - in production, use NER
        pronouns = ["it", "this", "that", "these", "those", "he", "she", "they"]
        departments = ["cs", "electronics", "mechanical", "civil", "cse", "ece"]
        sections = ["admissions", "academics", "placements", "campus", "student life"]

        text_lower = text.lower()

        for dept in departments:
            if dept in text_lower:
                self.department_context = dept
                self.named_references[dept] = f"Department of {dept.upper()}"

        for section in sections:
            if section in text_lower:
                self.section_context = section
                self.current_topics.append(section)

    def resolve_pronoun(self, pronoun: str) -> Optional[str]:
        """Resolve pronoun to entity."""
        return self.mentioned_entities.get(pronoun.lower())

    def update_context(self, message: str) -> None:
        """Update context from message."""
        self.extract_entities(message)

    def get_context_summary(self) -> str:
        """Get context summary for prompt."""
        context = []

        if self.department_context:
            context.append(f"Current department: {self.department_context}")

        if self.section_context:
            context.append(f"Current section: {self.section_context}")

        if self.current_topics:
            context.append(f"Topics discussed: {', '.join(set(self.current_topics[-3:]))}")

        return "\n".join(context)


class TokenManager:
    """Manages token usage to prevent excessive growth."""

    def __init__(
        self,
        max_context_tokens: int = 2000,
        summary_threshold: int = 1800,
        preserve_recent: int = 3,
    ) -> None:
        """
        Initialize token manager.

        Args:
            max_context_tokens: Maximum tokens in context
            summary_threshold: Summarize when exceeding this
            preserve_recent: Keep last N messages before summarizing
        """
        self.max_context_tokens = max_context_tokens
        self.summary_threshold = summary_threshold
        self.preserve_recent = preserve_recent
        self.total_tokens = 0

    def should_summarize(self, current_tokens: int) -> bool:
        """Check if should summarize to save tokens."""
        return current_tokens > self.summary_threshold

    def calculate_compression_needed(self, current_tokens: int) -> float:
        """Calculate how much to compress."""
        if current_tokens <= self.max_context_tokens:
            return 1.0

        return self.max_context_tokens / current_tokens

    def add_tokens(self, tokens: int) -> None:
        """Add tokens to counter."""
        self.total_tokens += tokens

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return self.total_tokens


class ConversationSummarizer:
    """Summarizes conversation history to save tokens."""

    @staticmethod
    def create_summary(messages: List[ConversationMessage]) -> str:
        """
        Create summary of messages.

        Args:
            messages: Messages to summarize

        Returns:
            Summary string
        """
        if not messages:
            return ""

        # Extract key information
        topics = []
        questions = []
        answers = []

        for msg in messages:
            if msg.role == MessageRole.USER:
                if "?" in msg.content:
                    questions.append(msg.content[:100])
                topics.append(msg.content[:50])
            elif msg.role == MessageRole.ASSISTANT:
                answers.append(msg.content[:100])

        summary_parts = []

        if questions:
            summary_parts.append(f"Questions asked: {'; '.join(set(questions[:3]))}")

        if topics:
            summary_parts.append(f"Topics: {', '.join(set(topics[:5]))}")

        if answers:
            summary_parts.append(f"Key points covered: {'; '.join(set(answers[:3]))}")

        return "\n".join(summary_parts)


class ConversationMemory:
    """Advanced conversation memory with multi-turn, context, and token management."""

    def __init__(
        self,
        max_messages: int = 20,
        max_context_tokens: int = 2000,
        enable_summarization: bool = True,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Initialize conversation memory.

        Args:
            max_messages: Maximum messages to keep
            max_context_tokens: Maximum tokens in context
            enable_summarization: Enable auto-summarization
            session_id: Session identifier
        """
        self.max_messages = max_messages
        self.enable_summarization = enable_summarization
        self.session_id = session_id or self._generate_session_id()

        self.messages: List[ConversationMessage] = []
        self.summary: Optional[str] = None
        self.context_tracker = ContextTracker()
        self.token_manager = TokenManager(max_context_tokens)

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add message to memory.

        Args:
            role: Message role
            content: Message content
            metadata: Optional metadata
        """
        msg = ConversationMessage(role, content, metadata)
        self.messages.append(msg)
        self.token_manager.add_tokens(msg.tokens)

        # Update context
        if role == MessageRole.USER:
            self.context_tracker.update_context(content)

        # Check if should summarize
        if self._should_compress():
            self._compress_history()

        # Trim if too many messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        logger.debug(f"Added message: {role.value} ({msg.tokens} tokens)")

    def _should_compress(self) -> bool:
        """Check if should compress history."""
        if not self.enable_summarization:
            return False

        current_tokens = sum(m.tokens for m in self.messages)
        return self.token_manager.should_summarize(current_tokens)

    def _compress_history(self) -> None:
        """Compress history by summarizing older messages."""
        if len(self.messages) <= self.token_manager.preserve_recent:
            return

        # Preserve recent messages
        recent = self.messages[-self.token_manager.preserve_recent :]
        older = self.messages[: -self.token_manager.preserve_recent]

        # Summarize older
        new_summary = ConversationSummarizer.create_summary(older)

        if self.summary:
            self.summary += "\n" + new_summary
        else:
            self.summary = new_summary

        # Keep recent messages
        self.messages = recent

        logger.info(f"Compressed history. Summary: {len(self.summary)} chars")

    def get_context_window(self, k: int = 5) -> List[Dict[str, str]]:
        """
        Get recent context window for LLM.

        Args:
            k: Number of recent messages to include

        Returns:
            List of messages for LLM
        """
        recent_messages = self.messages[-k:] if len(self.messages) > k else self.messages

        context = []

        # Add summary if exists
        if self.summary:
            context.append({
                "role": "system",
                "content": f"Previous conversation summary:\n{self.summary}",
            })

        # Add recent messages
        for msg in recent_messages:
            context.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        return context

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history."""
        return [msg.to_dict() for msg in self.messages]

    def get_context_summary(self) -> str:
        """Get context summary for awareness."""
        return self.context_tracker.get_context_summary()

    def resolve_reference(self, pronoun: str) -> Optional[str]:
        """Resolve pronoun or reference."""
        return self.context_tracker.resolve_pronoun(pronoun)

    def get_mentioned_departments(self) -> List[str]:
        """Get all mentioned departments."""
        departments = set()
        for msg in self.messages:
            if msg.role == MessageRole.USER:
                text_lower = msg.content.lower()
                if "cs" in text_lower or "computer" in text_lower:
                    departments.add("Computer Science")
                if "electronics" in text_lower or "ece" in text_lower:
                    departments.add("Electronics")
                if "mechanical" in text_lower:
                    departments.add("Mechanical")
                if "civil" in text_lower:
                    departments.add("Civil")

        return list(departments)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            "session_id": self.session_id,
            "total_messages": len(self.messages),
            "total_tokens": self.token_manager.get_total_tokens(),
            "avg_message_length": (
                sum(len(m.content) for m in self.messages) // max(len(self.messages), 1)
            ),
            "has_summary": self.summary is not None,
            "context": self.get_context_summary(),
            "mentioned_departments": self.get_mentioned_departments(),
        }

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
        self.summary = None
        self.context_tracker = ContextTracker()
        logger.info(f"Cleared history for session {self.session_id}")

    def export_session(self, filepath: str) -> None:
        """Export session to file."""
        try:
            data = {
                "session_id": self.session_id,
                "created_at": datetime.utcnow().isoformat(),
                "messages": self.get_conversation_history(),
                "summary": self.summary,
                "stats": self.get_session_stats(),
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Exported session to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting session: {e}")

    def import_session(self, filepath: str) -> None:
        """Import session from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.session_id = data.get("session_id", self.session_id)
            self.summary = data.get("summary")

            for msg_data in data.get("messages", []):
                role = MessageRole[msg_data["role"].upper()]
                self.add_message(
                    role=role,
                    content=msg_data["content"],
                    metadata=msg_data.get("metadata"),
                )

            logger.info(f"Imported session from {filepath}")
        except Exception as e:
            logger.error(f"Error importing session: {e}")


class MemoryManager:
    """Manages multiple conversation sessions."""

    def __init__(self, max_sessions: int = 10) -> None:
        """Initialize memory manager."""
        self.max_sessions = max_sessions
        self.sessions: Dict[str, ConversationMemory] = {}
        self.current_session_id: Optional[str] = None

    def create_session(self) -> str:
        """Create new conversation session."""
        memory = ConversationMemory()
        self.sessions[memory.session_id] = memory
        self.current_session_id = memory.session_id

        # Trim old sessions if exceeding max
        if len(self.sessions) > self.max_sessions:
            oldest_id = min(self.sessions.keys())
            del self.sessions[oldest_id]
            logger.info(f"Removed old session: {oldest_id}")

        logger.info(f"Created session: {memory.session_id}")
        return memory.session_id

    def get_session(self, session_id: Optional[str] = None) -> Optional[ConversationMemory]:
        """Get conversation session."""
        if session_id is None:
            session_id = self.current_session_id

        return self.sessions.get(session_id)

    def add_message(
        self,
        role: MessageRole,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add message to session."""
        session = self.get_session(session_id)
        if session:
            session.add_message(role, content, metadata)

    def get_context_window(
        self,
        k: int = 5,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Get context window from session."""
        session = self.get_session(session_id)
        if session:
            return session.get_context_window(k)
        return []

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with stats."""
        return [
            {
                "session_id": session_id,
                "stats": memory.get_session_stats(),
            }
            for session_id, memory in self.sessions.items()
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
