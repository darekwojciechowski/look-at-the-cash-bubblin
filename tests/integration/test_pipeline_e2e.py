"""End-to-end pipeline integration: read → clean → process → export."""

from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_core import clean_descriptions, process_dataframe
from data_processing.data_imports import ipko_import, read_transaction_csv


@pytest.mark.integration
class TestEndToEndDataProcessing:
    """Integration tests for complete data processing workflow."""

    def test_complete_pipeline_with_real_csv(self, sample_csv_file: Path, test_data_dir: Path) -> None:
        """Test complete pipeline from CSV reading to export.

        Given: a real CSV file with two transaction rows
        When:  the full pipeline (read → clean → process → export) is executed
        Then:  the output categories are determined by real mapping tables
               and the output file row count matches processed rows
        """
        # Arrange — via sample_csv_file fixture

        # Act — Read CSV
        df = read_transaction_csv(str(sample_csv_file), "utf-8")
        assert not df.empty
        assert len(df) == 2

        # Act — Process data
        cleaned_df = clean_descriptions(df)
        assert "data" in cleaned_df.columns

        processed_df = process_dataframe(cleaned_df)
        assert "category" in processed_df.columns
        assert len(processed_df) > 0
        assert set(processed_df["category"]) == {"FUEL", "FOOD"}

        # Act — Export to file
        output_file = test_data_dir / "output.csv"
        processed_df.to_csv(output_file, index=False)

        # Assert
        assert output_file.exists()
        result_df = pd.read_csv(output_file)
        assert len(result_df) == len(processed_df)

    def test_ipko_import_and_processing_uses_real_category_mappings(self) -> None:
        """Test IPKO import and processing with explicit expected category outcomes.

        Given: a raw IPKO-formatted DataFrame with known merchant descriptions
        When:  the full import → clean → process pipeline is executed
        Then:  category outcomes include FUEL, FOOD, and fallback MISC
        """
        # Arrange
        raw_ipko_df = pd.DataFrame({
            0: ["2023-01-01", "2023-01-02", "2023-01-03"],
            1: ["2023-01-01", "2023-01-02", "2023-01-03"],
            2: ["purchase", "purchase", "purchase"],
            3: ["-100.0", "-50.0", "-30.0"],
            4: ["PLN", "PLN", "PLN"],
            5: ["orlen station", "biedronka groceries", "unknown merchant"],
            6: ["", "", ""],
            7: ["", "", ""],
            8: ["", "", ""],
        })

        # Act
        imported_df = ipko_import(raw_ipko_df)
        processed_df = process_dataframe(imported_df)

        # Assert
        assert "category" in processed_df.columns
        assert list(processed_df["category"]) == ["FUEL", "FOOD", "MISC"]
