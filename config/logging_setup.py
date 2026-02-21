import sys
from pathlib import Path

import pandas as pd
from loguru import logger


def setup_logging() -> None:
    """Configure loguru handlers for console (stderr) and file output.

    Removes the default loguru handler, sets custom level colors, adds a
    colorized stderr handler at INFO level, and adds a file handler that
    overwrites ``app.log`` on each run.
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
    """Log the full contents of a DataFrame at INFO level via loguru.

    Temporarily overrides pandas display options so all columns, rows,
    and cell content are visible in the log output.

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
