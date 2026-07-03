"""
Tests for system prompts and prompt orchestration.
"""

import pytest
from prompts.system_prompts import (
    SystemPrompts,
    PromptTemplates,
    ResponseValidation,
    ConversationManager,
)
from prompts.prompt_orchestrator import (
    PromptOrchestrator,
    ResponseHandler,
    ResponseType,
)


class TestSystemPrompts:
    """Tests for system prompts."""

    def test_get_base_system_prompt(self):
        """Test getting base system prompt."""
        prompt = SystemPrompts.get_system_prompt()
        
        assert prompt
        assert "CRITICAL RULES" in prompt
        assert "NEVER HALLUCINATE" in prompt
        assert "ALWAYS CITE" in prompt

    def test_base_prompt_has_all_rules(self):
        """Test base prompt contains all rules."""
        prompt = SystemPrompts.get_system_prompt()
        
        required_rules = [
            "ANSWER ONLY FROM RETRIEVED CONTEXT",
            "NEVER HALLUCINATE",
            "ALWAYS CITE SOURCES",
            "REFUSE UNSUPPORTED QUESTIONS",
            "MENTION CONFLICTING INFORMATION",
            "MAINTAIN PROFESSIONAL TONE",
            "SUPPORT FOLLOW-UP QUESTIONS",
            "CONVERSATION MEMORY",
        ]
        
        for rule in required_rules:
            assert rule in prompt

    def test_get_context_aware_prompt(self):
        """Test context aware prompt."""
        prompt = SystemPrompts.get_context_aware_prompt()
        
        assert prompt
        assert "Response Structure" in prompt

    def test_get_conflict_handling_prompt(self):
        """Test conflict handling prompt."""
        prompt = SystemPrompts.get_conflict_handling_prompt()
        
        assert prompt
        assert "ACKNOWLEDGE THE CONFLICT" in prompt

    def test_get_follow_up_prompt(self):
        """Test follow-up prompt."""
        prompt = SystemPrompts.get_follow_up_prompt()
        
        assert prompt
        assert "REFERENCE PREVIOUS CONTEXT" in prompt

    def test_get_refusal_prompt(self):
        """Test refusal prompt."""
        prompt = SystemPrompts.get_refusal_prompt()
        
        assert prompt
        assert "TEMPLATE RESPONSES" in prompt


class TestPromptTemplates:
    """Tests for prompt templates."""

    def test_format_citation(self):
        """Test citation formatting."""
        citation = PromptTemplates.format_citation(
            section_name="Admissions",
            url="https://college.edu/admissions",
        )
        
        assert "[Source:" in citation
        assert "Admissions" in citation
        assert "https://college.edu/admissions" in citation

    def test_format_context(self):
        """Test context formatting."""
        context = PromptTemplates.format_context(
            source_name="College Website",
            section="Admissions",
            content="Application deadline is March 31",
            score=0.92,
        )
        
        assert "College Website" in context
        assert "Admissions" in context
        assert "Application deadline" in context
        assert "92%" in context or "0.92" in context

    def test_format_user_question(self):
        """Test user question formatting."""
        message = PromptTemplates.format_user_question(
            question="What is the admission deadline?",
            context="The deadline is March 31",
            sources="[Source: Admissions]",
        )
        
        assert "Question:" in message
        assert "What is the admission deadline?" in message
        assert "March 31" in message

    def test_format_answer(self):
        """Test answer formatting."""
        answer = PromptTemplates.format_answer(
            answer="The deadline is March 31",
            sources=["Admissions Policy", "College Website"],
            related_topics=["Application Process", "Requirements"],
        )
        
        assert "March 31" in answer
        assert "Admissions Policy" in answer
        assert "Application Process" in answer

    def test_format_refusal(self):
        """Test refusal formatting."""
        refusal = PromptTemplates.format_refusal(
            reason="This is outside college scope",
            alternatives=["Question about admissions", "Academic programs"],
            next_steps=["Contact admissions office", "Visit college website"],
        )
        
        assert "outside college scope" in refusal
        assert "admissions" in refusal
        assert "Contact admissions office" in refusal


class TestResponseValidation:
    """Tests for response validation."""

    def test_detects_hallucination_indicators(self):
        """Test hallucination detection."""
        response = "I believe the deadline is March 31"
        
        indicators = ResponseValidation.check_hallucination_indicators(response)
        
        assert len(indicators) > 0
        assert any("believe" in str(i).lower() for i in indicators)

    def test_passes_hallucination_check(self):
        """Test response without hallucination."""
        response = "According to the admission policy [Source: Admissions], the deadline is March 31."
        
        indicators = ResponseValidation.check_hallucination_indicators(response)
        
        assert len(indicators) == 0

    def test_checks_citations(self):
        """Test citation checking."""
        response_with_citation = "The deadline is March 31 [Source: Admissions]"
        response_without_citation = "The deadline is March 31"
        
        assert ResponseValidation.check_citations(response_with_citation) is True
        assert ResponseValidation.check_citations(response_without_citation) is False

    def test_validate_response_complete(self):
        """Test complete response validation."""
        response = "According to policy [Source: Admissions], the deadline is March 31."
        context = "The deadline is March 31"
        
        validation = ResponseValidation.validate_response(response, context)
        
        assert "passes_validation" in validation
        assert validation["has_citations"] is True


