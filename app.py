"""
Application entry point for College FAQ Chatbot.

Initializes the application, loads configuration,
sets up logging, and starts the chatbot service.
"""

import sys
from pathlib import Path

from config import Settings, get_settings
from core.logger import setup_logging, get_logger

logger = get_logger(__name__)


def setup_application() -> Settings:
    """
    Initialize application and load configuration.
    
    Returns:
        Settings: Application configuration
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    try:
        settings = get_settings()
        
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
        
        logger.info("Application setup completed successfully")
        return settings
        
    except Exception as e:
        logger.error(f"Application setup failed: {str(e)}")
        raise


def main() -> int:
    """
    Main application entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        settings = setup_application()
        
        logger.info("College FAQ Chatbot initialized successfully")
        logger.info(f"Starting Streamlit dashboard...")
        
        # Note: In production, use:
        # streamlit run streamlit/dashboard.py
        
        return 0
        
    except Exception as e:
        logger.error(f"Application failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
