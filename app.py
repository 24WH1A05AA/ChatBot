"""
Application entry point for College FAQ Chatbot.

Initializes the application, loads configuration,
sets up logging, and starts the chatbot service.
Integrates optimization engine for caching, parallel execution,
batch processing, health checks, and graceful shutdown.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from config import Settings, get_settings
from core.logger import setup_logging, get_logger
from core.optimization import (
    OptimizationEngine,
    get_optimization_engine,
    HealthMonitor,
    HealthStatus,
)

logger = get_logger(__name__)


class Application:
    """
    Main application class with optimization engine integration.
    
    Manages application lifecycle, initialization, and graceful shutdown
    of all optimization components.
    """

    def __init__(self) -> None:
        """Initialize application."""
        self.settings: Optional[Settings] = None
        self.optimization_engine: Optional[OptimizationEngine] = None
        self._shutdown_complete: bool = False

    def setup_application(self) -> Settings:
        """
        Initialize application and load configuration.
        
        Returns:
            Settings: Application configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            settings = get_settings()
            self.settings = settings
            
            # Setup logging
            setup_logging(
                level=settings.LOG_LEVEL,
                log_file=settings.LOG_FILE,
                is_debug=settings.DEBUG,
            )
            
            logger.info(f"Application starting in {settings.ENVIRONMENT} environment")
            logger.debug(f"Configuration loaded: {settings.ENVIRONMENT}")
            
            # Create necessary directories
            settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            settings.CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
            settings.PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
            
            # -----------------------------------------------------------------
            # Initialize Optimization Engine
            # -----------------------------------------------------------------
            if settings.CACHE_ENABLED:
                optimization_config = {
                    # Caching
                    "cache.embedding.max_size": settings.CACHE_EMBEDDING_MAX_SIZE,
                    "cache.embedding.ttl": settings.CACHE_EMBEDDING_TTL,
                    "cache.embedding.max_memory_mb": settings.CACHE_MAX_MEMORY_MB / 4,
                    "cache.llm.max_size": settings.CACHE_LLM_MAX_SIZE,
                    "cache.llm.ttl": settings.CACHE_LLM_TTL,
                    "cache.llm.max_memory_mb": settings.CACHE_MAX_MEMORY_MB / 4,
                    "cache.crawl.max_size": settings.CACHE_CRAWL_MAX_SIZE,
                    "cache.crawl.ttl": settings.CACHE_CRAWL_TTL,
                    "cache.crawl.max_memory_mb": settings.CACHE_MAX_MEMORY_MB / 4,
                    "cache.file.max_size": settings.CACHE_FILE_MAX_SIZE,
                    "cache.file.ttl": settings.CACHE_FILE_TTL,
                    "cache.file.max_memory_mb": settings.CACHE_MAX_MEMORY_MB / 4,
                    
                    # Parallel Execution
                    "parallel.embedding_workers": settings.PARALLEL_EMBEDDING_WORKERS,
                    "parallel.embedding_rate_limit": settings.EMBEDDING_RATE_LIMIT,
                    "parallel.crawl_workers": settings.PARALLEL_CRAWL_WORKERS,
                    "parallel.crawl_rate_limit": settings.CRAWL_RATE_LIMIT,
                    "parallel.general_workers": settings.PARALLEL_GENERAL_WORKERS,
                    
                    # Batch Processing
                    "batch.default_size": settings.BATCH_SIZE,
                    "batch.max_concurrent": settings.BATCH_MAX_CONCURRENT,
                    "batch.timeout": settings.BATCH_TIMEOUT,
                    
                    # Retry
                    "retry.embedding.max_retries": settings.RETRY_MAX_ATTEMPTS,
                    "retry.embedding.base_delay": settings.RETRY_BASE_DELAY,
                    "retry.embedding.max_delay": settings.RETRY_MAX_DELAY,
                    "retry.crawl.max_retries": settings.RETRY_MAX_ATTEMPTS,
                    "retry.crawl.base_delay": settings.RETRY_BASE_DELAY * 2,
                    "retry.crawl.max_delay": settings.RETRY_MAX_DELAY,
                    
                    # Memory
                    "memory.max_mb": settings.MEMORY_MAX_MB,
                    "memory.warning_pct": settings.MEMORY_WARNING_PCT,
                    "memory.critical_pct": settings.MEMORY_CRITICAL_PCT,
                    
                    # Health
                    "health.check_interval": settings.HEALTH_CHECK_INTERVAL,
                    
                    # Shutdown
                    "shutdown.timeout": settings.SHUTDOWN_TIMEOUT,
                    
                    # Logging
                    "logging.json_output": settings.LOG_JSON_OUTPUT,
                    "logging.min_level": settings.LOG_LEVEL,
                }
                
                self.optimization_engine = get_optimization_engine(optimization_config)
                logger.info("Optimization engine initialized")
                
                # Register health checks for core components
                self._register_health_checks()
            else:
                logger.info("Caching disabled by configuration")
            
            logger.info("Application setup completed successfully")
            return settings
            
        except Exception as e:
            logger.error(f"Application setup failed: {str(e)}")
            raise

    def _register_health_checks(self) -> None:
        """Register health checks for application components."""
        if not self.optimization_engine:
            return
        
        health_monitor = self.optimization_engine.health_monitor
        
        # Check: OpenAI API health
        def check_openai() -> bool:
            try:
                import openai
                # Simple connectivity check - list models
                openai.Model.list()
                return True
            except Exception:
                return False
        
        health_monitor.register_component_check(
            "openai_api",
            ping_fn=check_openai,
            details_fn=lambda: {
                "model": self.settings.OPENAI_MODEL if self.settings else "unknown",
            },
        )
        
        # Check: ChromaDB health
        def check_chromadb() -> bool:
            try:
                from vectorstore.vectorstore import VectorStore
                vs = VectorStore()
                stats = vs.get_statistics()
                return "total_embeddings" in stats
            except Exception:
                return False
        
        health_monitor.register_component_check(
            "chromadb",
            ping_fn=check_chromadb,
            details_fn=lambda: {
                "path": str(self.settings.CHROMA_DB_PATH) if self.settings else "unknown",
            },
        )
        
        # Check: Disk space
        def check_disk() -> bool:
            try:
                import shutil
                usage = shutil.disk_usage(self.settings.PERSIST_DIRECTORY if self.settings else ".")
                free_gb = usage.free / (1024 ** 3)
                return free_gb > 0.5  # At least 500MB free
            except Exception:
                return True  # Skip if can't check
        
        health_monitor.register_component_check(
            "disk_space",
            ping_fn=check_disk,
        )
        
        # Check: Cache health
        def check_cache() -> bool:
            if self.optimization_engine:
                caches = self.optimization_engine.get_all_stats().get("caches", {})
                return len(caches) > 0
            return True
        
        health_monitor.register_component_check(
            "cache_system",
            ping_fn=check_cache,
        )
        
        logger.info("Registered 4 health checks")

    async def shutdown(self, reason: str = "application shutdown") -> None:
        """
        Graceful application shutdown.
        
        Args:
            reason: Reason for shutdown
        """
        if self._shutdown_complete:
            return
        
        logger.info(f"Shutting down application: {reason}")
        
        if self.optimization_engine:
            try:
                result = await self.optimization_engine.shutdown(reason=reason)
                logger.info(
                    f"Optimization engine shutdown: "
                    f"{result.get('components_cleaned', 0)} components cleaned"
                )
            except Exception as e:
                logger.error(f"Error during optimization engine shutdown: {e}")
        
        self._shutdown_complete = True
        logger.info("Application shutdown complete")


