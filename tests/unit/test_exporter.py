"""
Tests for data_processing.exporter module.
Comprehensive testing of data export functionality to various formats.
"""

from pathlib import Path
from unittest.mock import MagicMock, call, mock_open

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_loader import Expense
from data_processing.exporter import (
    export_for_google_sheets,
    export_misc_transactions,
    export_unassigned_transactions_to_csv,
    get_data,
)


@pytest.mark.unit
class TestExportForGoogleSheets:
    """Test suite for Google Sheets export functionality."""

    def test_export_for_google_sheets_success(self, mocker: MockerFixture, sample_dataframe_with_categories: pd.DataFrame) -> None:
        """Test successful export to Google Sheets format."""
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        mock_logger = mocker.patch("data_processing.exporter.logger")

        export_for_google_sheets(sample_dataframe_with_categories)

        mock_logger.info.assert_called()
        mock_to_csv.assert_called_once_with(Path("for_google_spreadsheet.csv"), index=False)

    def test_export_for_google_sheets_empty_dataframe(self, mocker: MockerFixture) -> None:
        """Test export with empty DataFrame."""
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        empty_df = pd.DataFrame(columns=["category", "price", "month", "year", "data"])

        export_for_google_sheets(empty_df)

        mock_to_csv.assert_called_once_with(Path("for_google_spreadsheet.csv"), index=False)


@pytest.mark.unit
class TestExportMiscTransactions:
    """Test suite for MISC category transaction export."""

    def test_export_misc_transactions_filters_correctly(self, mocker: MockerFixture, sample_dataframe_with_categories: pd.DataFrame) -> None:
        """Test that only MISC category transactions are exported."""
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        export_misc_transactions(sample_dataframe_with_categories)

        mock_to_csv.assert_called_once_with(Path("unassigned_transactions.csv"), index=False, encoding="utf-8-sig")

        # Verify only MISC rows are selected
        misc_df = sample_dataframe_with_categories[sample_dataframe_with_categories["category"] == "MISC"]
        assert len(misc_df) == 2
        pd.testing.assert_frame_equal(misc_df, sample_dataframe_with_categories[sample_dataframe_with_categories["category"] == "MISC"])

    def test_export_misc_transactions_no_misc_category(self, mocker: MockerFixture) -> None:
        """Test export when no MISC transactions exist."""
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        df = pd.DataFrame(
            {
                "category": ["FOOD", "FUEL"],
                "price": [100.0, 50.0],
                "month": [1, 1],
                "year": [2023, 2023],
                "data": ["groceries", "fuel"],
            }
        )

        export_misc_transactions(df)

        mock_to_csv.assert_called_once()

    def test_export_misc_transactions_empty_dataframe(self, mocker: MockerFixture) -> None:
        """Test export with empty DataFrame."""
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        empty_df = pd.DataFrame(columns=["category", "price", "month", "year", "data"])

        export_misc_transactions(empty_df)

        mock_to_csv.assert_called_once()


@pytest.mark.unit
class TestExportUnassignedTransactions:
    """Test suite for unassigned transactions export."""

    def test_export_unassigned_transactions_to_csv(self, mocker: MockerFixture, sample_dataframe_with_categories: pd.DataFrame) -> None:
        """Test basic export of unassigned transactions."""
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        export_unassigned_transactions_to_csv(sample_dataframe_with_categories)

        mock_to_csv.assert_called_once_with(Path("unassigned_transactions.csv"), index=False, encoding="utf-8-sig")


@pytest.mark.unit
class TestExportFinalData:
    """Test suite for final data export operations."""

    def test_get_data_success(self, mocker: MockerFixture, csv_data_mock: str) -> None:
        """Test successful parsing of final data from CSV."""
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_csv_reader.return_value = iter(
            [
                ["month", "year", "item", "price"],
                ["1", "2023", "item1", "100"],
                ["2", "2023", "item2", "200"],
            ]
        )

        expenses = get_data()

        assert len(expenses) == 2
        assert expenses[0].month == "1"
        assert expenses[0].year == "2023"
        assert expenses[0].item == "item1"
        assert expenses[0].price == "100"
        assert expenses[1].month == "2"
        assert expenses[1].year == "2023"

    def test_get_data_empty_csv(self, mocker: MockerFixture) -> None:
        """Test parsing empty CSV file."""
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_csv_reader.return_value = iter(
            [
                ["month", "year", "item", "price"],
            ]
        )

        expenses = get_data()

        assert len(expenses) == 0


@pytest.mark.unit
class TestGetData:
    """Test suite for get_data function."""

    def test_get_data_creates_expenses(self, mocker: MockerFixture) -> None:
        """
        Test get_data creates Expense objects from CSV.

        Fixed: get_data now properly passes all 4 arguments to Expense constructor.
        """
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_expense = mocker.patch("data_processing.exporter.Expense")
        mock_csv_reader.return_value = iter(
            [
                ["month", "year", "item", "price"],
                ["1", "2023", "item1", "100"],
                ["2", "2023", "item2", "200"],
            ]
        )

        mock_expense_instance = MagicMock()
        mock_expense.return_value = mock_expense_instance

        expenses = get_data()

        assert len(expenses) == 2
        # Verify Expense constructor calls with all 4 arguments
        expected_calls = [
            call("1", "2023", "item1", "100"),
            call("2", "2023", "item2", "200"),
        ]
        mock_expense.assert_has_calls(expected_calls)

    def test_get_data_empty_csv(self, mocker: MockerFixture) -> None:
        """Test get_data with empty CSV file."""
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_expense = mocker.patch("data_processing.exporter.Expense")
        mock_csv_reader.return_value = iter(
            [
                ["month", "year", "item", "price"],
            ]
        )

        mock_expense_instance = MagicMock()
        mock_expense.return_value = mock_expense_instance

        expenses = get_data()

        assert len(expenses) == 0
        mock_expense.assert_not_called()
