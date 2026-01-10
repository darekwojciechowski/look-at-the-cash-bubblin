from loguru import logger
import sys


def setup_logging() -> None:
    """Configure logging with Loguru - Professional format with colors."""
    try:
        # Remove default handler
        logger.remove()

        # Add console handler with professional colorful format
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True
        )

        # Add file handler with detailed format (no colors for file)
        logger.add(
            'app.log',
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {function}:{line} - {message}",
            level="INFO",
            mode='w',
            encoding='utf-8'
        )

        # Test log to confirm setup
        logger.info("Logging initialized successfully")
    except Exception as e:
        print(f"Error setting up logging: {e}")
