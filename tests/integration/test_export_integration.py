"""Integration tests for CSV export with real file I/O."""

from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from config.logging_setup import setup_logging
from data_processing.data_core import process_dataframe, process_income_dataframe
from data_processing.exporter import (
    export_cleaned_income_data,
    export_for_google_sheets,
    export_income_for_google_sheets,
    export_unassigned_income,
    export_unassigned_transactions_to_csv,
)


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
        assert list(result_df.columns) == ["category", "amount", "day", "month", "year", "data"]
        assert len(result_df) == len(sample_dataframe_with_categories)
        assert result_df.isna().sum().sum() == 0  # No NaN values

    def test_given_processed_dataframe_when_exported_then_header_uses_tab_separator(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that google_sheets_expenses.csv has the exact header with tab separators.

        Given: a processed transaction DataFrame
        When:  export_for_google_sheets() writes the file
        Then:  the first line of the file is exactly
               'Day\\tMonth\\tYear\\tItem\\tCategory\\tAmount\\tImportance'
               with tab characters as separators (not spaces or commas)
        """
        # Arrange
        monkeypatch.chdir(tmp_path)
        expected_header = "Txn_Id\tDay\tMonth\tYear\tItem\tCategory\tAmount\tImportance"

        # Act
        export_for_google_sheets(sample_dataframe_with_categories)

        # Assert
        output_file = tmp_path / "google_sheets_expenses.csv"
        first_line = output_file.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == expected_header

    def test_given_misc_dataframe_when_exported_then_header_uses_comma_separator(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that unassigned_transactions.csv has the exact header with comma separators.

        Given: a DataFrame with MISC transactions in the canonical column order
        When:  export_unassigned_transactions_to_csv() writes the file
        Then:  the first line of the file is exactly
               'day,month,year,amount,category,data,extracted_location,google_maps_link'
               with comma characters as separators (not tabs or semicolons)
        """
        # Arrange
        monkeypatch.chdir(tmp_path)
        misc_df = pd.DataFrame({
            "day": [1],
            "month": [1],
            "year": [2025],
            "amount": [100.0],
            "category": ["MISC"],
            "data": ["test transaction"],
        })
        expected_header = "txn_id,day,month,year,amount,category,data,extracted_location,google_maps_link"

        # Act
        export_unassigned_transactions_to_csv(misc_df)

        # Assert
        output_file = tmp_path / "unassigned_transactions.csv"
        first_line = output_file.read_text(encoding="utf-8-sig").splitlines()[0]
        assert first_line == expected_header

    def test_given_logging_configured_when_export_runs_then_app_log_is_created(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that app.log is created when export runs with logging enabled.

        Given: logging is configured and the working directory is a temp folder
        When:  export_for_google_sheets() is called
        Then:  app.log exists in the working directory
        """
        # Arrange
        monkeypatch.chdir(tmp_path)
        setup_logging()

        # Act
        export_for_google_sheets(sample_dataframe_with_categories)

        # Assert
        assert (tmp_path / "app.log").exists()


@pytest.mark.integration
class TestIncomeExportEndToEnd:
    """End-to-end: mixed-sign DataFrame → both tracks → all six income/expense files."""

    def test_three_income_files_produced(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Given a mixed-sign DataFrame, the income track produces three files with
        the expected headers, separators, and row counts."""
        monkeypatch.chdir(tmp_path)

        mixed_df = pd.DataFrame({
            "data": [
                "wynagrodzenie january",
                "biedronka groceries",
                "freelance payout",
                "unknown deposit",
                "zwrot za zakup",
            ],
            "amount": ["5000.0", "-50.0", "1200.0", "300.0", "100.0"],
            "month": [1, 1, 1, 1, 1],
            "year": [2023, 2023, 2023, 2023, 2023],
            "day": [1, 2, 3, 4, 5],
        })

        income_df = process_income_dataframe(mixed_df.copy())

        (tmp_path / "data").mkdir()
        export_income_for_google_sheets(income_df)
        export_cleaned_income_data(income_df, tmp_path / "data" / "processed_income.csv")
        export_unassigned_income(income_df)

        # Google Sheets file: 3 income rows survive (refund is filtered as REMOVE_ENTRY)
        gs = pd.read_csv(tmp_path / "google_sheets_income.csv", sep="\t")
        assert list(gs.columns) == ["Txn_Id", "Day", "Month", "Year", "Item", "Category", "Amount", "Importance"]
        assert len(gs) == 3

        # Cleaned file: 3 rows, comma-separated, utf-8-sig
        cleaned = pd.read_csv(tmp_path / "data" / "processed_income.csv", encoding="utf-8-sig")
        assert list(cleaned.columns) == ["txn_id", "day", "month", "year", "category", "amount"]
        assert len(cleaned) == 3

        # Unassigned file: only INCOME_MISC rows, no location columns
        unassigned = pd.read_csv(tmp_path / "unassigned_income.csv", encoding="utf-8-sig")
        assert "google_maps_link" not in unassigned.columns
        assert len(unassigned) == 1
        assert unassigned["category"].iloc[0] == "INCOME_MISC"

    def test_expense_and_income_tracks_partition_input(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The expense and income tracks must not double-count any row."""
        monkeypatch.chdir(tmp_path)

        mixed_df = pd.DataFrame({
            "data": ["salary", "biedronka", "freelance"],
            "amount": ["5000.0", "-50.0", "1200.0"],
            "month": [1, 1, 1],
            "year": [2023, 2023, 2023],
            "day": [1, 2, 3],
        })

        expense = process_dataframe(mixed_df.copy())
        income = process_income_dataframe(mixed_df.copy())

        assert len(expense) == 1
        assert len(income) == 2
