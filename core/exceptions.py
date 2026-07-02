"""
Custom exception hierarchy for the College FAQ Chatbot.

Provides domain-specific exceptions for better error handling
and debugging across different application layers.
"""

from typing import Any, Optional


class AppException(Exception):
    """
    Base exception for all application-specific errors.
    
    Provides structured error information including error codes,
    messages, and optional context data.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize AppException.
        
        Args:
            message: Human-readable error message
            error_code: Unique error code for classification
            details: Additional context information
            cause: Original exception that caused this error
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r})"
        )


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize ValidationError."""
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            cause=cause,
        )


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize ConfigurationError."""
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details=details,
            cause=cause,
        )


class CrawlerError(AppException):
    """Base exception for web crawling operations."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize CrawlerError."""
        super().__init__(
            message=message,
            error_code="CRAWLER_ERROR",
            details=details,
            cause=cause,
        )


class IngestionError(AppException):
    """Base exception for knowledge base ingestion operations."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize IngestionError."""
        super().__init__(
            message=message,
            error_code="INGESTION_ERROR",
            details=details,
            cause=cause,
        )


class RetrieverError(AppException):
    """Base exception for retrieval operations."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize RetrieverError."""
        super().__init__(
            message=message,
            error_code="RETRIEVER_ERROR",
            details=details,
            cause=cause,
        )


class ChatbotError(AppException):
    """Base exception for chatbot operations."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize ChatbotError."""
        super().__init__(
            message=message,
            error_code="CHATBOT_ERROR",
            details=details,
            cause=cause,
        )


class EvaluationError(AppException):
    """Base exception for evaluation operations."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize EvaluationError."""
        super().__init__(
            message=message,
            error_code="EVALUATION_ERROR",
            details=details,
            cause=cause,
        )


class PromptInjectionError(AppException):
    """Raised when potential prompt injection is detected."""

    def __init__(
        self,
        message: str = "Potential prompt injection detected",
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize PromptInjectionError."""
        super().__init__(
            message=message,
            error_code="PROMPT_INJECTION_ERROR",
            details=details,
            cause=cause,
        )


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize RateLimitError."""
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            cause=cause,
        )


class TimeoutError(AppException):
    """Raised when operation times out."""

    def __init__(
        self,
        message: str = "Operation timed out",
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize TimeoutError."""
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details=details,
            cause=cause,
        )
