"""
Tests for conversation memory system.
"""

import pytest
import json
from pathlib import Path

from memory.conversation_memory import (
    ConversationMessage,
    MessageRole,
    ContextTracker,
    TokenManager,
    ConversationSummarizer,
    ConversationMemory,
    MemoryManager,
)


class TestConversationMessage:
    """Tests for conversation messages."""

    def test_creates_message(self):
        """Test creating message."""
        msg = ConversationMessage(
            role=MessageRole.USER,
            content="What is the deadline?",
        )

        assert msg.role == MessageRole.USER
        assert msg.content == "What is the deadline?"
        assert msg.tokens > 0

    def test_message_to_dict(self):
        """Test converting to dict."""
        msg = ConversationMessage(MessageRole.ASSISTANT, "The deadline is March 31")
        d = msg.to_dict()

        assert d["role"] == "assistant"
        assert d["content"] == "The deadline is March 31"
        assert "timestamp" in d


class TestContextTracker:
    """Tests for context tracking."""

    def test_creates_tracker(self):
        """Test creating tracker."""
        tracker = ContextTracker()
        assert tracker is not None

    def test_extracts_department(self):
        """Test department extraction."""
        tracker = ContextTracker()
        tracker.extract_entities("Tell me about the CS program")

        assert tracker.department_context == "cs"

    def test_extracts_section(self):
        """Test section extraction."""
        tracker = ContextTracker()
        tracker.extract_entities("What about admissions?")

        assert tracker.section_context == "admissions"

    def test_resolves_pronoun(self):
        """Test pronoun resolution."""
        tracker = ContextTracker()
        tracker.mentioned_entities["it"] = "the deadline"

        assert tracker.resolve_pronoun("it") == "the deadline"

    def test_context_summary(self):
        """Test context summary generation."""
        tracker = ContextTracker()
        tracker.extract_entities("Tell me about CS admissions")

        summary = tracker.get_context_summary()
        assert "cs" in summary.lower()


class TestTokenManager:
    """Tests for token management."""

    def test_creates_manager(self):
        """Test creating manager."""
        manager = TokenManager()
        assert manager.total_tokens == 0

    def test_adds_tokens(self):
        """Test adding tokens."""
        manager = TokenManager()
        manager.add_tokens(100)
        manager.add_tokens(50)

        assert manager.get_total_tokens() == 150

    def test_detects_summarization_needed(self):
        """Test summarization detection."""
        manager = TokenManager(max_context_tokens=1000, summary_threshold=900)

        assert not manager.should_summarize(800)
        assert manager.should_summarize(950)

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        manager = TokenManager(max_context_tokens=1000)

        ratio = manager.calculate_compression_needed(500)
        assert ratio == 1.0  # No compression needed

        ratio = manager.calculate_compression_needed(2000)
        assert ratio == 0.5  # Compress to 50%


class TestConversationSummarizer:
    """Tests for summarization."""

    def test_creates_summary(self):
        """Test summary creation."""
        messages = [
            ConversationMessage(MessageRole.USER, "What is the deadline?"),
            ConversationMessage(MessageRole.ASSISTANT, "The deadline is March 31"),
        ]

        summary = ConversationSummarizer.create_summary(messages)
        assert summary
        assert "deadline" in summary.lower() or "march" in summary.lower()

    def test_empty_summary(self):
        """Test empty summary."""
        summary = ConversationSummarizer.create_summary([])
        assert summary == ""


