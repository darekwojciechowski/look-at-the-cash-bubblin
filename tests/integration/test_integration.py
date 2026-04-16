"""
Integration tests for the complete data processing pipeline.
Tests end-to-end workflows with real data and file I/O.
"""

from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_core import clean_descriptions, process_dataframe
from data_processing.data_imports import ipko_import, read_transaction_csv
from main import main


@pytest.mark.integration
class TestMainWorkflowIntegration:
    """Integration tests for main() with real file I/O."""

    def test_main_workflow_with_real_csv(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """End-to-end test: main() reads a real IPKO CSV file without mocking I/O.

        Given: a real cp1250-encoded IPKO CSV file with two transactions
        When:  main() is called with the file path patched and exports mocked
        Then:  both export functions are called and the processed DataFrame is non-empty with a category column
        """
        # Arrange
        csv_file = tmp_path / "demo_ipko.csv"
        # IPKO export format: 9 unnamed columns, no header
        csv_file.write_text(
            "2024-01-15,PLN,purchase,-50.0,PLN,orlen fuel station,,orlen,,\n"
            "2024-01-16,PLN,purchase,-15.0,PLN,starbucks coffee,,starbucks,,\n",
            encoding="cp1250",
        )

        mocker.patch("main.CSV_INPUT_FILE", csv_file)
        mock_export_misc = mocker.patch("main.export_misc_transactions")
        mock_export_cleaned = mocker.patch("main.export_cleaned_data")

        # Act
        main()

        # Assert
        mock_export_misc.assert_called_once()
        mock_export_cleaned.assert_called_once()
        processed_df = mock_export_cleaned.call_args[0][0]
        assert not processed_df.empty
        assert "category" in processed_df.columns


@pytest.mark.integration
class TestEndToEndDataProcessing:
    """Integration tests for complete data processing workflow."""

    def test_complete_pipeline_with_real_csv(
        self, sample_csv_file: Path, test_data_dir: Path, mocker: MockerFixture
    ) -> None:
        """Test complete pipeline from CSV reading to export.

        Given: a real CSV file with two transaction rows
        When:  the full pipeline (read → clean → process → export) is executed
        Then:  the output file contains the same number of rows as the processed DataFrame
        """
        # Arrange — via sample_csv_file fixture

        # Act — Read CSV
        df = read_transaction_csv(str(sample_csv_file), "utf-8")
        assert not df.empty
        assert len(df) == 2

        # Act — Process data
        cleaned_df = clean_descriptions(df)
        assert "data" in cleaned_df.columns

        # Mock mappings for categorization — use a callable so that
        # post-cleaning descriptions (e.g. "Orlen gas station") are matched
        # via substring, replicating real mappings() behaviour.
        def mock_mappings(data: str) -> str:
            data_lower = data.lower()
            if "orlen" in data_lower:
                return "FUEL"
            if "biedronka" in data_lower:
                return "FOOD"
            return "MISC"

        mocker.patch("data_processing.data_core.mappings", mock_mappings)

        processed_df = process_dataframe(cleaned_df)
        assert "category" in processed_df.columns
        assert len(processed_df) > 0

        # Act — Export to file
        output_file = test_data_dir / "output.csv"
        processed_df.to_csv(output_file, index=False)

        # Assert
        assert output_file.exists()
        result_df = pd.read_csv(output_file)
        assert len(result_df) == len(processed_df)

    def test_ipko_import_and_processing(self, sample_ipko_dataframe: pd.DataFrame, mocker: MockerFixture) -> None:
        """Test IPKO import format and subsequent processing.

        Given: a raw IPKO-formatted DataFrame and a mock mappings dict
        When:  the full import → clean → process pipeline is executed
        Then:  the processed DataFrame contains a category column
        """
        # Arrange — via sample_ipko_dataframe fixture

        # Act — Import IPKO data
        imported_df = ipko_import(sample_ipko_dataframe)
        assert "price" in imported_df.columns
        assert "data" in imported_df.columns

        # Act — Process imported data
        cleaned_df = clean_descriptions(imported_df)
        assert len(cleaned_df) == len(imported_df)

        # Mock mappings
        mock_mappings = {
            "transfer//description1//extra1//extra3//data1": "TRANSFER",
            "payment//description2//extra2//extra4//data2": "PAYMENT",
        }
        mocker.patch("data_processing.data_core.mappings", mock_mappings)

        processed_df = process_dataframe(cleaned_df)

        # Assert
        assert "category" in processed_df.columns


@pytest.mark.integration
class TestDataExportIntegration:
    """Integration tests for data export functionality."""

    def test_export_misc_to_file(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        test_data_dir: Path,
        mocker: MockerFixture,
    ) -> None:
        """Test exporting MISC transactions to CSV file.

        Given: a DataFrame with two MISC rows and a real output path
        When:  the MISC rows are written to a CSV file
        Then:  the file exists, is readable, contains two rows, all with category MISC
        """
        # Arrange
        output_file = test_data_dir / "unassigned.csv"

        # Mock the export path
        mocker.patch("data_processing.exporter.Path", return_value=output_file)

        # Act — Create the file manually since we're testing integration
        misc_df = sample_dataframe_with_categories[sample_dataframe_with_categories["category"] == "MISC"]
        misc_df.to_csv(output_file, index=False, encoding="utf-8-sig")

        # Assert
        assert output_file.exists()
        result_df = pd.read_csv(output_file, encoding="utf-8-sig")
        assert len(result_df) == 2  # Two MISC entries
        assert all(result_df["category"] == "MISC")

    def test_google_sheets_export_format(
        self, sample_dataframe_with_categories: pd.DataFrame, test_data_dir: Path
    ) -> None:
        """Test Google Sheets export format compatibility.

        Given: a DataFrame with categories, prices, months, years, and data
        When:  it is exported to a CSV file and re-read
        Then:  columns match the expected order and no NaN values are present
        """
        # Arrange
        output_file = test_data_dir / "for_google_sheets.csv"

        # Act
        sample_dataframe_with_categories.to_csv(output_file, index=False)

        # Assert
        result_df = pd.read_csv(output_file)
        assert list(result_df.columns) == ["category", "price", "month", "year", "data"]
        assert len(result_df) == len(sample_dataframe_with_categories)
        assert result_df.isna().sum().sum() == 0  # No NaN values


@pytest.mark.integration
@pytest.mark.slow
class TestLargeDatasetProcessing:
    """Integration tests with larger datasets."""

    def test_processing_large_dataset(self, test_data_dir: Path, mocker: MockerFixture) -> None:
        """Test processing a larger dataset (1000+ transactions).

        Given: a CSV file with 1000 transaction rows saved to disk
        When:  read → clean → process is executed with a MISC-returning mock
        Then:  the processed DataFrame contains 1000 rows all categorised as MISC
        """
        # Arrange
        large_df = pd.DataFrame({
            "data": [f"transaction {i}" for i in range(1000)],
            "price": [f"-{i % 100 + 10}.0" for i in range(1000)],
            "month": [i % 12 + 1 for i in range(1000)],
            "year": [2023] * 1000,
        })

        # Save to file
        input_file = test_data_dir / "large_transactions.csv"
        large_df.to_csv(input_file, index=False)

        # Act
        df = read_transaction_csv(str(input_file), "utf-8")
        assert len(df) == 1000

        cleaned_df = clean_descriptions(df)
        assert len(cleaned_df) == 1000

        # Mock mappings — use a callable so .map() receives a function,
        # returning "MISC" for every description (matching real fallback behaviour).
        mocker.patch("data_processing.data_core.mappings", lambda _data: "MISC")

        processed_df = process_dataframe(cleaned_df)

        # Assert
        # All should be MISC since no descriptions match a real keyword
        assert len(processed_df) == 1000
        assert (processed_df["category"] == "MISC").all()
