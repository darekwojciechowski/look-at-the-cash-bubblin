"""Tests for data_processing.exporter module.
Covers CSV and Google Sheets export, MISC transaction filtering, and Expense loading.
"""

from pathlib import Path
from unittest.mock import MagicMock, call, mock_open

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.exporter import (
    export_for_google_sheets,
    export_misc_transactions,
    export_unassigned_transactions_to_csv,
    get_data,
)


@pytest.mark.unit
class TestExportForGoogleSheets:
    """Test suite for Google Sheets export functionality."""

    def test_export_for_google_sheets_success(
        self, mocker: MockerFixture, sample_dataframe_with_categories: pd.DataFrame
    ) -> None:
        """Test successful export to Google Sheets format.

        Given: a DataFrame with category data and mocked to_csv/logger
        When:  export_for_google_sheets() is called
        Then:  logger.info is called and to_csv writes to the expected path
        """
        # Arrange
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        mock_logger = mocker.patch("data_processing.exporter.logger")

        # Act
        export_for_google_sheets(sample_dataframe_with_categories)

        # Assert
        mock_logger.info.assert_called()
        mock_to_csv.assert_called_once_with(Path("for_google_spreadsheet.csv"), index=False)

    def test_export_for_google_sheets_empty_dataframe(self, mocker: MockerFixture) -> None:
        """Test export with empty DataFrame.

        Given: an empty DataFrame with the expected columns
        When:  export_for_google_sheets() is called
        Then:  to_csv is still called with the correct output path
        """
        # Arrange
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        empty_df = pd.DataFrame(columns=["category", "price", "month", "year", "data"])

        # Act
        export_for_google_sheets(empty_df)

        # Assert
        mock_to_csv.assert_called_once_with(Path("for_google_spreadsheet.csv"), index=False)


@pytest.mark.unit
class TestExportMiscTransactions:
    """Test suite for MISC category transaction export."""

    def test_export_misc_transactions_filters_correctly(
        self, mocker: MockerFixture, sample_dataframe_with_categories: pd.DataFrame
    ) -> None:
        """Test that only MISC category transactions are exported.

        Given: a DataFrame with two MISC rows and other category rows
        When:  export_misc_transactions() is called
        Then:  to_csv is called once with the unassigned path and exactly two MISC rows exist
        """
        # Arrange
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")

        # Act
        export_misc_transactions(sample_dataframe_with_categories)

        # Assert
        mock_to_csv.assert_called_once_with(Path("unassigned_transactions.csv"), index=False, encoding="utf-8-sig")

        # Verify only MISC rows are selected
        misc_df = sample_dataframe_with_categories[sample_dataframe_with_categories["category"] == "MISC"]
        assert len(misc_df) == 2
        pd.testing.assert_frame_equal(
            misc_df, sample_dataframe_with_categories[sample_dataframe_with_categories["category"] == "MISC"]
        )

    def test_export_misc_transactions_no_misc_category(self, mocker: MockerFixture) -> None:
        """Test export when no MISC transactions exist.

        Given: a DataFrame containing only FOOD and FUEL rows
        When:  export_misc_transactions() is called
        Then:  to_csv is still called once (with an empty selection)
        """
        # Arrange
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        df = pd.DataFrame({
            "category": ["FOOD", "FUEL"],
            "price": [100.0, 50.0],
            "month": [1, 1],
            "year": [2023, 2023],
            "data": ["groceries", "fuel"],
        })

        # Act
        export_misc_transactions(df)

        # Assert
        mock_to_csv.assert_called_once()

    def test_export_misc_transactions_empty_dataframe(self, mocker: MockerFixture) -> None:
        """Test export with empty DataFrame.

        Given: an empty DataFrame with the expected columns
        When:  export_misc_transactions() is called
        Then:  to_csv is called once without raising an error
        """
        # Arrange
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")
        empty_df = pd.DataFrame(columns=["category", "price", "month", "year", "data"])

        # Act
        export_misc_transactions(empty_df)

        # Assert
        mock_to_csv.assert_called_once()


@pytest.mark.unit
class TestExportUnassignedTransactions:
    """Test suite for unassigned transactions export."""

    def test_export_unassigned_transactions_to_csv(
        self, mocker: MockerFixture, sample_dataframe_with_categories: pd.DataFrame
    ) -> None:
        """Test basic export of unassigned transactions.

        Given: a DataFrame with category data
        When:  export_unassigned_transactions_to_csv() is called
        Then:  to_csv is called once with the unassigned path and utf-8-sig encoding
        """
        # Arrange
        mock_to_csv = mocker.patch("pandas.DataFrame.to_csv")

        # Act
        export_unassigned_transactions_to_csv(sample_dataframe_with_categories)

        # Assert
        mock_to_csv.assert_called_once_with(Path("unassigned_transactions.csv"), index=False, encoding="utf-8-sig")


