"""
Settings configuration using Pydantic v2 BaseSettings.

Handles all environment-based configuration with validation
and type safety. Supports environment-specific configurations
(development, staging, production).
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application configuration settings.
    
    Loads from environment variables and .env files.
    Uses Pydantic v2 for validation and type safety.
    """

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="production",
        description="Application environment"
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FILE: Path = Field(
        default=Path("logs/app.log"),
        description="Path to log file"
    )

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name"
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name"
    )

    # Website Crawling
    COLLEGE_WEBSITE_URL: str = Field(
        default="https://example.com",
        description="College website URL to crawl"
    )
    CRAWL_DEPTH: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum crawling depth"
    )
    MAX_PAGES: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum pages to crawl"
    )
    REQUEST_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        description="HTTP request timeout in seconds"
    )

    # ChromaDB Configuration
    CHROMA_DB_PATH: Path = Field(
        default=Path("./vectorstore/chroma_db"),
        description="Path to ChromaDB persistent storage"
    )
    PERSIST_DIRECTORY: Path = Field(
        default=Path("./knowledge_base"),
        description="Knowledge base directory path"
    )

    # Chunking Configuration
    CHUNK_SIZE: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Document chunk size in characters"
    )
    CHUNK_OVERLAP: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between chunks in characters"
    )

    # Retrieval Configuration
    TOP_K: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of top results to retrieve"
    )
    SIMILARITY_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )

    # RAGAS Configuration
    RAGAS_BATCH_SIZE: int = Field(
        default=10,
        ge=1,
        le=100,
        description="RAGAS evaluation batch size"
    )
    RAGAS_TIMEOUT: int = Field(
        default=60,
        ge=10,
        le=600,
        description="RAGAS evaluation timeout in seconds"
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("OPENAI_API_KEY", pre=True)
    def validate_api_key(cls, v: str) -> str:
        """Validate that OpenAI API key is provided."""
        if not v or v == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY must be set in environment variables"
            )
        return v

    @validator("COLLEGE_WEBSITE_URL", pre=True)
    def validate_website_url(cls, v: str) -> str:
        """Validate website URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(
                "COLLEGE_WEBSITE_URL must start with http:// or https://"
            )
        return v

    @validator("CHUNK_OVERLAP", pre=True)
    def validate_chunk_overlap(cls, v: int, values: dict) -> int:
        """Validate that chunk overlap is less than chunk size."""
        chunk_size = values.get("CHUNK_SIZE", 1000)
        if v >= chunk_size:
            raise ValueError(
                "CHUNK_OVERLAP must be less than CHUNK_SIZE"
            )
        return v


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings: Configuration settings instance
    """
    return Settings()
