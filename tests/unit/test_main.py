"""
Tests for main module.
Ensures proper workflow integration and data pipeline execution.
"""

from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from main import main


@pytest.fixture
def main_raw_dataframe() -> pd.DataFrame:
    """Fixture providing minimal raw transaction data for main() pipeline mocking."""
    return pd.DataFrame(
        {
            "data": ["orlen fuel station", "starbucks coffee"],
            "price": ["-100.0", "-15.0"],
            "month": [1, 1],
            "year": [2023, 2023],
        }
    )


@pytest.fixture
def main_processed_dataframe() -> pd.DataFrame:
    """Fixture providing expected processed transaction data for main() pipeline mocking."""
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

    def test_main_workflow_integration(
        self,
        mocker: MockerFixture,
        main_raw_dataframe: pd.DataFrame,
        main_processed_dataframe: pd.DataFrame,
    ) -> None:
        """
        Integration test verifying complete main workflow.

        Ensures:
        - Correct function call order
        - Proper data flow between functions
        - Expected CSV output format
        - All pipeline components are invoked
        """
        mock_setup_logging = mocker.patch("main.setup_logging")
        mock_read_csv = mocker.patch("main.read_transaction_csv")
        mock_ipko_import = mocker.patch("main.ipko_import")
        mock_process_df = mocker.patch("main.process_dataframe")
        mock_export_misc = mocker.patch("main.export_misc_transactions")
        mock_export_cleaned = mocker.patch("main.export_cleaned_data")

        # Arrange
        mock_read_csv.return_value = main_raw_dataframe
        mock_ipko_import.return_value = main_raw_dataframe
        mock_process_df.return_value = main_processed_dataframe

        # Act
        main()

        # Assert - verify call order and arguments
        mock_setup_logging.assert_called_once()
        mock_read_csv.assert_called_once_with(Path("data/demo_ipko.csv"), "cp1250")

        # Verify data flows correctly through pipeline
        pd.testing.assert_frame_equal(mock_ipko_import.call_args[0][0], main_raw_dataframe)
        pd.testing.assert_frame_equal(mock_process_df.call_args[0][0], main_raw_dataframe)

        mock_export_misc.assert_called_once()
        pd.testing.assert_frame_equal(mock_export_misc.call_args[0][0], main_processed_dataframe)

        # Verify export_cleaned_data called with correct parameters
        mock_export_cleaned.assert_called_once_with(main_processed_dataframe, Path("data/processed_transactions.csv"))

    def test_main_workflow_with_empty_dataframe(self, mocker: MockerFixture) -> None:
        """Test main workflow with empty DataFrame."""
        mock_setup_logging = mocker.patch("main.setup_logging")
        mock_read_csv = mocker.patch("main.read_transaction_csv")
        mock_ipko_import = mocker.patch("main.ipko_import")
        mock_process_df = mocker.patch("main.process_dataframe")
        mock_export_misc = mocker.patch("main.export_misc_transactions")
        mock_export_cleaned = mocker.patch("main.export_cleaned_data")

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

    def test_main_handles_read_csv_failure(self, mocker: MockerFixture) -> None:
        """Test main workflow when CSV reading fails."""
        mock_setup_logging = mocker.patch("main.setup_logging")
        mock_read_csv = mocker.patch("main.read_transaction_csv")

        # Arrange
        mock_read_csv.side_effect = FileNotFoundError("File not found")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            main()

        mock_setup_logging.assert_called_once()

    def test_main_handles_processing_failure(
        self,
        mocker: MockerFixture,
        main_raw_dataframe: pd.DataFrame,
    ) -> None:
        """Test main workflow when data processing fails."""
        mock_setup_logging = mocker.patch("main.setup_logging")
        mock_read_csv = mocker.patch("main.read_transaction_csv")
        mock_ipko_import = mocker.patch("main.ipko_import")
        mock_process_df = mocker.patch("main.process_dataframe")

        # Arrange
        mock_read_csv.return_value = main_raw_dataframe
        mock_ipko_import.return_value = main_raw_dataframe
        mock_process_df.side_effect = KeyError("Invalid column")

        # Act & Assert
        with pytest.raises(KeyError):
            main()

        mock_setup_logging.assert_called_once()
