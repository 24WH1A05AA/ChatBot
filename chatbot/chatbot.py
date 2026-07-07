"""
Main chatbot orchestrator integrating retriever, prompts, and LLM.

Implements the complete RAG pipeline: Question → Retriever → Prompt → LLM → Answer.
With security validation for input/output.
"""

from typing import List, Dict, Any, Optional, Tuple
import time
import json
from datetime import datetime
from enum import Enum

from retriever.retrieval_pipeline import RetrievalPipeline, RetrievalResult
from prompts.system_prompts import SystemPrompts, ConversationManager
from prompts.prompt_orchestrator import PromptOrchestrator, ResponseHandler, ResponseType
from vectorstore.vectorstore import VectorStore
from security.security import SecurityManager
from llm import get_llm_provider, LLMProvider
from config import get_settings
from core.logger import get_logger
from core.optimization import (
    get_optimization_engine,
    StructuredLogger,
    cached,
    retry,
    timed,
    log_correlation_id,
    BatchProcessor,
    BatchConfig,
    Compression,
)

logger = get_logger(__name__)


class ConversationRole(Enum):
    """Conversation roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage:
    """Single message in conversation."""

    def __init__(
        self,
        role: ConversationRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize chat message."""
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def to_openai_format(self) -> Dict[str, str]:
        """Convert to OpenAI message format."""
        return {
            "role": self.role.value,
            "content": self.content,
        }


class ChatbotMetrics:
    """Metrics for chatbot operations."""

    def __init__(self) -> None:
        """Initialize metrics."""
        self.total_queries = 0
        self.total_latency_ms = 0.0
        self.total_tokens = 0
        self.retrieval_times = []
        self.llm_times = []
        self.response_types: Dict[str, int] = {}

    def add_query(
        self,
        retrieval_time_ms: float,
        llm_time_ms: float,
        tokens_used: int,
        response_type: str,
    ) -> None:
        """Record query metrics."""
        self.total_queries += 1
        self.total_latency_ms += retrieval_time_ms + llm_time_ms
        self.total_tokens += tokens_used
        self.retrieval_times.append(retrieval_time_ms)
        self.llm_times.append(llm_time_ms)
        self.response_types[response_type] = self.response_types.get(response_type, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_queries": self.total_queries,
            "avg_latency_ms": self.total_latency_ms / max(self.total_queries, 1),
            "total_tokens": self.total_tokens,
            "avg_retrieval_ms": sum(self.retrieval_times) / max(len(self.retrieval_times), 1),
            "avg_llm_ms": sum(self.llm_times) / max(len(self.llm_times), 1),
            "response_type_distribution": self.response_types,
        }


