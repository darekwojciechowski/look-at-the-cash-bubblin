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


def test_process_dataframe(sample_dataframe, mappings_mock):
    """Test the process_dataframe function."""
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


@patch("logging.error")
def test_process_dataframe_ipko_import_failure(mock_logging_error, sample_dataframe):
    """Test process_dataframe when there's a processing error."""
    # Create an invalid DataFrame that will cause an error during processing
    invalid_df = pd.DataFrame({
        "invalid_column": ["test"],
        "price": ["invalid_price"],
        "month": [1],
        "year": [2023]
    })

    # Verify that the exception is raised
    with pytest.raises(KeyError):
        process_dataframe(invalid_df)
