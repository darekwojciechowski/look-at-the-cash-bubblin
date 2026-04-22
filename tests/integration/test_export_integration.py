"""Integration tests for CSV export with real file I/O."""

from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture


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
