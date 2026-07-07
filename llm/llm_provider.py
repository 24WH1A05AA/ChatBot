"""
LLM Provider abstraction layer supporting OpenRouter and OpenAI.

Handles API calls, model fallback, rate limiting, and error handling.
"""

from typing import Optional, List, Dict, Any
import asyncio
import time
from enum import Enum
from abc import ABC, abstractmethod

import httpx
import openai
from openai import OpenAI, AsyncOpenAI

from config import get_settings
from core.logger import get_logger
from core.exceptions import LLMError
from core.optimization import (
    cached,
    retry,
    timed,
)

logger = get_logger(__name__)


class ProviderType(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OPENROUTER = "openrouter"


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """Generate LLM response."""
        pass

    @abstractmethod
    def generate_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """Generate LLM response (sync version)."""
        pass


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM provider with fallback support."""

    def __init__(self, api_key: str, base_model: str, fallback_models: List[str]):
        """
        Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key
            base_model: Primary model to use
            fallback_models: List of fallback models if primary fails
        """
        self.api_key = api_key
        self.base_model = base_model
        self.fallback_models = fallback_models
        self.base_url = "https://openrouter.io/api/v1"
        
        # Initialize async and sync clients
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.base_url,
        )
        
        self.model_queue = [base_model] + fallback_models
        self.current_model_index = 0
        self.failed_models = set()
        
        logger.info(f"Initialized OpenRouter provider with {len(self.model_queue)} models")
        logger.info(f"Primary model: {base_model}")
        logger.info(f"Fallback models: {fallback_models}")

    def _get_next_model(self) -> str:
        """Get next available model from queue."""
        available_models = [
            m for m in self.model_queue 
            if m not in self.failed_models
        ]
        
        if not available_models:
            logger.warning("All models failed, resetting failed models list")
            self.failed_models.clear()
            available_models = self.model_queue
        
        model = available_models[self.current_model_index % len(available_models)]
        self.current_model_index += 1
        return model

    def _mark_model_failed(self, model: str) -> None:
        """Mark model as failed for this session."""
        self.failed_models.add(model)
        logger.warning(f"Model {model} marked as failed, will use fallback")

    @retry(max_retries=3, base_delay=1.0)
    @timed
    def generate_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """
        Generate LLM response synchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (uses default if None)
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            Generated response text
            
        Raises:
            LLMError: If all models fail
        """
        model = model or self.base_model
        
        try:
            logger.debug(f"Generating response with model: {model}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.0,
                **kwargs,
            )
            
            result = response.choices[0].message.content
            logger.debug(f"Generated response with {len(result)} characters")
            return result
            
        except Exception as e:
            logger.warning(f"Model {model} failed: {str(e)}")
            self._mark_model_failed(model)
            
            # Try fallback models
            next_model = self._get_next_model()
            if next_model != model:
                logger.info(f"Trying fallback model: {next_model}")
                return self.generate_sync(
                    messages=messages,
                    model=next_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            else:
                raise LLMError(f"All models exhausted. Last error: {str(e)}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """
        Generate LLM response asynchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (uses default if None)
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            Generated response text
            
        Raises:
            LLMError: If all models fail
        """
        model = model or self.base_model
        
        try:
            logger.debug(f"Generating async response with model: {model}")
            
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.0,
                **kwargs,
            )
            
            result = response.choices[0].message.content
            logger.debug(f"Generated async response with {len(result)} characters")
            return result
            
        except Exception as e:
            logger.warning(f"Model {model} failed: {str(e)}")
            self._mark_model_failed(model)
            
            # Try fallback models
            next_model = self._get_next_model()
            if next_model != model:
                logger.info(f"Trying fallback model: {next_model}")
                return await self.generate(
                    messages=messages,
                    model=next_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            else:
                raise LLMError(f"All models exhausted. Last error: {str(e)}")


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.api_key = api_key
        self.model = model
        
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        
        logger.info(f"Initialized OpenAI provider with model: {model}")

    @retry(max_retries=3, base_delay=1.0)
    @timed
    def generate_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """Generate LLM response synchronously."""
        model = model or self.model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMError(f"OpenAI API error: {str(e)}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """Generate LLM response asynchronously."""
        model = model or self.model
        
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMError(f"OpenAI API error: {str(e)}")


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    _provider: Optional[LLMProvider] = None

    @classmethod
    def create(cls) -> LLMProvider:
        """
        Create LLM provider based on configuration.
        
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider configuration is invalid
        """
        if cls._provider is not None:
            return cls._provider
        
        settings = get_settings()
        
        if settings.LLM_PROVIDER == "openrouter":
            fallback_models = [
                m.strip() 
                for m in settings.OPENROUTER_FALLBACK_MODELS.split(",")
                if m.strip()
            ]
            
            cls._provider = OpenRouterProvider(
                api_key=settings.OPENROUTER_API_KEY,
                base_model=settings.OPENROUTER_MODEL,
                fallback_models=fallback_models,
            )
        elif settings.LLM_PROVIDER == "openai":
            cls._provider = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
            )
        else:
            raise ValueError(
                f"Unknown LLM provider: {settings.LLM_PROVIDER}"
            )
        
        logger.info(f"Created {settings.LLM_PROVIDER} provider")
        return cls._provider

    @classmethod
    def get(cls) -> LLMProvider:
        """Get or create LLM provider."""
        if cls._provider is None:
            return cls.create()
        return cls._provider

    @classmethod
    def reset(cls) -> None:
        """Reset provider instance (useful for testing)."""
        cls._provider = None


# Convenience functions
def get_llm_provider() -> LLMProvider:
    """Get LLM provider instance."""
    return LLMProviderFactory.get()


def create_llm_provider() -> LLMProvider:
    """Create new LLM provider instance."""
    return LLMProviderFactory.create()
