"""
Prompt orchestrator and response generation handler.

Manages prompt selection, validation, and response generation.
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import json

from prompts.system_prompts import (
    SystemPrompts,
    PromptTemplates,
    ResponseValidation,
    ConversationManager,
    PromptType,
)
from core.logger import get_logger

logger = get_logger(__name__)


class ResponseType(Enum):
    """Type of response generated."""
    ANSWERED = "answered"
    PARTIAL = "partial"
    REFUSAL = "refusal"
    CONFLICT = "conflict"
    CLARIFICATION_NEEDED = "clarification_needed"


class PromptOrchestrator:
    """Orchestrates prompt selection and management."""

    def __init__(self, enable_validation: bool = True) -> None:
        """
        Initialize prompt orchestrator.
        
        Args:
            enable_validation: Enable response validation
        """
        self.enable_validation = enable_validation
        self.conversation_manager = ConversationManager()

    def select_system_prompt(
        self,
        scenario: str = "default",
    ) -> str:
        """
        Select appropriate system prompt.
        
        Args:
            scenario: Scenario type (default, conflict, follow_up)
            
        Returns:
            System prompt string
        """
        scenarios = {
            "default": SystemPrompts.get_system_prompt,
            "context_aware": SystemPrompts.get_context_aware_prompt,
            "conflict": SystemPrompts.get_conflict_handling_prompt,
            "follow_up": SystemPrompts.get_follow_up_prompt,
            "refusal": SystemPrompts.get_refusal_prompt,
        }
        
        prompt_func = scenarios.get(scenario, SystemPrompts.get_system_prompt)
        return prompt_func()

    def build_user_message(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> str:
        """
        Build user message with context.
        
        Args:
            question: User question
            retrieved_chunks: Retrieved context chunks
            
        Returns:
            Formatted user message
        """
        try:
            # Format context
            context_parts = []
            for chunk in retrieved_chunks:
                context_part = PromptTemplates.format_context(
                    source_name=chunk.get("source_url", "Unknown"),
                    section=chunk.get("section", "General"),
                    content=chunk.get("text", "")[:500],  # Limit context length
                    timestamp=chunk.get("retrieved_at", ""),
                    score=chunk.get("similarity_score", 0.0),
                )
                context_parts.append(context_part)
            
            context_str = "\n\n".join(context_parts)
            
            # Format citations
            citations = []
            for chunk in retrieved_chunks:
                citation = PromptTemplates.format_citation(
                    section_name=chunk.get("section", "Unknown"),
                    url=chunk.get("source_url", "Unknown"),
                )
                citations.append(citation)
            
            citations_str = " ".join(citations)
            
            # Build message
            user_message = PromptTemplates.format_user_question(
                question=question,
                context=context_str,
                sources=citations_str,
            )
            
            return user_message
        
        except Exception as e:
            logger.error(f"Error building user message: {e}")
            return f"Question: {question}"

    def build_follow_up_message(
        self,
        current_question: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> str:
        """
        Build follow-up message with conversation context.
        
        Args:
            current_question: Current question
            retrieved_chunks: Retrieved context
            
        Returns:
            Formatted follow-up message
        """
        try:
            conversation_context = self.conversation_manager.get_conversation_context()
            
            context_str = "\n\n".join([
                chunk.get("text", "")[:500]
                for chunk in retrieved_chunks
            ])
            
            return PromptTemplates.format_follow_up(
                conversation_history=conversation_context,
                current_question=current_question,
                context=context_str,
            )
        
        except Exception as e:
            logger.error(f"Error building follow-up message: {e}")
            return f"Question: {current_question}"

    def build_conflict_message(
        self,
        conflict_info: Dict[str, Any],
    ) -> str:
        """
        Build conflict resolution message.
        
        Args:
            conflict_info: Conflicting information
            
        Returns:
            Formatted conflict message
        """
        try:
            return PromptTemplates.CONFLICT_RESOLUTION_TEMPLATE.format(
                source_a_info=conflict_info.get("source_a", ""),
                source_a_citation=conflict_info.get("citation_a", ""),
                source_b_info=conflict_info.get("source_b", ""),
                source_b_citation=conflict_info.get("citation_b", ""),
            )
        
        except Exception as e:
            logger.error(f"Error building conflict message: {e}")
            return "Conflict resolution error"

    def add_to_conversation_history(
        self,
        question: str,
        response: str,
        context_used: List[str],
    ) -> None:
        """
        Add exchange to conversation history.
        
        Args:
            question: User question
            response: Assistant response
            context_used: Context documents used
        """
        self.conversation_manager.add_exchange(question, response, context_used)
        logger.debug(f"Added to conversation history. Total exchanges: {len(self.conversation_manager.history)}")


class ResponseHandler:
    """Handles response generation and validation."""

    def __init__(self, enable_validation: bool = True) -> None:
        """Initialize response handler."""
        self.enable_validation = enable_validation

    def generate_answer(
        self,
        llm_response: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate answer response with citations.
        
        Args:
            llm_response: LLM generated response
            retrieved_chunks: Retrieved context chunks
            
        Returns:
            Formatted answer with metadata
        """
        try:
            # Extract sources
            sources = []
            for chunk in retrieved_chunks:
                sources.append(f"{chunk.get('section', 'Unknown')} - {chunk.get('source_url', 'Unknown')}")
            
            # Extract related topics from chunks
            related_topics = []
            for chunk in retrieved_chunks:
                section = chunk.get('section', '')
                if section and section not in related_topics:
                    related_topics.append(section)
            
            # Validate response if enabled
            validation_result = {}
            if self.enable_validation:
                context_str = "\n".join([c.get('text', '') for c in retrieved_chunks])
                validation_result = ResponseValidation.validate_response(llm_response, context_str)
            
            return {
                "type": ResponseType.ANSWERED.value,
                "response": llm_response,
                "sources": sources,
                "related_topics": related_topics,
                "validation": validation_result,
                "success": validation_result.get("passes_validation", True) if validation_result else True,
            }
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "type": ResponseType.ANSWERED.value,
                "response": llm_response,
                "error": str(e),
            }

    def generate_refusal(
        self,
        reason: str,
        alternatives: Optional[List[str]] = None,
        contact_info: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate refusal response.
        
        Args:
            reason: Reason for refusal
            alternatives: Alternative topics that can be answered
            contact_info: Contact information for next steps
            
        Returns:
            Formatted refusal response
        """
        try:
            alternatives = alternatives or [
                "Information about admissions",
                "Course and program details",
                "Campus facilities and services",
                "Academic calendar and schedules",
            ]
            
            next_steps = []
            if contact_info:
                next_steps.append(f"Contact: {contact_info}")
            next_steps.extend([
                "Try rephrasing your question",
                "Ask about related college topics",
            ])
            
            response_text = PromptTemplates.format_refusal(
                reason=reason,
                alternatives=alternatives,
                next_steps=next_steps,
            )
            
            return {
                "type": ResponseType.REFUSAL.value,
                "response": response_text,
                "reason": reason,
                "alternatives": alternatives,
                "success": True,
            }
        
        except Exception as e:
            logger.error(f"Error generating refusal: {e}")
            return {
                "type": ResponseType.REFUSAL.value,
                "response": f"I cannot answer this question. Please try rephrasing or ask about other college topics.",
                "error": str(e),
            }

    def generate_conflict_response(
        self,
        info_1: str,
        citation_1: str,
        info_2: str,
        citation_2: str,
        recommendation: str,
    ) -> Dict[str, Any]:
        """
        Generate conflict response.
        
        Args:
            info_1: First conflicting information
            citation_1: Citation for first
            info_2: Second conflicting information
            citation_2: Citation for second
            recommendation: Recommendation for verification
            
        Returns:
            Formatted conflict response
        """
        try:
            response_text = PromptTemplates.CONFLICT_TEMPLATE.format(
                info_1=info_1,
                citation_1=citation_1,
                info_2=info_2,
                citation_2=citation_2,
                recommendation=recommendation,
            )
            
            return {
                "type": ResponseType.CONFLICT.value,
                "response": response_text,
                "conflict_points": [info_1, info_2],
                "success": True,
            }
        
        except Exception as e:
            logger.error(f"Error generating conflict response: {e}")
            return {
                "type": ResponseType.CONFLICT.value,
                "response": "I found conflicting information. Please contact the relevant department.",
                "error": str(e),
            }

    def generate_clarification_request(
        self,
        interpretations: List[str],
    ) -> Dict[str, Any]:
        """
        Generate clarification request.
        
        Args:
            interpretations: Possible interpretations of the question
            
        Returns:
            Formatted clarification request
        """
        try:
            clarification_text = "I'm not entirely clear on your question. Did you mean:\n\n"
            for i, interp in enumerate(interpretations, 1):
                clarification_text += f"{i}. {interp}\n"
            clarification_text += "\nPlease clarify so I can provide accurate information."
            
            return {
                "type": ResponseType.CLARIFICATION_NEEDED.value,
                "response": clarification_text,
                "interpretations": interpretations,
                "success": True,
            }
        
        except Exception as e:
            logger.error(f"Error generating clarification: {e}")
            return {
                "type": ResponseType.CLARIFICATION_NEEDED.value,
                "response": "Could you please rephrase your question?",
                "error": str(e),
            }

    def validate_and_adjust(
        self,
        response: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate response and adjust if needed.
        
        Args:
            response: Generated response
            retrieved_chunks: Retrieved context
            
        Returns:
            Validated/adjusted response
        """
        try:
            if not self.enable_validation:
                return response
            
            if response["type"] != ResponseType.ANSWERED.value:
                return response
            
            # Check for validation issues
            validation = response.get("validation", {})
            
            if validation.get("has_hallucination_indicators"):
                logger.warning(f"Hallucination indicators found: {validation.get('hallucination_indicators')}")
                response["success"] = False
                response["warning"] = "Response may contain uncertain language"
            
            if not validation.get("has_citations"):
                logger.warning("No citations found in response")
                response["success"] = False
                response["warning"] = "Response missing citations"
            
            return response
        
        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return response
