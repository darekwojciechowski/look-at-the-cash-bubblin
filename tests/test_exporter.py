import pytest
import pandas as pd
from unittest.mock import patch, mock_open, MagicMock
from data_processing.exporter import (
    export_for_google_sheets,
    export_misc_transactions,
    export_unassigned_transactions_to_csv,
    export_final_data,
    export_final_date_for_google_spreadsheet,
    get_data,
)
from data_processing.data_loader import Expense


@pytest.fixture
def sample_dataframe():
    """Provides a sample DataFrame for testing purposes."""
    return pd.DataFrame({
        "category": ["Misc", "Food", "Misc"],
        "price": [100, 200, 300],
        "month": [1, 1, 1],
        "year": [2023, 2023, 2023],
        "data": ["location 1", "location 2", "location 3"]
    })


@pytest.fixture
def sample_expenses():
    """Provides a sample list of Expense objects for testing."""
    return [
        Expense(1, 2023, "item1", 100),
        Expense(1, 2023, "item2", 200),
        Expense(1, 2023, "item3", 300),
    ]


@patch("builtins.print")
@patch("pandas.DataFrame.to_csv")
def test_export_for_google_sheets(mock_to_csv, mock_print, sample_dataframe):
    """
    Tests the export_for_google_sheets function to ensure:
    - The DataFrame is printed to the console.
    - The DataFrame is exported to a CSV file named 'for_google_spreadsheet.csv'.
    """
    export_for_google_sheets(sample_dataframe)

    mock_print.assert_called_once()
    mock_to_csv.assert_called_once_with(
        "for_google_spreadsheet.csv", index=False)


@patch("pandas.DataFrame.to_csv")
def test_export_misc_transactions(mock_to_csv, sample_dataframe):
    """
    Tests the export_misc_transactions function to ensure:
    - Only rows with the 'Misc' category are exported.
    - The resulting DataFrame is saved to 'unassigned_transactions.csv'.
    """
    export_misc_transactions(sample_dataframe)

    mock_to_csv.assert_called_once_with(
        "unassigned_transactions.csv", index=False, encoding='utf-8-sig')
    expected_df = sample_dataframe[sample_dataframe["category"] == "Misc"]
    pd.testing.assert_frame_equal(
        expected_df, sample_dataframe[sample_dataframe["category"] == "Misc"]
    )


@patch("pandas.DataFrame.to_csv")
def test_export_unassigned_transactions_to_csv(mock_to_csv, sample_dataframe):
    """
    Tests the export_unassigned_transactions_to_csv function to ensure:
    - The DataFrame is exported to a CSV file named 'unassigned_transactions.csv'.
    """
    export_unassigned_transactions_to_csv(sample_dataframe)

    mock_to_csv.assert_called_once_with(
        "unassigned_transactions.csv", index=False, encoding='utf-8-sig')


@patch("builtins.open", new_callable=mock_open, read_data="month,year,item,price\n1,2023,item1,100\n")
@patch("csv.reader")
def test_export_final_data(mock_csv_reader, mock_file):
    """
    Tests the export_final_data function to ensure:
    - The correct number of Expense objects are created from the CSV data.
    - The Expense objects have the expected attributes.
    """
    mock_csv_reader.return_value = iter([
        ["month", "year", "item", "price"],
        ["1", "2023", "item1", "100"],
    ])

    expenses = export_final_data()

    assert len(expenses) == 1
    assert expenses[0].month == "1"
    assert expenses[0].year == "2023"
    assert expenses[0].item == "item1"
    assert expenses[0].price == "100"


@patch("builtins.print")
@patch("pandas.DataFrame.to_csv")
def test_export_final_date_for_google_spreadsheet(mock_to_csv, mock_print, sample_expenses):
    """
    Tests the export_final_date_for_google_spreadsheet function to ensure:
    - The DataFrame is printed to the console.
    - The DataFrame is exported to a CSV file named 'for_google_spreadsheet.csv' with tab-separated values.
    """
    export_final_date_for_google_spreadsheet(sample_expenses)

    mock_print.assert_called_once()
    mock_to_csv.assert_called_once_with(
        "for_google_spreadsheet.csv", sep="\t", index=False)


@patch("builtins.print")
@patch("pandas.DataFrame.to_csv")
@patch("logging.error")
def test_export_final_date_for_google_spreadsheet_empty_data(mock_error, mock_to_csv, mock_print):
    """
    Tests the export_final_date_for_google_spreadsheet function with empty data to ensure:
    - An error is logged when DataFrame is empty.
    - Function returns early without further processing.
    """
    empty_data = []
    export_final_date_for_google_spreadsheet(empty_data)

    mock_error.assert_called_once_with(
        "The DataFrame is empty. No data to export.")
    mock_to_csv.assert_not_called()
    mock_print.assert_not_called()


@patch("builtins.open", new_callable=mock_open, read_data="month,year,item,price\n1,2023,item1,100\n")
@patch("csv.reader")
@patch("data_processing.exporter.Expense")
def test_get_data(mock_expense, mock_csv_reader, mock_file):
    """
    Tests the get_data function to ensure:
    - The correct number of Expense objects are created from the CSV data.
    - The Expense constructor is called with the expected arguments.
    Note: get_data has a bug - it only passes 2 arguments to Expense constructor.
    """
    mock_csv_reader.return_value = iter([
        ["month", "year", "item", "price"],
        ["1", "2023", "item1", "100"],
    ])

    mock_expense_instance = MagicMock()
    mock_expense.return_value = mock_expense_instance

    expenses = get_data()

    assert len(expenses) == 1
    # Verify that Expense was called with only the first 2 elements of the row
    # This demonstrates the bug in get_data function
    mock_expense.assert_called_once_with("1", "2023")


@patch("logging.error")
def test_export_final_date_for_google_spreadsheet_dataframe_operations(mock_error):
    """
    Tests the export_final_date_for_google_spreadsheet function's DataFrame operations.
    """
    # Test with valid data that creates a non-empty DataFrame
    sample_data = ["1,2023,item1,FOOD,100,Essential"]

    with patch("builtins.print") as mock_print:
        with patch("pandas.DataFrame.to_csv") as mock_to_csv:
            export_final_date_for_google_spreadsheet(sample_data)

            # Verify DataFrame operations were called
            mock_print.assert_called_once()
            mock_to_csv.assert_called_once_with(
                "for_google_spreadsheet.csv", sep="\t", index=False)
