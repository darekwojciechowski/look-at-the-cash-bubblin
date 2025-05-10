import pytest
import pandas as pd
from unittest.mock import patch, mock_open
from data_processing.data_imports import ipko_import, read_transaction_csv


@pytest.fixture
def sample_ipko_dataframe():
    """Provides a sample DataFrame for testing the ipko_import function."""
    return pd.DataFrame({
        0: ["2023-01-01", "2023-01-02"],
        1: ["PLN", "PLN"],
        2: ["transfer", "payment"],
        3: ["-100.0", "-50.0"],
        4: ["PLN", "PLN"],
        5: ["description1", "description2"],
        6: ["extra1", "extra2"],
        7: ["data1", "data2"],
        8: ["extra3", "extra4"]
    })


def test_ipko_import(sample_ipko_dataframe):
    """
    Tests the ipko_import function to ensure:
    - The resulting DataFrame contains the expected columns.
    - Date conversion is performed correctly.
    - The 'data' column is transformed as expected.
    - Unnecessary columns are dropped.
    """
    processed_df = ipko_import(sample_ipko_dataframe)

    # Verify the expected columns are present
    expected_columns = ["price", "data", "month", "year"]
    assert list(processed_df.columns) == expected_columns

    # Verify date conversion
    assert processed_df["month"].iloc[0] == 1
    assert processed_df["year"].iloc[0] == 2023

    # Verify data column transformation
    assert processed_df["data"].iloc[0] == "transfer//description1//extra1//extra3//data1"

    # Verify dropped columns
    assert "transaction_date" not in processed_df.columns
    assert "currency" not in processed_df.columns


@patch("builtins.open", new_callable=mock_open, read_data="col1,col2\nval1,val2")
@patch("pandas.read_csv")
def test_read_transaction_csv(mock_read_csv, mock_file):
    """
    Tests the read_transaction_csv function to ensure:
    - The CSV file is read correctly with the specified encoding.
    - The resulting DataFrame is not empty and contains the expected data.
    """
    mock_read_csv.return_value = pd.DataFrame(
        {"col1": ["val1"], "col2": ["val2"]}
    )

    # Call the function
    df = read_transaction_csv("dummy_path.csv", "utf-8")

    # Verify the DataFrame is loaded correctly
    mock_read_csv.assert_called_once_with(
        "dummy_path.csv", on_bad_lines="skip", encoding="utf-8"
    )
    assert not df.empty
    assert df["col1"].iloc[0] == "val1"
    assert df["col2"].iloc[0] == "val2"
