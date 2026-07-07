"""
Configuration package for College FAQ Chatbot.

This package manages all application-level configuration,
settings, and environment variables.
"""

from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
