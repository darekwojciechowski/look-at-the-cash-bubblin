from data_processing.data_core import clean_date, process_dataframe
from unittest.mock import patch
import pandas as pd
import pytest
import sys
import os


@pytest.fixture
def sample_dataframe():
    """Fixture to provide a sample DataFrame for testing."""
    return pd.DataFrame({
        "data": [
            "purchase in terminal - mobile code",
            "web payment - mobile code",
            "orlen",
            "starbucks",
            "piotrkowska 157a"
        ],
        "price": ["-50.0", "-20.0", "-100.0", "-15.0", "200.0"],
        "month": [1, 1, 1, 1, 1],
        "year": [2023, 2023, 2023, 2023, 2023]
    })


@pytest.fixture
def mappings_mock():
    """Fixture to provide a mock mappings dictionary."""
    return {
        "terminal purchase": "Shopping",
        "web payment": "Online Payment",
        "Orlen gas station": "Fuel",
        "Starbucks coffee shop": "Coffee",
        "Biedronka - Piotrkowska 157a": "Groceries"
    }


def test_clean_date(sample_dataframe):
    """Test the clean_date function."""
    cleaned_df = clean_date(sample_dataframe)
    assert cleaned_df["data"].iloc[0] == "terminal purchase"
    assert cleaned_df["data"].iloc[1] == "web payment"
    assert cleaned_df["data"].iloc[2] == "Orlen gas station"
    assert cleaned_df["data"].iloc[3] == "Starbucks coffee shop"
    assert cleaned_df["data"].iloc[4] == "Biedronka - Piotrkowska 157a"


@patch("data_processing.data_core.ipko_import")
def test_process_dataframe(mock_ipko_import, sample_dataframe, mappings_mock):
    """Test the process_dataframe function."""
    # Mock ipko_import to return the input DataFrame
    mock_ipko_import.return_value = sample_dataframe

    # Patch the mappings dictionary
    with patch("data_processing.data_core.mappings", mappings_mock):
        processed_df = process_dataframe(sample_dataframe)

    # Debug: Print the processed DataFrame for inspection
    print(processed_df)

    # Verify the processed DataFrame
    # Expect 4 rows after filtering out the positive price row
    assert len(processed_df) == 4
    assert processed_df["category"].iloc[0] == "Shopping"
    assert processed_df["category"].iloc[1] == "Online Payment"
    assert processed_df["category"].iloc[2] == "Fuel"
    assert processed_df["category"].iloc[3] == "Coffee"

    # Verify that positive prices are removed
    assert "200.0" not in processed_df["price"].values

    # Verify column order
    expected_columns = ["month", "year", "price", "category", "data"]
    assert list(processed_df.columns) == expected_columns


@patch("data_processing.data_core.ipko_import")
@patch("logging.error")
def test_process_dataframe_ipko_import_failure(mock_logging_error, mock_ipko_import, sample_dataframe):
    """Test process_dataframe when ipko_import fails."""
    # Mock ipko_import to raise an exception
    mock_ipko_import.side_effect = Exception("Import failed")

    # Verify that the exception is raised and logged
    with pytest.raises(Exception, match="Import failed"):
        process_dataframe(sample_dataframe)

    # Verify that error was logged
    mock_logging_error.assert_called_once_with(
        "ipko_import failed: Import failed")
