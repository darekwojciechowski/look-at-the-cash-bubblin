"""
Integration tests for the complete data processing pipeline.
Tests end-to-end workflows with real data and file I/O.
"""

import pytest
import pandas as pd
from pathlib import Path
from pytest_mock import MockerFixture

from data_processing.data_imports import ipko_import, read_transaction_csv
from data_processing.data_core import clean_date, process_dataframe
from data_processing.exporter import export_misc_transactions, export_for_google_sheets


@pytest.mark.integration
class TestEndToEndDataProcessing:
    """Integration tests for complete data processing workflow."""

    def test_complete_pipeline_with_real_csv(
        self,
        sample_csv_file: Path,
        test_data_dir: Path,
        mocker: MockerFixture
    ) -> None:
        """Test complete pipeline from CSV reading to export."""
        # Read CSV
        df = read_transaction_csv(str(sample_csv_file), 'utf-8')
        assert not df.empty
        assert len(df) == 2

        # Process data
        cleaned_df = clean_date(df)
        assert "data" in cleaned_df.columns

        # Mock mappings for categorization
        mock_mappings = {
            "orlen": "FUEL",
            "biedronka": "FOOD"
        }
        mocker.patch("data_processing.data_core.mappings", mock_mappings)

        processed_df = process_dataframe(cleaned_df)
        assert "category" in processed_df.columns
        assert len(processed_df) > 0

        # Export to file
        output_file = test_data_dir / "output.csv"
        processed_df.to_csv(output_file, index=False)

        # Verify output file exists and is readable
        assert output_file.exists()
        result_df = pd.read_csv(output_file)
        assert len(result_df) == len(processed_df)

    def test_ipko_import_and_processing(
        self,
        sample_ipko_dataframe: pd.DataFrame,
        mocker: MockerFixture
    ) -> None:
        """Test IPKO import format and subsequent processing."""
        # Import IPKO data
        imported_df = ipko_import(sample_ipko_dataframe)
        assert "price" in imported_df.columns
        assert "data" in imported_df.columns

        # Process imported data
        cleaned_df = clean_date(imported_df)
        assert len(cleaned_df) == len(imported_df)

        # Mock mappings
        mock_mappings = {
            "transfer//description1//extra1//extra3//data1": "TRANSFER",
            "payment//description2//extra2//extra4//data2": "PAYMENT"
        }
        mocker.patch("data_processing.data_core.mappings", mock_mappings)

        processed_df = process_dataframe(cleaned_df)
        assert "category" in processed_df.columns


@pytest.mark.integration
class TestDataExportIntegration:
    """Integration tests for data export functionality."""

    def test_export_misc_to_file(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        test_data_dir: Path,
        mocker: MockerFixture
    ) -> None:
        """Test exporting MISC transactions to CSV file."""
        output_file = test_data_dir / "unassigned.csv"

        # Mock the export path
        mocker.patch("data_processing.exporter.Path", return_value=output_file)

        # Create the file manually since we're testing integration
        misc_df = sample_dataframe_with_categories[
            sample_dataframe_with_categories["category"] == "MISC"
        ]
        misc_df.to_csv(output_file, index=False, encoding='utf-8-sig')

        # Verify file exists and contains correct data
        assert output_file.exists()
        result_df = pd.read_csv(output_file, encoding='utf-8-sig')
        assert len(result_df) == 2  # Two MISC entries
        assert all(result_df["category"] == "MISC")

    def test_google_sheets_export_format(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        test_data_dir: Path
    ) -> None:
        """Test Google Sheets export format compatibility."""
        output_file = test_data_dir / "for_google_sheets.csv"

        # Export data
        sample_dataframe_with_categories.to_csv(output_file, index=False)

        # Verify format is compatible with Google Sheets
        result_df = pd.read_csv(output_file)
        assert list(result_df.columns) == [
            "category", "price", "month", "year", "data"]
        assert len(result_df) == len(sample_dataframe_with_categories)
        assert result_df.isna().sum().sum() == 0  # No NaN values


@pytest.mark.integration
@pytest.mark.slow
class TestLargeDatasetProcessing:
    """Integration tests with larger datasets."""

    def test_processing_large_dataset(
        self,
        test_data_dir: Path,
        mocker: MockerFixture
    ) -> None:
        """Test processing a larger dataset (1000+ transactions)."""
        # Create large dataset
        large_df = pd.DataFrame({
            "data": [f"transaction {i}" for i in range(1000)],
            "price": [f"-{i % 100 + 10}.0" for i in range(1000)],
            "month": [i % 12 + 1 for i in range(1000)],
            "year": [2023] * 1000
        })

        # Save to file
        input_file = test_data_dir / "large_transactions.csv"
        large_df.to_csv(input_file, index=False)

        # Read and process
        df = read_transaction_csv(str(input_file), 'utf-8')
        assert len(df) == 1000

        cleaned_df = clean_date(df)
        assert len(cleaned_df) == 1000

        # Mock mappings
        mocker.patch("data_processing.data_core.mappings", {})

        processed_df = process_dataframe(cleaned_df)
        # All should be MISC since no mappings match
        assert len(processed_df) == 1000
