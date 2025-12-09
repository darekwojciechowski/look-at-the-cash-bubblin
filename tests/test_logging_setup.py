"""
Tests for config.logging_setup module.
Ensures proper logging configuration and error handling.
"""

import logging
from unittest.mock import patch, MagicMock, mock_open
from config.logging_setup import setup_logging


class TestSetupLogging:
    """Test suite for setup_logging function."""

    def setup_method(self):
        """Reset logging configuration before each test."""
        # Clear all existing handlers
        logger = logging.getLogger()
        logger.handlers.clear()
        logger.setLevel(logging.WARNING)  # Reset to default level

    def teardown_method(self):
        """Clean up after each test."""
        # Clear all handlers again
        logger = logging.getLogger()
        logger.handlers.clear()

    def test_setup_logging_success(self):
        """Test successful logging setup."""
        with patch('builtins.open', mock_open()) as mock_file:
            setup_logging()

            logger = logging.getLogger()

            # Verify logger level is set to INFO
            assert logger.level == logging.INFO

            # Verify two handlers are added (stream and file)
            assert len(logger.handlers) == 2

            # Verify handler types
            handler_types = [
                type(handler).__name__ for handler in logger.handlers]
            assert 'StreamHandler' in handler_types
            assert 'FileHandler' in handler_types

            # Verify file was opened for writing (check if called with app.log in args)
            mock_file.assert_called_once()
            call_args = mock_file.call_args
            # filename should contain app.log
            assert 'app.log' in call_args[0][0]

    def test_setup_logging_clears_existing_handlers(self):
        """Test that existing handlers are cleared."""
        logger = logging.getLogger()

        # Clear all existing handlers first (including pytest handlers)
        initial_handler_count = len(logger.handlers)

        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        logger.addHandler(dummy_handler)

        # Verify handler was added
        assert len(logger.handlers) == initial_handler_count + 1

        with patch('builtins.open', mock_open()):
            setup_logging()

            # Verify handlers are cleared and new ones added (2 new handlers)
            assert len(logger.handlers) == 2
            assert dummy_handler not in logger.handlers

    def test_setup_logging_formatter_configuration(self):
        """Test that handlers have correct formatter."""
        with patch('builtins.open', mock_open()):
            setup_logging()

            logger = logging.getLogger()

            for handler in logger.handlers:
                formatter = handler.formatter
                assert formatter is not None
                # Test that formatter format is the expected shortened format
                assert formatter._fmt == '%(message)s'

    def test_setup_logging_info_message_logged(self):
        """Test that setup completion message is logged."""
        with patch('builtins.open', mock_open()):
            with patch.object(logging.getLogger(), 'info') as mock_info:
                setup_logging()
                mock_info.assert_called_with(
                    "Logging setup complete. Test log message.")

    def test_setup_logging_file_handler_error(self):
        """Test error handling when file handler creation fails."""
        with patch('builtins.open', side_effect=PermissionError("Cannot create file")):
            with patch('builtins.print') as mock_print:
                setup_logging()

                # Verify error is printed
                mock_print.assert_called_once()
                call_args = mock_print.call_args[0][0]
                assert "Error setting up logging:" in call_args
                assert "Cannot create file" in call_args

    def test_setup_logging_stream_handler_error(self):
        """Test error handling when stream handler creation fails."""
        with patch('logging.StreamHandler', side_effect=Exception("Stream error")):
            with patch('builtins.print') as mock_print:
                setup_logging()

                # Verify error is printed
                mock_print.assert_called_once()
                call_args = mock_print.call_args[0][0]
                assert "Error setting up logging:" in call_args
                assert "Stream error" in call_args

    def test_setup_logging_no_existing_handlers(self):
        """Test setup when no existing handlers are present."""
        logger = logging.getLogger()
        # Ensure no handlers exist
        logger.handlers.clear()

        with patch('builtins.open', mock_open()):
            setup_logging()

            # Should still add handlers successfully
            assert len(logger.handlers) == 2

    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    def test_setup_logging_handler_configuration(self, mock_stream_handler, mock_file_handler):
        """Test that handlers are configured correctly."""
        mock_stream_instance = MagicMock()
        mock_file_instance = MagicMock()
        mock_stream_handler.return_value = mock_stream_instance
        mock_file_handler.return_value = mock_file_instance

        with patch('builtins.open', mock_open()):
            setup_logging()

            # Verify handlers were created with correct parameters
            mock_file_handler.assert_called_once_with(
                'app.log', mode='w', encoding='utf-8')
            mock_stream_handler.assert_called_once()

            # Verify formatters were set
            mock_stream_instance.setFormatter.assert_called_once()
            mock_file_instance.setFormatter.assert_called_once()

            # Verify handlers were added to logger
            logger = logging.getLogger()
            assert mock_stream_instance in logger.handlers
            assert mock_file_instance in logger.handlers
