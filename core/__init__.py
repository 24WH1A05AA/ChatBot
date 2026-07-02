"""
Core package containing shared utilities, logging, exceptions, and base classes.

This package provides the foundational infrastructure for the entire application.
"""

from core.exceptions import *
from core.logger import get_logger

__all__ = [
    "get_logger",
    "AppException",
    "ValidationError",
    "CrawlerError",
    "IngestionError",
    "RetrieverError",
    "ChatbotError",
    "EvaluationError",
]
