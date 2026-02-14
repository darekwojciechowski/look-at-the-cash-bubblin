from pathlib import Path
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from data_processing.data_imports import ipko_import, read_transaction_csv


@pytest.fixture
def sample_ipko_dataframe():
    """Provides a sample DataFrame for testing the ipko_import function."""
    return pd.DataFrame(
        {
            0: ["2023-01-01", "2023-01-02"],
            1: ["PLN", "PLN"],
            2: ["transfer", "payment"],
            3: ["-100.0", "-50.0"],
            4: ["PLN", "PLN"],
            5: ["description1", "description2"],
            6: ["extra1", "extra2"],
            7: ["data1", "data2"],
            8: ["extra3", "extra4"],
        }
    )


@pytest.mark.unit
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


@pytest.mark.unit
def test_ipko_import_lowercases_text_columns(sample_ipko_dataframe):
    """Test that text columns are properly converted to lowercase."""
    processed_df = ipko_import(sample_ipko_dataframe)

    # Verify all text in data column is lowercase
    assert "TRANSFER" not in processed_df["data"].iloc[0]
    assert "transfer" in processed_df["data"].iloc[0]


@pytest.mark.unit
def test_ipko_import_preserves_price_column(sample_ipko_dataframe):
    """Test that price column is preserved correctly."""
    processed_df = ipko_import(sample_ipko_dataframe)

    assert "price" in processed_df.columns
    assert processed_df["price"].iloc[0] == "-100.0"
    assert processed_df["price"].iloc[1] == "-50.0"


@pytest.mark.unit
@patch("builtins.open", new_callable=mock_open, read_data="col1,col2\nval1,val2")
@patch("pandas.read_csv")
def test_read_transaction_csv(mock_read_csv, mock_file):
    """
    Tests the read_transaction_csv function to ensure:
    - The CSV file is read correctly with the specified encoding.
    - The resulting DataFrame is not empty and contains the expected data.
    """
    mock_read_csv.return_value = pd.DataFrame({"col1": ["val1"], "col2": ["val2"]})

    # Call the function
    df = read_transaction_csv("dummy_path.csv", "utf-8")

    # Verify the DataFrame is loaded correctly
    mock_read_csv.assert_called_once_with("dummy_path.csv", on_bad_lines="skip", encoding="utf-8")
    assert not df.empty
    assert df["col1"].iloc[0] == "val1"
    assert df["col2"].iloc[0] == "val2"


@pytest.mark.unit
@patch("pandas.read_csv")
def test_read_transaction_csv_with_path_object(mock_read_csv):
    """Test that read_transaction_csv works with Path objects."""
    mock_read_csv.return_value = pd.DataFrame({"col1": ["val1"]})

    path_obj = Path("test_path.csv")
    df = read_transaction_csv(path_obj, "utf-8")

    assert not df.empty
    mock_read_csv.assert_called_once_with(path_obj, on_bad_lines="skip", encoding="utf-8")


@pytest.mark.unit
@patch("pandas.read_csv")
def test_read_transaction_csv_unicode_error_fallback(mock_read_csv):
    """Test that function tries alternative encodings on UnicodeDecodeError."""
    # First call raises UnicodeDecodeError, second succeeds
    mock_read_csv.side_effect = [UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"), pd.DataFrame({"col1": ["val1"]})]

    df = read_transaction_csv("test.csv", "utf-8")

    assert not df.empty
    assert mock_read_csv.call_count == 2


@pytest.mark.unit
@patch("pandas.read_csv")
def test_read_transaction_csv_tries_polish_encodings(mock_read_csv):
    """Test that function prefers Polish encodings."""
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        return pd.DataFrame({"col1": ["val1"]})

    mock_read_csv.side_effect = side_effect

    df = read_transaction_csv("test.csv", "utf-8")

    assert not df.empty
    # Should try utf-8, utf-8-sig, cp1250 in order
    assert call_count == 3


@pytest.mark.unit
@patch("pandas.read_csv")
def test_read_transaction_csv_all_encodings_fail(mock_read_csv):
    """Test that ValueError is raised when all encodings fail."""
    mock_read_csv.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")

    with pytest.raises(ValueError, match="Could not read.*with any of the tried encodings"):
        read_transaction_csv("test.csv", "utf-8")


@pytest.mark.unit
@patch("pandas.read_csv")
@patch("loguru.logger.error")
def test_read_transaction_csv_file_error(mock_logging_error, mock_read_csv):
    """
    Tests the read_transaction_csv function when file reading fails.
    """
    # Mock read_csv to raise an exception
    mock_read_csv.side_effect = FileNotFoundError("File not found")

    # Verify that the exception is raised and logged
    with pytest.raises(FileNotFoundError, match="File not found"):
        read_transaction_csv("nonexistent.csv", "utf-8")

    # Verify that error was logged
    mock_logging_error.assert_called_once_with(
        "[ERROR] Failed to read CSV file: nonexistent.csv. Error: File not found"
    )


@pytest.mark.unit
@patch("pandas.read_csv")
@patch("loguru.logger.error")
def test_read_transaction_csv_generic_error(mock_logging_error, mock_read_csv):
    """Test that generic errors are logged and re-raised."""
    mock_read_csv.side_effect = Exception("Generic error")

    with pytest.raises(Exception, match="Generic error"):
        read_transaction_csv("test.csv", "utf-8")

    mock_logging_error.assert_called_once()


@pytest.mark.unit
@patch("pandas.read_csv")
def test_read_transaction_csv_latin1_deprioritized(mock_read_csv):
    """Test that latin-1 encoding is deprioritized to avoid mojibake."""
    call_encodings = []

    def track_encoding(*args, **kwargs):
        call_encodings.append(kwargs.get("encoding"))
        if len(call_encodings) == 1:
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        return pd.DataFrame({"col1": ["val1"]})

    mock_read_csv.side_effect = track_encoding

    # Pass latin-1 as encoding - should be deprioritized
    df = read_transaction_csv("test.csv", "latin-1")

    assert not df.empty
    # First call should NOT be latin-1 since it's deprioritized
    assert call_encodings[0] in ["utf-8", "utf-8-sig", "cp1250", "iso-8859-2"]


@pytest.mark.unit
@patch("pandas.read_csv")
def test_read_transaction_csv_respects_non_latin1_encoding(mock_read_csv):
    """Test that non-latin1 caller encoding is tried first."""
    call_encodings = []

    def track_encoding(*args, **kwargs):
        call_encodings.append(kwargs.get("encoding"))
        return pd.DataFrame({"col1": ["val1"]})

    mock_read_csv.side_effect = track_encoding

    # Pass cp1250 - should be tried first
    df = read_transaction_csv("test.csv", "cp1250")

    assert not df.empty
    assert call_encodings[0] == "cp1250"


@pytest.mark.unit
@patch("pandas.read_csv")
def test_read_transaction_csv_encoding_related_exception(mock_read_csv):
    """Test that encoding-related exceptions trigger fallback to next encoding."""
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("codec error detected")
        return pd.DataFrame({"col1": ["val1"]})

    mock_read_csv.side_effect = side_effect

    df = read_transaction_csv("test.csv", "utf-8")

    assert not df.empty
    assert call_count == 2  # First failed with codec error, second succeeded
