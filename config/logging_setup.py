import logging


def setup_logging():
    """Configure logging for the script."""
    try:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Clear existing handlers to avoid duplicate logs
        if logger.hasHandlers():
            logger.handlers.clear()

        # StreamHandler for terminal output
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(
            '%(message)s'))  # Shortened format
        logger.addHandler(stream_handler)

        # FileHandler for logging to a file
        file_handler = logging.FileHandler(
            'app.log', mode='w', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(message)s'))  # Shortened format
        logger.addHandler(file_handler)

        # Test log to confirm setup
        logger.info("Logging setup complete. Test log message.")
    except Exception as e:
        print(f"Error setting up logging: {e}")
