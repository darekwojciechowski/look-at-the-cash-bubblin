"""
Tests for config.logging_setup module.
Ensures proper logging configuration and error handling with Loguru.
"""

from unittest.mock import mock_open, patch

import pytest
from loguru import logger

from config.logging_setup import setup_logging


@pytest.mark.unit
class TestSetupLogging:
    """Test suite for setup_logging function."""

    def setup_method(self):
        """Reset logging configuration before each test."""
        # Remove all loguru handlers
        logger.remove()

    def teardown_method(self):
        """Clean up after each test."""
        # Remove all loguru handlers
        logger.remove()

    def test_setup_logging_success(self):
        """Test successful logging setup."""
        with patch("builtins.open", mock_open()) as mock_file:
            setup_logging()

            # Verify handlers were added (stderr + file)
            # Loguru starts with default handlers, after setup_logging we should have 2
            assert len(logger._core.handlers) == 2

            # Verify file was opened for writing
            mock_file.assert_called_once()
            call_args = mock_file.call_args
            assert "app.log" in call_args[0][0]

    def test_setup_logging_clears_existing_handlers(self):
        """Test that existing handlers are cleared."""
        # Add a handler manually
        logger.add(lambda msg: None)
        _ = len(logger._core.handlers)  # Store initial count for reference

        with patch("builtins.open", mock_open()):
            setup_logging()

            # After setup, should have exactly 2 handlers (stderr + file)
            assert len(logger._core.handlers) == 2

    def test_setup_logging_info_message_logged(self):
        """Test that setup completion message is logged."""
        with patch("builtins.open", mock_open()), patch.object(logger, "info") as mock_info:
            setup_logging()
            mock_info.assert_called_with("Logging initialized successfully")

    def test_setup_logging_file_handler_error(self):
        """Test error handling when file handler creation fails."""
        with (
            patch("builtins.open", side_effect=PermissionError("Cannot create file")),
            patch("builtins.print") as mock_print,
        ):
            setup_logging()

            # Verify error is printed
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Error setting up logging:" in call_args
            assert "Cannot create file" in call_args

    def test_setup_logging_stream_handler_error(self):
        """Test error handling when logger.add fails."""
        with (
            patch("loguru.logger.add", side_effect=Exception("Handler error")),
            patch("builtins.print") as mock_print,
        ):
            setup_logging()

            # Verify error is printed
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Error setting up logging:" in call_args
            assert "Handler error" in call_args

    def test_setup_logging_no_existing_handlers(self):
        """Test setup when no existing handlers are present."""
        # Remove all handlers
        logger.remove()

        with patch("builtins.open", mock_open()):
            setup_logging()

            # Should have exactly 2 handlers (stderr + file)
            assert len(logger._core.handlers) == 2
