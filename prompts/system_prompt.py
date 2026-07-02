"""
System prompts and chat templates.

Contains the system instructions and prompt templates
for guiding the chatbot behavior.
"""

from typing import Optional


class SystemPromptManager:
    """
    Manages system prompts for the chatbot.
    
    Provides system instructions, conversation templates,
    and prompt engineering utilities.
    """

    def __init__(self) -> None:
        """Initialize the system prompt manager."""
        pass

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the chatbot.
        
        Returns:
            System prompt string with instructions
        """
        pass

    def get_chat_template(self) -> str:
        """
        Get the chat message template.
        
        Returns:
            Chat template string
        """
        pass

    def get_citation_template(self) -> str:
        """
        Get the citation format template.
        
        Returns:
            Citation template string
        """
        pass

    def get_rejection_template(self) -> str:
        """
        Get the template for rejecting out-of-scope queries.
        
        Returns:
            Rejection response template
        """
        pass