class TestConversationManager:
    """Tests for conversation management."""

    def test_creates_conversation_manager(self):
        """Test creating manager."""
        manager = ConversationManager()
        
        assert manager is not None
        assert len(manager.history) == 0

    def test_adds_exchange(self):
        """Test adding exchange."""
        manager = ConversationManager()
        
        manager.add_exchange(
            user_question="What is the deadline?",
            assistant_response="The deadline is March 31",
            context_used=["Admissions Policy"],
        )
        
        assert len(manager.history) == 1
        assert manager.history[0]["user_question"] == "What is the deadline?"

    def test_maintains_max_history(self):
        """Test max history limit."""
        manager = ConversationManager(max_history=5)
        
        for i in range(10):
            manager.add_exchange(
                user_question=f"Question {i}",
                assistant_response=f"Answer {i}",
                context_used=[],
            )
        
        assert len(manager.history) <= 5

    def test_gets_conversation_context(self):
        """Test getting conversation context."""
        manager = ConversationManager()
        
        manager.add_exchange(
            user_question="Question 1",
            assistant_response="Answer 1",
            context_used=[],
        )
        
        context = manager.get_conversation_context()
        
        assert "Question 1" in context
        assert "Answer 1" in context

    def test_clears_history(self):
        """Test clearing history."""
        manager = ConversationManager()
        
        manager.add_exchange("Q1", "A1", [])
        manager.clear_history()
        
        assert len(manager.history) == 0


class TestPromptOrchestrator:
    """Tests for prompt orchestration."""

    def test_creates_orchestrator(self):
        """Test creating orchestrator."""
        orchestrator = PromptOrchestrator()
        
        assert orchestrator is not None

    def test_selects_system_prompt(self):
        """Test prompt selection."""
        orchestrator = PromptOrchestrator()
        
        prompt = orchestrator.select_system_prompt("default")
        
        assert prompt
        assert "CRITICAL RULES" in prompt

    def test_selects_conflict_prompt(self):
        """Test conflict prompt selection."""
        orchestrator = PromptOrchestrator()
        
        prompt = orchestrator.select_system_prompt("conflict")
        
        assert prompt
        assert "ACKNOWLEDGE THE CONFLICT" in prompt

    def test_builds_user_message(self):
        """Test user message building."""
        orchestrator = PromptOrchestrator()
        
        chunks = [
            {
                "text": "The deadline is March 31",
                "source_url": "https://college.edu/admissions",
                "section": "Admissions",
                "similarity_score": 0.92,
            }
        ]
        
        message = orchestrator.build_user_message(
            question="What is the deadline?",
            retrieved_chunks=chunks,
        )
        
        assert message
        assert "What is the deadline?" in message
        assert "March 31" in message

    def test_adds_to_history(self):
        """Test adding to conversation history."""
        orchestrator = PromptOrchestrator()
        
        orchestrator.add_to_conversation_history(
            question="Q1",
            response="A1",
            context_used=["source1"],
        )
        
        assert len(orchestrator.conversation_manager.history) == 1


class TestResponseHandler:
    """Tests for response handling."""

    def test_creates_handler(self):
        """Test creating handler."""
        handler = ResponseHandler()
        
        assert handler is not None

    def test_generates_answer(self):
        """Test answer generation."""
        handler = ResponseHandler()
        
        chunks = [
            {
                "text": "The deadline is March 31",
                "source_url": "https://college.edu",
                "section": "Admissions",
            }
        ]
        
        response = handler.generate_answer(
            llm_response="The deadline is March 31 [Source: Admissions]",
            retrieved_chunks=chunks,
        )
        
        assert response["type"] == ResponseType.ANSWERED.value
        assert len(response["sources"]) > 0

    def test_generates_refusal(self):
        """Test refusal generation."""
        handler = ResponseHandler()
        
        response = handler.generate_refusal(
            reason="Outside college scope",
            alternatives=["Admissions info"],
        )
        
        assert response["type"] == ResponseType.REFUSAL.value
        assert "outside college scope" in response["response"].lower()

    def test_generates_conflict_response(self):
        """Test conflict response."""
        handler = ResponseHandler()
        
        response = handler.generate_conflict_response(
            info_1="Deadline is March 31",
            citation_1="[Source: Policy A]",
            info_2="Deadline is April 15",
            citation_2="[Source: Policy B]",
            recommendation="Contact admissions office",
        )
        
        assert response["type"] == ResponseType.CONFLICT.value
        assert "March 31" in response["response"]
        assert "April 15" in response["response"]

    def test_generates_clarification_request(self):
        """Test clarification request."""
        handler = ResponseHandler()
        
        response = handler.generate_clarification_request(
            interpretations=[
                "Are you asking about admissions?",
                "Are you asking about deadlines?",
            ]
        )
        
        assert response["type"] == ResponseType.CLARIFICATION_NEEDED.value
        assert "admissions" in response["response"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
