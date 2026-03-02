"""Tests for data_processing.data_imports module.
Comprehensive testing of CSV reading and IPKO format import functionality.
"""

from pathlib import Path
from unittest.mock import mock_open

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_imports import ipko_import, read_transaction_csv


@pytest.mark.unit
class TestIpkoImport:
    """Test suite for IPKO bank format import."""

    def test_ipko_import_columns_and_structure(self, sample_ipko_dataframe: pd.DataFrame) -> None:
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

    def test_ipko_import_lowercases_text_columns(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """Test that text columns are properly converted to lowercase."""
        processed_df = ipko_import(sample_ipko_dataframe)

        assert "TRANSFER" not in processed_df["data"].iloc[0]
        assert "transfer" in processed_df["data"].iloc[0]

    def test_ipko_import_preserves_price_column(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """Test that price column is preserved correctly."""
        processed_df = ipko_import(sample_ipko_dataframe)

        assert "price" in processed_df.columns
        assert processed_df["price"].iloc[0] == "-100.0"
        assert processed_df["price"].iloc[1] == "-50.0"


@pytest.mark.unit
class TestReadTransactionCsv:
    """Test suite for CSV file reading with encoding fallback."""

    def test_read_transaction_csv_success(self, mocker: MockerFixture) -> None:
        """
        Tests the read_transaction_csv function to ensure:
        - The CSV file is read correctly with the specified encoding.
        - The resulting DataFrame is not empty and contains the expected data.
        """
        mocker.patch("builtins.open", mock_open(read_data="col1,col2\nval1,val2"))
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.return_value = pd.DataFrame({"col1": ["val1"], "col2": ["val2"]})

        df = read_transaction_csv("dummy_path.csv", "utf-8")

        mock_read_csv.assert_called_once_with("dummy_path.csv", on_bad_lines="skip", encoding="utf-8")
        assert not df.empty
        assert df["col1"].iloc[0] == "val1"
        assert df["col2"].iloc[0] == "val2"

    def test_read_transaction_csv_with_path_object(self, mocker: MockerFixture) -> None:
        """Test that read_transaction_csv works with Path objects."""
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.return_value = pd.DataFrame({"col1": ["val1"]})

        path_obj = Path("test_path.csv")
        df = read_transaction_csv(path_obj, "utf-8")

        assert not df.empty
        mock_read_csv.assert_called_once_with(path_obj, on_bad_lines="skip", encoding="utf-8")

    def test_read_transaction_csv_unicode_error_fallback(self, mocker: MockerFixture) -> None:
        """Test that function tries alternative encodings on UnicodeDecodeError."""
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
            pd.DataFrame({"col1": ["val1"]}),
        ]

        df = read_transaction_csv("test.csv", "utf-8")

        assert not df.empty
        assert mock_read_csv.call_count == 2

    def test_read_transaction_csv_tries_polish_encodings(self, mocker: MockerFixture) -> None:
        """Test that function prefers Polish encodings."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = side_effect

        df = read_transaction_csv("test.csv", "utf-8")

        assert not df.empty
        # Should try utf-8, utf-8-sig, cp1250 in order
        assert call_count == 3

    def test_read_transaction_csv_all_encodings_fail(self, mocker: MockerFixture) -> None:
        """Test that ValueError is raised when all encodings fail."""
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")

        with pytest.raises(ValueError, match="Could not read.*with any of the tried encodings"):
            read_transaction_csv("test.csv", "utf-8")

    def test_read_transaction_csv_file_not_found(self, mocker: MockerFixture) -> None:
        """Tests the read_transaction_csv function when file reading fails."""
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        mock_log_error = mocker.patch("loguru.logger.error")

        with pytest.raises(FileNotFoundError, match="File not found"):
            read_transaction_csv("nonexistent.csv", "utf-8")

        mock_log_error.assert_called_once_with(
            "[ERROR] Failed to read CSV file: nonexistent.csv. Error: File not found"
        )

    def test_read_transaction_csv_generic_error(self, mocker: MockerFixture) -> None:
        """Test that generic errors are logged and re-raised."""
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = Exception("Generic error")
        mock_log_error = mocker.patch("loguru.logger.error")

        with pytest.raises(Exception, match="Generic error"):
            read_transaction_csv("test.csv", "utf-8")

        mock_log_error.assert_called_once()

    def test_read_transaction_csv_latin1_deprioritized(self, mocker: MockerFixture) -> None:
        """Test that latin-1 encoding is deprioritized to avoid mojibake."""
        call_encodings: list[str | None] = []

        def track_encoding(*args, **kwargs):
            call_encodings.append(kwargs.get("encoding"))
            if len(call_encodings) == 1:
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = track_encoding

        df = read_transaction_csv("test.csv", "latin-1")

        assert not df.empty
        assert call_encodings[0] in ["utf-8", "utf-8-sig", "cp1250", "iso-8859-2"]

    def test_read_transaction_csv_respects_non_latin1_encoding(self, mocker: MockerFixture) -> None:
        """Test that non-latin1 caller encoding is tried first."""
        call_encodings: list[str | None] = []

        def track_encoding(*args, **kwargs):
            call_encodings.append(kwargs.get("encoding"))
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = track_encoding

        df = read_transaction_csv("test.csv", "cp1250")

        assert not df.empty
        assert call_encodings[0] == "cp1250"

    def test_read_transaction_csv_encoding_related_exception(self, mocker: MockerFixture) -> None:
        """Test that encoding-related exceptions trigger fallback to next encoding."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("codec error detected")
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = side_effect

        df = read_transaction_csv("test.csv", "utf-8")

        assert not df.empty
        assert call_count == 2  # First failed with codec error, second succeeded
