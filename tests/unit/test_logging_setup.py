"""Tests for config.logging_setup module.
Covers handler setup, file and stream error handling, and Loguru configuration.
"""

from unittest.mock import mock_open, patch

import pytest
from loguru import logger

from config.logging_setup import setup_logging


@pytest.mark.unit
class TestSetupLogging:
    """Test suite for setup_logging function."""

    @pytest.fixture(autouse=True)
    def reset_logger(self) -> None:
        """Reset loguru handlers before and after each test."""
        logger.remove()
        yield
        logger.remove()

    def test_setup_logging_success(self):
        """Test successful logging setup.

        Given: no pre-existing loguru handlers and a mocked file open
        When:  setup_logging() is called
        Then:  exactly two handlers are registered and the log file is opened once
        """
        # Arrange
        with patch("builtins.open", mock_open()) as mock_file:
            # Act
            setup_logging()

            # Assert
            # Verify handlers were added (stderr + file)
            # Loguru starts with default handlers, after setup_logging we should have 2
            assert len(logger._core.handlers) == 2

            # Verify file was opened for writing
            mock_file.assert_called_once()
            call_args = mock_file.call_args
            assert "app.log" in call_args[0][0]

    def test_setup_logging_clears_existing_handlers(self):
        """Test that existing handlers are cleared.

        Given: one manually added loguru handler
        When:  setup_logging() is called
        Then:  exactly two handlers remain (stderr + file), replacing the old one
        """
        # Arrange
        logger.add(lambda msg: None)
        _ = len(logger._core.handlers)  # Store initial count for reference

        # Act
        with patch("builtins.open", mock_open()):
            setup_logging()

        # Assert
        # After setup, should have exactly 2 handlers (stderr + file)
        assert len(logger._core.handlers) == 2

    def test_setup_logging_info_message_logged(self):
        """Test that setup completion message is logged.

        Given: mocked file open and a patched logger.info
        When:  setup_logging() is called
        Then:  logger.info is called with the expected confirmation message
        """
        # Arrange
        with patch("builtins.open", mock_open()), patch.object(logger, "info") as mock_info:
            # Act
            setup_logging()

        # Assert
        mock_info.assert_called_with("Logging initialized successfully")

    def test_setup_logging_file_handler_error(self):
        """Test error handling when file handler creation fails.

        Given: opening a file raises PermissionError
        When:  setup_logging() is called
        Then:  the error message is printed and the function does not raise
        """
        # Arrange
        with (
            patch("builtins.open", side_effect=PermissionError("Cannot create file")),
            patch("builtins.print") as mock_print,
        ):
            # Act
            setup_logging()

        # Assert
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Error setting up logging:" in call_args
        assert "Cannot create file" in call_args

    def test_setup_logging_stream_handler_error(self):
        """Test error handling when logger.add fails.

        Given: logger.add raises a generic Exception
        When:  setup_logging() is called
        Then:  the error message is printed and the function does not raise
        """
        # Arrange
        with (
            patch("loguru.logger.add", side_effect=Exception("Handler error")),
            patch("builtins.print") as mock_print,
        ):
            # Act
            setup_logging()

        # Assert
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Error setting up logging:" in call_args
        assert "Handler error" in call_args

    def test_setup_logging_no_existing_handlers(self):
        """Test setup when no existing handlers are present.

        Given: all loguru handlers have been removed
        When:  setup_logging() is called
        Then:  exactly two handlers are registered (stderr + file)
        """
        # Arrange
        logger.remove()

        # Act
        with patch("builtins.open", mock_open()):
            setup_logging()

        # Assert
        assert len(logger._core.handlers) == 2