# Global application instance
_app: Optional[Application] = None


def get_application() -> Application:
    """
    Get or create the global application instance.
    
    Returns:
        Application instance
    """
    global _app
    if _app is None:
        _app = Application()
    return _app


def setup_application() -> Settings:
    """
    Initialize application and load configuration.
    
    Returns:
        Settings: Application configuration
    """
    app = get_application()
    return app.setup_application()


async def async_main() -> int:
    """
    Async main entry point with full optimization support.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        app = get_application()
        settings = app.setup_application()
        
        logger.info("College FAQ Chatbot initialized successfully")
        logger.info(f"Starting Streamlit dashboard...")
        
        # Start background tasks for optimization engine
        if app.optimization_engine:
            logger.info("Starting background optimization tasks...")
            await app.optimization_engine.start_background_tasks()
        
        # Register shutdown handler
        app.optimization_engine.shutdown_handler.register(
            "application",
            lambda: app.shutdown("application exit"),
        )
        
        # Log optimization stats
        if app.optimization_engine:
            stats = app.optimization_engine.get_all_stats()
            cache_count = len(stats.get("caches", {}))
            executor_count = len(stats.get("executors", {}))
            logger.info(
                f"Optimization status: {cache_count} caches, "
                f"{executor_count} executors, "
                f"memory: {stats.get('memory', {}).get('usage_pct', 'N/A')}%"
            )
        
        # Keep application running
        try:
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour intervals
        except asyncio.CancelledError:
            pass
        
        # Graceful shutdown
        await app.shutdown("application exit")
        
        return 0
        
    except Exception as e:
        logger.error(f"Application failed: {str(e)}", exc_info=True)
        return 1


def main() -> int:
    """
    Main application entry point (sync wrapper).
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        app = get_application()
        settings = app.setup_application()
        
        logger.info("College FAQ Chatbot initialized successfully")
        logger.info(f"Starting Streamlit dashboard...")
        
        # Log optimization status
        if app.optimization_engine:
            stats = app.optimization_engine.get_all_stats()
            logger.info(
                f"Optimization enabled: "
                f"{len(stats.get('caches', {}))} caches, "
                f"{len(stats.get('executors', {}))} executors"
            )
        
        logger.info(
            "Run 'streamlit run streamlit/dashboard.py' to start the dashboard"
        )
        
        return 0
        
    except Exception as e:
        logger.error(f"Application failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Check if we should run async
    if "--async" in sys.argv:
        sys.exit(asyncio.run(async_main()))
    else:
        sys.exit(main())