class TestConversationMemory:
    """Tests for conversation memory."""

    def test_creates_memory(self):
        """Test creating memory."""
        memory = ConversationMemory()
        assert memory.session_id
        assert len(memory.messages) == 0

    def test_adds_message(self):
        """Test adding message."""
        memory = ConversationMemory()
        memory.add_message(MessageRole.USER, "Hello")

        assert len(memory.messages) == 1
        assert memory.messages[0].content == "Hello"

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation."""
        memory = ConversationMemory()

        memory.add_message(MessageRole.USER, "What is the deadline?")
        memory.add_message(MessageRole.ASSISTANT, "The deadline is March 31")
        memory.add_message(MessageRole.USER, "How long before that?")
        memory.add_message(MessageRole.ASSISTANT, "Approximately 2 months")

        assert len(memory.messages) == 4
        assert memory.messages[-1].role == MessageRole.ASSISTANT

    def test_context_window(self):
        """Test context window generation."""
        memory = ConversationMemory()

        for i in range(10):
            memory.add_message(
                MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                f"Message {i}"
            )

        context = memory.get_context_window(k=3)
        assert len(context) <= 3

    def test_department_extraction(self):
        """Test department extraction."""
        memory = ConversationMemory()
        memory.add_message(MessageRole.USER, "Tell me about CS program")

        depts = memory.get_mentioned_departments()
        assert "Computer Science" in depts

    def test_token_limiting(self):
        """Test message limiting."""
        memory = ConversationMemory(max_messages=5)

        for i in range(10):
            memory.add_message(MessageRole.USER, f"Message {i}")

        assert len(memory.messages) <= 5

    def test_session_stats(self):
        """Test session statistics."""
        memory = ConversationMemory()
        memory.add_message(MessageRole.USER, "Hello")
        memory.add_message(MessageRole.ASSISTANT, "Hi there")

        stats = memory.get_session_stats()
        assert stats["total_messages"] == 2
        assert stats["total_tokens"] > 0

    def test_export_session(self, tmp_path):
        """Test exporting session."""
        memory = ConversationMemory()
        memory.add_message(MessageRole.USER, "Hello")
        memory.add_message(MessageRole.ASSISTANT, "Hi")

        export_file = tmp_path / "session.json"
        memory.export_session(str(export_file))

        assert export_file.exists()

        with open(export_file, 'r') as f:
            data = json.load(f)
            assert len(data["messages"]) == 2

    def test_import_session(self, tmp_path):
        """Test importing session."""
        # Create and export
        memory1 = ConversationMemory()
        memory1.add_message(MessageRole.USER, "Question")
        memory1.add_message(MessageRole.ASSISTANT, "Answer")

        export_file = tmp_path / "session.json"
        memory1.export_session(str(export_file))

        # Import
        memory2 = ConversationMemory()
        memory2.import_session(str(export_file))

        assert len(memory2.messages) == 2
        assert memory2.messages[0].content == "Question"

    def test_clear_history(self):
        """Test clearing history."""
        memory = ConversationMemory()
        memory.add_message(MessageRole.USER, "Message")

        memory.clear_history()

        assert len(memory.messages) == 0
        assert memory.summary is None


class TestMemoryManager:
    """Tests for memory manager."""

    def test_creates_manager(self):
        """Test creating manager."""
        manager = MemoryManager()
        assert len(manager.sessions) == 0

    def test_creates_session(self):
        """Test creating session."""
        manager = MemoryManager()
        session_id = manager.create_session()

        assert session_id
        assert session_id in manager.sessions
        assert manager.current_session_id == session_id

    def test_multiple_sessions(self):
        """Test multiple sessions."""
        manager = MemoryManager()

        id1 = manager.create_session()
        id2 = manager.create_session()

        assert id1 != id2
        assert len(manager.sessions) == 2

    def test_add_message_to_session(self):
        """Test adding message to session."""
        manager = MemoryManager()
        session_id = manager.create_session()

        manager.add_message(MessageRole.USER, "Hello", session_id=session_id)

        session = manager.get_session(session_id)
        assert len(session.messages) == 1

    def test_delete_session(self):
        """Test deleting session."""
        manager = MemoryManager()
        session_id = manager.create_session()

        manager.delete_session(session_id)

        assert session_id not in manager.sessions

    def test_list_sessions(self):
        """Test listing sessions."""
        manager = MemoryManager()

        manager.create_session()
        manager.create_session()

        sessions = manager.list_sessions()
        assert len(sessions) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
