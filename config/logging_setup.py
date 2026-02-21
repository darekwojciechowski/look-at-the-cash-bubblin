import sys
from pathlib import Path

import pandas as pd
from loguru import logger


def setup_logging() -> None:
    """Configure logging with Loguru - Professional format with colors."""
    try:
        # Remove default handler
        logger.remove()

        # Configure custom colors for levels
        logger.level("DEBUG", color="<cyan>")
        logger.level("INFO", color="<white>")
        logger.level("SUCCESS", color="<green>")
        logger.level("WARNING", color="<yellow>")
        logger.level("ERROR", color="<red>")
        logger.level("CRITICAL", color="<RED><bold>")

        # Add console handler with professional colorful format
        log_format = (
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            sys.stderr,
            format=log_format,
            level="INFO",
            colorize=True,
        )

        # Add file handler with detailed format (no colors for file)
        logger.add(
            Path("app.log"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {function}:{line} - {message}",
            level="INFO",
            mode="w",
            encoding="utf-8",
        )

        # Test log to confirm setup
        logger.info("Logging initialized successfully")
    except Exception as e:
        print(f"Error setting up logging: {e}")


def log_dataframe_preview(df: pd.DataFrame) -> None:
    """Log a full DataFrame preview using loguru, with all columns and rows visible."""
    with pd.option_context(
        "display.max_colwidth",
        None,
        "display.max_columns",
        None,
        "display.width",
        None,
        "display.max_rows",
        None,
    ):
        logger.info("[DATA] Processed DataFrame preview:\n{}", df.to_string())
