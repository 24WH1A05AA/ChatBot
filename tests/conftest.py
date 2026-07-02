"""
Pytest configuration and fixtures.

Provides shared fixtures and configuration for tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir() -> Path:
    """Provide path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_document() -> dict:
    """Provide a sample document for testing."""
    return {
        "id": "test_doc_1",
        "url": "https://example.com/test",
        "title": "Test Document",
        "content": "This is test content for evaluation.",
        "metadata": {"category": "admissions"},
    }


@pytest.fixture
def sample_query() -> str:
    """Provide a sample query for testing."""
    return "What are the admission requirements?"


@pytest.fixture
def sample_context() -> list:
    """Provide sample context for testing."""
    return [
        "Admission requires a valid bachelor's degree.",
        "The application deadline is March 31st.",
        "Applicants must submit official transcripts.",
    ]
