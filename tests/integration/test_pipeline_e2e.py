"""End-to-end pipeline integration: read → clean → process → export."""

from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_core import clean_descriptions, process_dataframe
from data_processing.data_imports import ipko_import, read_transaction_csv


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
