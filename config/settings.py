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

    # LLM Provider Configuration
    LLM_PROVIDER: Literal["openai", "openrouter"] = Field(
        default="openrouter",
        description="LLM provider (openai or openrouter)"
    )
    
    # OpenAI Configuration (legacy, kept for backward compatibility)
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key (optional if using OpenRouter)"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name"
    )
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = Field(
        default="",
        description="OpenRouter API key"
    )
    OPENROUTER_MODEL: str = Field(
        default="openai/gpt-oss-120b:free",
        description="OpenRouter model identifier"
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.io/api/v1",
        description="OpenRouter API base URL"
    )
    
    # Model Fallback List (comma-separated)
    OPENROUTER_FALLBACK_MODELS: str = Field(
        default="deepseek/deepseek-chat-v3-0324:free,qwen/qwen3-235b-a22b:free,deepseek/deepseek-r1:free,meta-llama/llama-4-maverick:free,nvidia/nemotron-3-super:free,nvidia/nemotron-3-ultra:free,google/gemma-3-27b-it:free",
        description="Comma-separated list of fallback models"
    )
    
    # Embedding Model Configuration
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name"
    )
    EMBEDDING_PROVIDER: Literal["openai", "huggingface", "local"] = Field(
        default="openai",
        description="Embedding model provider"
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

    # -------------------------------------------------------------------------
    # Optimization Configuration
    # -------------------------------------------------------------------------

    # Caching
    CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable caching layer"
    )
    CACHE_EMBEDDING_MAX_SIZE: int = Field(
        default=500,
        ge=10,
        le=10000,
        description="Max query embeddings cache entries"
    )
    CACHE_EMBEDDING_TTL: int = Field(
        default=600,
        ge=30,
        le=86400,
        description="Query embedding cache TTL (seconds)"
    )
    CACHE_LLM_MAX_SIZE: int = Field(
        default=200,
        ge=10,
        le=5000,
        description="Max LLM response cache entries"
    )
    CACHE_LLM_TTL: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="LLM response cache TTL (seconds)"
    )
    CACHE_CRAWL_MAX_SIZE: int = Field(
        default=100,
        ge=10,
        le=5000,
        description="Max crawl result cache entries"
    )
    CACHE_CRAWL_TTL: int = Field(
        default=1800,
        ge=60,
        le=86400,
        description="Crawl result cache TTL (seconds)"
    )
    CACHE_FILE_MAX_SIZE: int = Field(
        default=1000,
        ge=10,
        le=50000,
        description="Max file cache entries"
    )
    CACHE_FILE_TTL: int = Field(
        default=300,
        ge=30,
        le=86400,
        description="File cache TTL (seconds)"
    )
    CACHE_MAX_MEMORY_MB: float = Field(
        default=200.0,
        ge=10.0,
        le=2000.0,
        description="Total cache memory budget (MB)"
    )

    # Parallel Execution
    PARALLEL_EMBEDDING_WORKERS: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Parallel embedding workers"
    )
    PARALLEL_CRAWL_WORKERS: int = Field(
        default=8,
        ge=1,
        le=64,
        description="Parallel crawl workers"
    )
    PARALLEL_GENERAL_WORKERS: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Parallel general workers"
    )
    EMBEDDING_RATE_LIMIT: int = Field(
        default=50,
        ge=1,
        le=5000,
        description="Embedding API rate limit (req/s)"
    )
    CRAWL_RATE_LIMIT: int = Field(
        default=30,
        ge=1,
        le=1000,
        description="Crawl rate limit (req/s)"
    )

    # Batch Processing
    BATCH_SIZE: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Default batch size for batch processing"
    )
    BATCH_MAX_CONCURRENT: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Max concurrent batch operations"
    )
    BATCH_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Batch timeout in seconds"
    )

    # Retry Configuration
    RETRY_MAX_ATTEMPTS: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts"
    )
    RETRY_BASE_DELAY: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Base retry delay in seconds"
    )
    RETRY_MAX_DELAY: float = Field(
        default=60.0,
        ge=1.0,
        le=600.0,
        description="Maximum retry delay in seconds"
    )

    # Memory Management
    MEMORY_MAX_MB: float = Field(
        default=500.0,
        ge=50.0,
        le=8000.0,
        description="Maximum application memory budget (MB)"
    )
    MEMORY_WARNING_PCT: float = Field(
        default=80.0,
        ge=10.0,
        le=99.0,
        description="Memory warning threshold (%)"
    )
    MEMORY_CRITICAL_PCT: float = Field(
        default=95.0,
        ge=50.0,
        le=100.0,
        description="Memory critical threshold (%)"
    )

    # Health Check
    HEALTH_CHECK_INTERVAL: int = Field(
        default=30,
        ge=5,
        le=600,
        description="Health check interval (seconds)"
    )

    # Shutdown
    SHUTDOWN_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Graceful shutdown timeout (seconds)"
    )

    # Structured Logging
    LOG_JSON_OUTPUT: bool = Field(
        default=False,
        description="Output logs as JSON"
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("OPENROUTER_API_KEY", pre=True)
    def validate_openrouter_key(cls, v: str, values: dict) -> str:
        """Validate that API key is provided for selected provider."""
        provider = values.get("LLM_PROVIDER", "openrouter")
        
        if provider == "openrouter":
            if not v or v == "your_openrouter_api_key_here":
                raise ValueError(
                    "OPENROUTER_API_KEY must be set when using openrouter provider"
                )
        return v

    @validator("OPENAI_API_KEY", pre=True)
    def validate_openai_key(cls, v: str, values: dict) -> str:
        """Validate that OpenAI API key is provided if using OpenAI provider."""
        provider = values.get("LLM_PROVIDER", "openrouter")
        
        if provider == "openai":
            if not v or v == "your_openai_api_key_here":
                raise ValueError(
                    "OPENAI_API_KEY must be set when using openai provider"
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
        v = int(v) if isinstance(v, str) else v
        chunk_size = values.get("CHUNK_SIZE", 1000)
        chunk_size = int(chunk_size) if isinstance(chunk_size, str) else chunk_size
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
