"""Logging configuration for the application.

Provides two public functions:

- `setup_logging` — initializes loguru with a colorized stderr handler and a
  plain-text file handler that overwrites ``app.log`` on each run.
- `log_dataframe_preview` — logs the full contents of a pandas DataFrame at
  INFO level using temporary display settings that show all rows and columns.

Call `setup_logging` once at application startup before any other logging
calls.
"""

import sys
from pathlib import Path

import pandas as pd
from loguru import logger


def setup_logging() -> None:
    """Configure loguru with a colorized stderr handler and a file handler.

    Writes INFO-and-above records to stderr and to ``app.log`` in the current
    working directory. Truncates ``app.log`` on each run. On failure, prints
    the error to stdout instead of raising.
    """
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

        # Add colorized console handler
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

        # Confirm that logging is active
        logger.info("Logging initialized successfully")
    except Exception as e:
        print(f"Error setting up logging: {e}")


def log_dataframe_preview(df: pd.DataFrame) -> None:
    """Log the full contents of a DataFrame at INFO level.

    Temporarily disables pandas display truncation so all rows and columns
    appear in the log output.

    Args:
        df: DataFrame to log.
    """
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
