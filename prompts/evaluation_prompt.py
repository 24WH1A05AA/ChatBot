"""
Evaluation prompts for RAGAS scoring.

Contains prompts used by RAGAS to evaluate
response quality metrics.
"""

from typing import Optional


class EvaluationPromptManager:
    """
    Manages prompts used for evaluation.
    
    Provides templates for faithfulness, relevancy,
    and other quality metrics.
    """

    def __init__(self) -> None:
        """Initialize the evaluation prompt manager."""
        pass

    def get_faithfulness_prompt(self) -> str:
        """
        Get prompt for evaluating faithfulness.
        
        Returns:
            Faithfulness evaluation prompt
        """
        pass

    def get_relevancy_prompt(self) -> str:
        """
        Get prompt for evaluating relevancy.
        
        Returns:
            Relevancy evaluation prompt
        """
        pass

    def get_context_precision_prompt(self) -> str:
        """
        Get prompt for evaluating context precision.
        
        Returns:
            Context precision evaluation prompt
        """
        pass

    def get_context_recall_prompt(self) -> str:
        """
        Get prompt for evaluating context recall.
        
        Returns:
            Context recall evaluation prompt
        """
        pass
