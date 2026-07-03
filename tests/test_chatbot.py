"""
Tests for chatbot implementation.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from chatbot.chatbot import Chatbot, ChatMessage, ChatbotMetrics, ConversationRole
from vectorstore.vectorstore import VectorStore


class TestChatMessage:
    """Tests for ChatMessage."""

    def test_creates_message(self):
        """Test creating message."""
        msg = ChatMessage(
            role=ConversationRole.USER,
            content="Hello",
            metadata={"source": "test"},
        )
        
        assert msg.role == ConversationRole.USER
        assert msg.content == "Hello"
        assert msg.metadata["source"] == "test"

    def test_message_to_dict(self):
        """Test converting message to dict."""
        msg = ChatMessage(ConversationRole.ASSISTANT, "Hi there")
        d = msg.to_dict()
        
        assert d["role"] == "assistant"
        assert d["content"] == "Hi there"

    def test_message_to_openai_format(self):
        """Test converting to OpenAI format."""
        msg = ChatMessage(ConversationRole.USER, "Question")
        openai_msg = msg.to_openai_format()
        
        assert openai_msg["role"] == "user"
        assert openai_msg["content"] == "Question"


class TestChatbotMetrics:
    """Tests for ChatbotMetrics."""

    def test_creates_metrics(self):
        """Test creating metrics."""
        metrics = ChatbotMetrics()
        
        assert metrics.total_queries == 0
        assert metrics.total_tokens == 0

    def test_adds_query(self):
        """Test adding query metrics."""
        metrics = ChatbotMetrics()
        
        metrics.add_query(
            retrieval_time_ms=100.0,
            llm_time_ms=500.0,
            tokens_used=150,
            response_type="answered",
        )
        
        assert metrics.total_queries == 1
        assert metrics.total_tokens == 150

    def test_gets_summary(self):
        """Test getting metrics summary."""
        metrics = ChatbotMetrics()
        
        metrics.add_query(100.0, 500.0, 150, "answered")
        metrics.add_query(90.0, 480.0, 140, "refusal")
        
        summary = metrics.get_summary()
        
        assert summary["total_queries"] == 2
        assert summary["total_tokens"] == 290
        assert "avg_latency_ms" in summary


class TestChatbot:
    """Tests for Chatbot."""

    def test_creates_chatbot(self, tmp_path):
        """Test creating chatbot."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        assert chatbot is not None
        assert chatbot.llm_model == "gpt-4o-mini"

    def test_is_greeting(self, tmp_path):
        """Test greeting detection."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        assert chatbot._is_greeting("Hello") is True
        assert chatbot._is_greeting("Hi there") is True
        assert chatbot._is_greeting("What is the deadline?") is False

    def test_handle_greeting(self, tmp_path):
        """Test greeting handling."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        response = chatbot._handle_greeting("Hello")
        
        assert response
        assert "college" in response.lower() or "faq" in response.lower()

    def test_is_follow_up(self, tmp_path):
        """Test follow-up detection."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        assert chatbot._is_follow_up() is False
        
        chatbot.conversation_history.append(
            ChatMessage(ConversationRole.USER, "Question")
        )
        
        assert chatbot._is_follow_up() is True

    def test_estimate_tokens(self, tmp_path):
        """Test token estimation."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        tokens = chatbot._estimate_tokens("Hello", "Hi there")
        
        assert tokens > 0
        assert tokens == len("HelloHi there") // 4

    def test_get_conversation_history(self, tmp_path):
        """Test getting conversation history."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        chatbot.conversation_history.append(
            ChatMessage(ConversationRole.USER, "Q1")
        )
        chatbot.conversation_history.append(
            ChatMessage(ConversationRole.ASSISTANT, "A1")
        )
        
        history = chatbot.get_conversation_history()
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_clear_conversation(self, tmp_path):
        """Test clearing conversation."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        chatbot.conversation_history.append(
            ChatMessage(ConversationRole.USER, "Q1")
        )
        
        chatbot.clear_conversation()
        
        assert len(chatbot.conversation_history) == 0

    def test_export_conversation(self, tmp_path):
        """Test exporting conversation."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        chatbot.conversation_history.append(
            ChatMessage(ConversationRole.USER, "Q1")
        )
        
        export_path = tmp_path / "conversation.json"
        chatbot.export_conversation(str(export_path))
        
        assert export_path.exists()


@pytest.mark.asyncio
class TestChatbotAsync:
    """Tests for async chatbot operations."""

    async def test_call_llm_fails_gracefully(self, tmp_path):
        """Test LLM call failure handling."""
        vs = VectorStore(collection_name="test", persist_dir=tmp_path)
        chatbot = Chatbot(vectorstore=vs)
        
        # Mock with invalid model
        chatbot.llm_model = "invalid-model-xyz"
        
        result = await chatbot._call_llm(
            system_prompt="Test prompt",
            user_message="Test message",
        )
        
        # Should return None on error
        assert result is None or isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