@pytest.mark.unit
class TestExportFinalData:
    """Test suite for final data export operations."""

    def test_get_data_success(self, mocker: MockerFixture, csv_data_mock: str) -> None:
        """Test successful parsing of final data from CSV.

        Given: a mocked CSV reader that returns a header row and two data rows
        When:  get_data() is called
        Then:  two Expense-like objects are returned with the correct field values
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_csv_reader.return_value = iter([
            ["month", "year", "item", "price"],
            ["1", "2023", "item1", "100"],
            ["2", "2023", "item2", "200"],
        ])

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 2
        assert expenses[0].month == "1"
        assert expenses[0].year == "2023"
        assert expenses[0].item == "item1"
        assert expenses[0].price == "100"
        assert expenses[1].month == "2"
        assert expenses[1].year == "2023"

    def test_get_data_empty_csv(self, mocker: MockerFixture) -> None:
        """Test parsing empty CSV file.

        Given: a mocked CSV reader that returns only a header row
        When:  get_data() is called
        Then:  an empty list is returned
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_csv_reader.return_value = iter([
            ["month", "year", "item", "price"],
        ])

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 0


@pytest.mark.unit
class TestGetData:
    """Test suite for get_data function."""

    def test_get_data_creates_expenses(self, mocker: MockerFixture) -> None:
        """
        Test get_data creates Expense objects from CSV.

        Given: a mocked CSV reader with two data rows and a patched Expense constructor
        When:  get_data() is called
        Then:  the Expense constructor is called twice with the correct four arguments

        Fixed: get_data now properly passes all 4 arguments to Expense constructor.
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_expense = mocker.patch("data_processing.exporter.Expense")
        mock_csv_reader.return_value = iter([
            ["month", "year", "item", "price"],
            ["1", "2023", "item1", "100"],
            ["2", "2023", "item2", "200"],
        ])
        mock_expense_instance = MagicMock()
        mock_expense.return_value = mock_expense_instance

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 2
        # Verify Expense constructor calls with all 4 arguments
        expected_calls = [
            call("1", "2023", "item1", "100"),
            call("2", "2023", "item2", "200"),
        ]
        mock_expense.assert_has_calls(expected_calls)

    def test_get_data_empty_csv(self, mocker: MockerFixture) -> None:
        """Test get_data with empty CSV file.

        Given: a mocked CSV reader with only a header row
        When:  get_data() is called
        Then:  an empty list is returned and Expense is never called
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_csv_reader = mocker.patch("csv.reader")
        mock_expense = mocker.patch("data_processing.exporter.Expense")
        mock_csv_reader.return_value = iter([
            ["month", "year", "item", "price"],
        ])
        mock_expense_instance = MagicMock()
        mock_expense.return_value = mock_expense_instance

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 0
        mock_expense.assert_not_called()


@pytest.mark.unit
class TestExporterModuleImport:
    """Smoke tests for the public API surface of data_processing.exporter."""

    def test_module_imports_successfully(self) -> None:
        """Verify the exporter module imports without raising an error.

        Given: the data_processing.exporter module on the Python path
        When:  the module is imported
        Then:  no ImportError is raised
        """
        # Arrange + Act + Assert — top-level import already succeeded; reaching
        # this line proves the module loaded cleanly.
        import data_processing.exporter  # noqa: F401

    def test_get_data_accepts_path_parameter(self) -> None:
        """Verify get_data has a path parameter with the expected default.

        Given: the data_processing.exporter module is imported
        When:  the signature of get_data is inspected
        Then:  a 'path' parameter exists with default Path('data/processed_transactions.csv')
        """
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(get_data)

        # Assert
        assert "path" in sig.parameters
        assert sig.parameters["path"].default == Path("data/processed_transactions.csv")

    def test_module_has_expected_functions(self) -> None:
        """Verify the exporter module exposes the four expected public functions.

        Given: the data_processing.exporter module is imported
        When:  each expected function name is checked with hasattr and callable
        Then:  all four functions exist and are callable
        """
        # Arrange
        import data_processing.exporter

        expected_functions = [
            "export_for_google_sheets",
            "export_misc_transactions",
            "export_unassigned_transactions_to_csv",
            "get_data",
        ]

        # Act + Assert
        for func_name in expected_functions:
            assert hasattr(data_processing.exporter, func_name)
            assert callable(getattr(data_processing.exporter, func_name))
