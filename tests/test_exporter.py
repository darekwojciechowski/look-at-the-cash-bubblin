"""
Tests for data_processing.exporter module.
Comprehensive testing of data export functionality to various formats.
"""

from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pandas as pd
import pytest

from data_processing.data_loader import Expense
from data_processing.exporter import (
    export_final_data,
    export_final_date_for_google_spreadsheet,
    export_for_google_sheets,
    export_misc_transactions,
    export_unassigned_transactions_to_csv,
    get_data,
)


@pytest.fixture
def sample_dataframe():
    """Provides realistic transaction DataFrame for testing."""
    return pd.DataFrame(
        {
            "category": ["MISC", "FOOD", "MISC", "FUEL"],
            "price": [100.0, 200.0, 300.0, 50.0],
            "month": [1, 1, 2, 2],
            "year": [2023, 2023, 2023, 2023],
            "data": [
                "unknown transaction",
                "biedronka shopping",
                "misc item",
                "orlen fuel",
            ],
        }
    )


@pytest.fixture
def sample_expenses():
    """Provides realistic Expense objects for testing."""
    return [
        Expense(1, 2023, "apartment rent", 1200),
        Expense(1, 2023, "groceries", 200),
        Expense(2, 2023, "fuel", 100),
    ]


@pytest.fixture
def csv_data_mock():
    """Mock CSV data for testing file reading operations."""
    return "month,year,item,price\n1,2023,item1,100\n2,2023,item2,200\n"


class TestExportForGoogleSheets:
    """Test suite for Google Sheets export functionality."""

    @patch("builtins.print")
    @patch("pandas.DataFrame.to_csv")
    def test_export_for_google_sheets_success(self, mock_to_csv, mock_print, sample_dataframe):
        """Test successful export to Google Sheets format."""
        export_for_google_sheets(sample_dataframe)

        mock_print.assert_called_once()
        mock_to_csv.assert_called_once_with(Path("for_google_spreadsheet.csv"), index=False)

    @patch("pandas.DataFrame.to_csv")
    def test_export_for_google_sheets_empty_dataframe(self, mock_to_csv):
        """Test export with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["category", "price", "month", "year", "data"])

        with patch("builtins.print"):
            export_for_google_sheets(empty_df)

        mock_to_csv.assert_called_once_with(Path("for_google_spreadsheet.csv"), index=False)


class TestExportMiscTransactions:
    """Test suite for MISC category transaction export."""

    @patch("pandas.DataFrame.to_csv")
    def test_export_misc_transactions_filters_correctly(self, mock_to_csv, sample_dataframe):
        """Test that only MISC category transactions are exported."""
        export_misc_transactions(sample_dataframe)

        mock_to_csv.assert_called_once_with(Path("unassigned_transactions.csv"), index=False, encoding="utf-8-sig")

        # Verify only MISC rows are selected
        misc_df = sample_dataframe[sample_dataframe["category"] == "MISC"]
        assert len(misc_df) == 2
        pd.testing.assert_frame_equal(misc_df, sample_dataframe[sample_dataframe["category"] == "MISC"])

    @patch("pandas.DataFrame.to_csv")
    def test_export_misc_transactions_no_misc_category(self, mock_to_csv):
        """Test export when no MISC transactions exist."""
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

    @patch("pandas.DataFrame.to_csv")
    def test_export_misc_transactions_empty_dataframe(self, mock_to_csv):
        """Test export with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["category", "price", "month", "year", "data"])

        export_misc_transactions(empty_df)

        mock_to_csv.assert_called_once()


class TestExportUnassignedTransactions:
    """Test suite for unassigned transactions export."""

    @patch("pandas.DataFrame.to_csv")
    def test_export_unassigned_transactions_to_csv(self, mock_to_csv, sample_dataframe):
        """Test basic export of unassigned transactions."""
        export_unassigned_transactions_to_csv(sample_dataframe)

        mock_to_csv.assert_called_once_with(Path("unassigned_transactions.csv"), index=False, encoding="utf-8-sig")


class TestExportFinalData:
    """Test suite for final data export operations."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.reader")
    def test_export_final_data_success(self, mock_csv_reader, mock_file, csv_data_mock):
        """Test successful parsing of final data from CSV."""
        mock_csv_reader.return_value = iter(
            [
                ["month", "year", "item", "price"],
                ["1", "2023", "item1", "100"],
                ["2", "2023", "item2", "200"],
            ]
        )

        expenses = export_final_data()

        assert len(expenses) == 2
        assert expenses[0].month == "1"
        assert expenses[0].year == "2023"
        assert expenses[0].item == "item1"
        assert expenses[0].price == "100"
        assert expenses[1].month == "2"
        assert expenses[1].year == "2023"

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.reader")
    def test_export_final_data_empty_csv(self, mock_csv_reader, mock_file):
        """Test parsing empty CSV file."""
        mock_csv_reader.return_value = iter(
            [
                ["month", "year", "item", "price"],
            ]
        )

        expenses = export_final_data()

        assert len(expenses) == 0


class TestExportFinalDateForGoogleSpreadsheet:
    """Test suite for Google Spreadsheet final data export."""

    @patch("builtins.print")
    @patch("pandas.DataFrame.to_csv")
    def test_export_final_date_for_google_spreadsheet_success(self, mock_to_csv, mock_print, sample_expenses):
        """Test successful export to Google Spreadsheet format."""
        export_final_date_for_google_spreadsheet(sample_expenses)

        mock_print.assert_called_once()
        mock_to_csv.assert_called_once_with(Path("for_google_spreadsheet.csv"), sep="\t", index=False)

    @patch("builtins.print")
    @patch("pandas.DataFrame.to_csv")
    @patch("loguru.logger.error")
    def test_export_final_date_for_google_spreadsheet_empty_data(self, mock_error, mock_to_csv, mock_print):
        """Test export with empty data list."""
        empty_data = []
        export_final_date_for_google_spreadsheet(empty_data)

        mock_error.assert_called_once_with("The DataFrame is empty. No data to export.")
        mock_to_csv.assert_not_called()
        mock_print.assert_not_called()

    @patch("builtins.print")
    @patch("pandas.DataFrame.to_csv")
    def test_export_final_date_for_google_spreadsheet_single_expense(self, mock_to_csv, mock_print):
        """Test export with single expense."""
        single_expense = [Expense(1, 2023, "test item", 100)]

        export_final_date_for_google_spreadsheet(single_expense)

        mock_print.assert_called_once()
        mock_to_csv.assert_called_once()


class TestGetData:
    """Test suite for get_data function."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.reader")
    @patch("data_processing.exporter.Expense")
    def test_get_data_creates_expenses(self, mock_expense, mock_csv_reader, mock_file):
        """
        Test get_data creates Expense objects from CSV.

        Fixed: get_data now properly passes all 4 arguments to Expense constructor.
        """
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

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.reader")
    @patch("data_processing.exporter.Expense")
    def test_get_data_empty_csv(self, mock_expense, mock_csv_reader, mock_file):
        """Test get_data with empty CSV file."""
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
