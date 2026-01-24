"""
Tests for main module.
Ensures proper workflow integration and data pipeline execution.
"""

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from main import main


@pytest.fixture
def sample_raw_dataframe():
    """Fixture providing realistic raw transaction data."""
    return pd.DataFrame(
        {
            "data": ["orlen fuel station", "starbucks coffee"],
            "price": ["-100.0", "-15.0"],
            "month": [1, 1],
            "year": [2023, 2023],
        }
    )


@pytest.fixture
def sample_processed_dataframe():
    """Fixture providing expected processed transaction data."""
    return pd.DataFrame(
        {
            "month": [1, 1],
            "year": [2023, 2023],
            "price": [100.0, 15.0],
            "category": ["FUEL", "COFFEE"],
            "data": ["orlen fuel station", "starbucks coffee"],
        }
    )


@pytest.mark.unit
class TestMainWorkflow:
    """Test suite for main workflow integration."""

    @patch("main.export_cleaned_data")
    @patch("main.export_misc_transactions")
    @patch("main.process_dataframe")
    @patch("main.ipko_import")
    @patch("main.read_transaction_csv")
    @patch("main.setup_logging")
    def test_main_workflow_integration(
        self,
        mock_setup_logging,
        mock_read_csv,
        mock_ipko_import,
        mock_process_df,
        mock_export_misc,
        mock_export_cleaned,
        sample_raw_dataframe,
        sample_processed_dataframe,
    ):
        """
        Integration test verifying complete main workflow.

        Ensures:
        - Correct function call order
        - Proper data flow between functions
        - Expected CSV output format
        - All pipeline components are invoked
        """
        # Arrange
        mock_read_csv.return_value = sample_raw_dataframe
        mock_ipko_import.return_value = sample_raw_dataframe
        mock_process_df.return_value = sample_processed_dataframe

        # Act
        main()

        # Assert - verify call order and arguments
        mock_setup_logging.assert_called_once()
        mock_read_csv.assert_called_once_with(Path("data/demo_ipko.csv"), "cp1250")

        # Verify data flows correctly through pipeline
        pd.testing.assert_frame_equal(mock_ipko_import.call_args[0][0], sample_raw_dataframe)

        pd.testing.assert_frame_equal(mock_process_df.call_args[0][0], sample_raw_dataframe)

        mock_export_misc.assert_called_once()
        pd.testing.assert_frame_equal(mock_export_misc.call_args[0][0], sample_processed_dataframe)

        # Verify export_cleaned_data called with correct parameters
        mock_export_cleaned.assert_called_once_with(sample_processed_dataframe, Path("data/processed_transactions.csv"))

    @patch("main.export_cleaned_data")
    @patch("main.export_misc_transactions")
    @patch("main.process_dataframe")
    @patch("main.ipko_import")
    @patch("main.read_transaction_csv")
    @patch("main.setup_logging")
    def test_main_workflow_with_empty_dataframe(
        self,
        mock_setup_logging,
        mock_read_csv,
        mock_ipko_import,
        mock_process_df,
        mock_export_misc,
        mock_export_cleaned,
    ):
        """Test main workflow with empty DataFrame."""
        # Arrange
        empty_df = pd.DataFrame(columns=["data", "price", "month", "year"])
        mock_read_csv.return_value = empty_df
        mock_ipko_import.return_value = empty_df
        mock_process_df.return_value = empty_df

        # Act
        main()

        # Assert - workflow should complete without errors
        mock_setup_logging.assert_called_once()
        mock_export_misc.assert_called_once()
        mock_export_cleaned.assert_called_once()

    @patch("main.setup_logging")
    @patch("main.read_transaction_csv")
    def test_main_handles_read_csv_failure(self, mock_read_csv, mock_setup_logging):
        """Test main workflow when CSV reading fails."""
        # Arrange
        mock_read_csv.side_effect = FileNotFoundError("File not found")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            main()

        mock_setup_logging.assert_called_once()

    @patch("main.setup_logging")
    @patch("main.read_transaction_csv")
    @patch("main.ipko_import")
    @patch("main.process_dataframe")
    def test_main_handles_processing_failure(
        self,
        mock_process_df,
        mock_ipko_import,
        mock_read_csv,
        mock_setup_logging,
        sample_raw_dataframe,
    ):
        """Test main workflow when data processing fails."""
        # Arrange
        mock_read_csv.return_value = sample_raw_dataframe
        mock_ipko_import.return_value = sample_raw_dataframe
        mock_process_df.side_effect = KeyError("Invalid column")

        # Act & Assert
        with pytest.raises(KeyError):
            main()

        mock_setup_logging.assert_called_once()