class Chatbot:
    """Main chatbot orchestrator."""

    def __init__(
        self,
        vectorstore: VectorStore,
        llm_provider: Optional[LLMProvider] = None,
        max_conversation_history: int = 20,
        retrieval_k: int = 5,
        temperature: float = 0.0,
    ) -> None:
        """
        Initialize chatbot.
        
        Args:
            vectorstore: Vector store instance
            llm_provider: LLM provider instance (uses default if None)
            max_conversation_history: Max conversation turns
            retrieval_k: Number of retrieved chunks
            temperature: LLM temperature (0.0 = deterministic)
        """
        self.vectorstore = vectorstore
        self.llm_provider = llm_provider or get_llm_provider()
        self.settings = get_settings()
        self.retrieval_k = retrieval_k
        self.temperature = temperature
        
        # Initialize components
        self.retrieval_pipeline = RetrievalPipeline(vectorstore)
        self.prompt_orchestrator = PromptOrchestrator(enable_validation=True)
        self.response_handler = ResponseHandler(enable_validation=True)
        self.conversation_manager = ConversationManager(max_history=max_conversation_history)
        self.security_manager = SecurityManager()
        
        # Conversation state
        self.conversation_history: List[ChatMessage] = []
        self.metrics = ChatbotMetrics()
        
        provider_name = self.settings.LLM_PROVIDER
        logger.info(f"Initialized Chatbot with {provider_name} provider")
        logger.info("Security validation enabled")

    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting."""
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        return any(query.lower().startswith(g) for g in greetings)

    def _handle_greeting(self, query: str) -> str:
        """Handle greeting query."""
        greetings_responses = [
            "Hello! I'm the college FAQ chatbot. I can help you with questions about admissions, academics, campus facilities, and more. What would you like to know?",
            "Hi there! Welcome to the college FAQ chatbot. Feel free to ask me anything about our college. How can I help?",
            "Greetings! I'm here to answer your questions about the college. What's on your mind?",
        ]
        
        import random
        response = random.choice(greetings_responses)
        logger.info("Handled greeting query")
        return response

    def _is_follow_up(self) -> bool:
        """Check if query is a follow-up."""
        return len(self.conversation_history) > 0

    async def chat(
        self,
        query: str,
        section: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process user query and return response.
        
        Args:
            query: User question
            section: Optional section filter
            department: Optional department filter
            
        Returns:
            Complete response with all metadata
        """
        try:
            start_time = time.time()
            
            # SECURITY: Validate user input for attacks
            is_safe, rejection_reason = self.security_manager.validate_user_input(query)
            if not is_safe:
                logger.warning(f"Security violation detected: {rejection_reason}")
                self.conversation_history.append(
                    ChatMessage(ConversationRole.USER, query)
                )
                self.conversation_history.append(
                    ChatMessage(ConversationRole.ASSISTANT, rejection_reason)
                )
                return {
                    "query": query,
                    "response": rejection_reason,
                    "type": "rejection",
                    "sources": [],
                    "retrieved_chunks": [],
                    "metrics": {
                        "latency_ms": (time.time() - start_time) * 1000,
                        "retrieval_ms": 0,
                        "llm_ms": 0,
                        "tokens_used": 0,
                    },
                    "success": False,
                }
            
            # Add user message to history
            self.conversation_history.append(
                ChatMessage(ConversationRole.USER, query)
            )
            
            # Check if greeting
            if self._is_greeting(query):
                greeting_response = self._handle_greeting(query)
                self.conversation_history.append(
                    ChatMessage(ConversationRole.ASSISTANT, greeting_response)
                )
                return {
                    "query": query,
                    "response": greeting_response,
                    "type": "greeting",
                    "sources": [],
                    "retrieved_chunks": [],
                    "metrics": {
                        "latency_ms": (time.time() - start_time) * 1000,
                        "tokens_used": 0,
                    },
                    "success": True,
                }
            
            # Retrieve relevant chunks
            retrieval_start = time.time()
            retrieval_result = self.retrieval_pipeline.retrieve(
                query=query,
                k=self.retrieval_k,
                section=section,
                department=department,
            )
            retrieval_time = (time.time() - retrieval_start) * 1000
            
            if not retrieval_result or not retrieval_result.results:
                logger.warning("No relevant context retrieved")
                response = self.response_handler.generate_refusal(
                    reason="No relevant information found in knowledge base",
                    alternatives=[
                        "Try rephrasing your question",
                        "Ask about admissions, academics, or campus facilities",
                        "Contact the relevant department directly",
                    ],
                    contact_info="help@college.edu",
                )
                
                self.conversation_history.append(
                    ChatMessage(ConversationRole.ASSISTANT, response["response"])
                )
                
                return {
                    "query": query,
                    "response": response["response"],
                    "type": response["type"],
                    "sources": [],
                    "retrieved_chunks": [],
                    "metrics": {
                        "latency_ms": (time.time() - start_time) * 1000,
                        "retrieval_ms": retrieval_time,
                        "tokens_used": 0,
                    },
                    "success": True,
                }
            
            # Build prompt
            scenario = "follow_up" if self._is_follow_up() else "default"
            system_prompt = self.prompt_orchestrator.select_system_prompt(scenario)
            
            # Format chunks for message
            formatted_chunks = [r.to_dict() for r in retrieval_result.results]
            
            if scenario == "follow_up":
                user_message = self.prompt_orchestrator.build_follow_up_message(
                    current_question=query,
                    retrieved_chunks=formatted_chunks,
                )
            else:
                user_message = self.prompt_orchestrator.build_user_message(
                    question=query,
                    retrieved_chunks=formatted_chunks,
                )
            
            # Call LLM
            llm_start = time.time()
            llm_response = await self._call_llm(system_prompt, user_message)
            llm_time = (time.time() - llm_start) * 1000
            
            if llm_response is None:
                logger.error("LLM call failed")
                response = {
                    "type": ResponseType.REFUSAL.value,
                    "response": "I encountered an error processing your question. Please try again.",
                    "success": False,
                }
            else:
                # Generate response object
                response = self.response_handler.generate_answer(
                    llm_response=llm_response,
                    retrieved_chunks=formatted_chunks,
                )
                
                # SECURITY: Validate LLM output for information leaks
                is_safe, sanitized_response = self.security_manager.validate_llm_output(
                    response["response"]
                )
                if not is_safe:
                    logger.warning("Information leak detected in LLM response, sanitizing...")
                    response["response"] = sanitized_response
            
            # Extract sources
            sources = []
            for result in retrieval_result.results:
                sources.append({
                    "url": result.metadata.get("source_url"),
                    "section": result.metadata.get("section"),
                    "title": result.metadata.get("chunk_title"),
                    "similarity_score": result.similarity_score,
                })
            
            # Estimate tokens (rough calculation)
            tokens_used = self._estimate_tokens(user_message, llm_response or "")
            
            # Add assistant message
            self.conversation_history.append(
                ChatMessage(
                    ConversationRole.ASSISTANT,
                    response["response"],
                    metadata={
                        "type": response.get("type"),
                        "sources": sources,
                    }
                )
            )
            
            # Track conversation
            self.prompt_orchestrator.add_to_conversation_history(
                question=query,
                response=response["response"],
                context_used=[r.metadata.get("source_url", "") for r in retrieval_result.results],
            )
            
            # Record metrics
            self.metrics.add_query(
                retrieval_time_ms=retrieval_time,
                llm_time_ms=llm_time,
                tokens_used=tokens_used,
                response_type=response.get("type", "unknown"),
            )
            
            # Build complete response
            return {
                "query": query,
                "response": response["response"],
                "type": response.get("type"),
                "sources": sources,
                "retrieved_chunks": formatted_chunks,
                "metrics": {
                    "total_latency_ms": (time.time() - start_time) * 1000,
                    "retrieval_ms": retrieval_time,
                    "llm_ms": llm_time,
                    "tokens_used": tokens_used,
                },
                "validation": response.get("validation", {}),
                "success": response.get("success", True),
            }
        
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return {
                "query": query,
                "response": f"An error occurred: {str(e)}",
                "type": "error",
                "sources": [],
                "retrieved_chunks": [],
                "metrics": {
                    "latency_ms": (time.time() - start_time) * 1000,
                },
                "success": False,
            }

    async def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
    ) -> Optional[str]:
        """
        Call LLM with messages using configured provider.
        
        Args:
            system_prompt: System prompt
            user_message: User message
            
        Returns:
            LLM response or None on error
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
            
            # Use LLM provider (OpenRouter with fallback or OpenAI)
            response = await self.llm_provider.generate(
                messages=messages,
                temperature=self.temperature,
                max_tokens=2000,
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return None

    def _estimate_tokens(self, user_message: str, llm_response: str) -> int:
        """
        Rough token estimation.
        
        Args:
            user_message: User message
            llm_response: LLM response
            
        Returns:
            Estimated tokens
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(user_message + llm_response) // 4

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return [msg.to_dict() for msg in self.conversation_history]

    def get_metrics(self) -> Dict[str, Any]:
        """Get chatbot metrics."""
        return self.metrics.get_summary()
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security violation summary."""
        return self.security_manager.get_security_summary()
    
    def export_security_log(self, filepath: str) -> None:
        """Export security log to file."""
        self.security_manager.export_security_log(filepath)
        logger.info(f"Exported security log to {filepath}")

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.conversation_manager.clear_history()
        logger.info("Cleared conversation history")

    def export_conversation(self, filepath: str) -> None:
        """Export conversation to file."""
        try:
            data = {
                "conversation": self.get_conversation_history(),
                "metrics": self.get_metrics(),
                "exported_at": datetime.utcnow().isoformat(),
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Exported conversation to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting conversation: {e}")
