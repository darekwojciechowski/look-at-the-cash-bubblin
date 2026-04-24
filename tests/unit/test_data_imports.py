"""Tests for data_processing.data_imports module.
Covers IPKO format import and CSV reading with encoding fallback.
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
        """Verify column set, date conversion, data concatenation, and dropped columns.

        Given: a raw IPKO-formatted DataFrame
        When:  ipko_import() is called
        Then:  the result has [price, data, month, year] columns with correct values and dropped extras
        """
        # Arrange — via sample_ipko_dataframe fixture
        processed_df = ipko_import(sample_ipko_dataframe)

        # Assert
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
        """Test that text columns are properly converted to lowercase.

        Given: a raw IPKO DataFrame with uppercase text in the data column
        When:  ipko_import() is called
        Then:  the data column contains only lowercase text
        """
        # Arrange — via sample_ipko_dataframe fixture
        processed_df = ipko_import(sample_ipko_dataframe)

        # Assert
        assert "TRANSFER" not in processed_df["data"].iloc[0]
        assert "transfer" in processed_df["data"].iloc[0]

    def test_ipko_import_preserves_price_column(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """Test that price column is preserved correctly.

        Given: a raw IPKO DataFrame with known price values
        When:  ipko_import() is called
        Then:  the price column is present with the original string values
        """
        # Arrange — via sample_ipko_dataframe fixture
        processed_df = ipko_import(sample_ipko_dataframe)

        # Assert
        assert "price" in processed_df.columns
        assert processed_df["price"].iloc[0] == "-100.0"
        assert processed_df["price"].iloc[1] == "-50.0"


@pytest.mark.unit
class TestReadTransactionCsv:
    """Test suite for CSV file reading with encoding fallback."""

    def test_read_transaction_csv_success(self, mocker: MockerFixture) -> None:
        """Verify read_transaction_csv calls pandas with the correct encoding and returns data.

        Given: a mocked pandas.read_csv that returns a single-row DataFrame
        When:  read_transaction_csv() is called with a dummy path and utf-8 encoding
        Then:  read_csv is called once with correct arguments and the data is returned
        """
        # Arrange
        mocker.patch("builtins.open", mock_open(read_data="col1,col2\nval1,val2"))
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.return_value = pd.DataFrame({"col1": ["val1"], "col2": ["val2"]})

        # Act
        df = read_transaction_csv("dummy_path.csv", "utf-8")

        # Assert
        call_kwargs = mock_read_csv.call_args.kwargs
        assert call_kwargs["encoding"] == "utf-8"
        assert callable(call_kwargs["on_bad_lines"])
        assert call_kwargs["engine"] == "python"
        assert not df.empty
        assert df["col1"].iloc[0] == "val1"
        assert df["col2"].iloc[0] == "val2"

    def test_read_transaction_csv_with_path_object(self, mocker: MockerFixture) -> None:
        """Test that read_transaction_csv works with Path objects.

        Given: a Path object as the file argument
        When:  read_transaction_csv() is called
        Then:  the Path is forwarded to read_csv and a non-empty DataFrame is returned
        """
        # Arrange
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.return_value = pd.DataFrame({"col1": ["val1"]})
        path_obj = Path("test_path.csv")

        # Act
        df = read_transaction_csv(path_obj, "utf-8")

        # Assert
        assert not df.empty
        call_kwargs = mock_read_csv.call_args.kwargs
        assert call_kwargs["encoding"] == "utf-8"
        assert callable(call_kwargs["on_bad_lines"])
        assert call_kwargs["engine"] == "python"

    def test_read_transaction_csv_unicode_error_fallback(self, mocker: MockerFixture) -> None:
        """Test that function tries alternative encodings on UnicodeDecodeError.

        Given: pandas.read_csv raises UnicodeDecodeError on the first call
        When:  read_transaction_csv() is called
        Then:  the function retries with a different encoding and returns data
        """
        # Arrange
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
            pd.DataFrame({"col1": ["val1"]}),
        ]

        # Act
        df = read_transaction_csv("test.csv", "utf-8")

        # Assert
        assert not df.empty
        assert mock_read_csv.call_count == 2

    def test_read_transaction_csv_tries_polish_encodings(self, mocker: MockerFixture) -> None:
        """Test that function prefers Polish encodings.

        Given: pandas.read_csv fails twice with UnicodeDecodeError then succeeds
        When:  read_transaction_csv() is called
        Then:  three attempts are made in the order utf-8, utf-8-sig, cp1250
        """
        # Arrange
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = side_effect

        # Act
        df = read_transaction_csv("test.csv", "utf-8")

        # Assert
        assert not df.empty
        # Should try utf-8, utf-8-sig, cp1250 in order
        assert call_count == 3

    def test_read_transaction_csv_all_encodings_fail(self, mocker: MockerFixture) -> None:
        """Test that ValueError is raised when all encodings fail.

        Given: pandas.read_csv always raises UnicodeDecodeError
        When:  read_transaction_csv() is called
        Then:  a ValueError with a descriptive message is raised
        """
        # Arrange
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")

        # Act + Assert
        with pytest.raises(ValueError, match="Could not read.*with any of the tried encodings"):
            read_transaction_csv("test.csv", "utf-8")

    def test_read_transaction_csv_file_not_found(self, mocker: MockerFixture) -> None:
        """Verify FileNotFoundError is logged then re-raised when the file is missing.

        Given: pandas.read_csv raises FileNotFoundError
        When:  read_transaction_csv() is called
        Then:  the error is logged and re-raised unchanged
        """
        # Arrange
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        mock_log_error = mocker.patch("loguru.logger.error")

        # Act + Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            read_transaction_csv("nonexistent.csv", "utf-8")

        mock_log_error.assert_called_once_with(
            "[ERROR] Failed to read CSV file: nonexistent.csv. Error: File not found"
        )

    def test_read_transaction_csv_generic_error(self, mocker: MockerFixture) -> None:
        """Test that generic errors are logged and re-raised.

        Given: pandas.read_csv raises a generic Exception
        When:  read_transaction_csv() is called
        Then:  the error is logged and re-raised
        """
        # Arrange
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = Exception("Generic error")
        mock_log_error = mocker.patch("loguru.logger.error")

        # Act + Assert
        with pytest.raises(Exception, match="Generic error"):
            read_transaction_csv("test.csv", "utf-8")

        mock_log_error.assert_called_once()

    def test_read_transaction_csv_latin1_deprioritized(self, mocker: MockerFixture) -> None:
        """Test that latin-1 encoding is deprioritized to avoid mojibake.

        Given: the caller requests latin-1 encoding
        When:  read_transaction_csv() tries encodings in its preferred order
        Then:  the first attempt uses a Polish-friendly encoding, not latin-1
        """
        # Arrange
        call_encodings: list[str | None] = []

        def track_encoding(*args, **kwargs):
            call_encodings.append(kwargs.get("encoding"))
            if len(call_encodings) == 1:
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = track_encoding

        # Act
        df = read_transaction_csv("test.csv", "latin-1")

        # Assert
        assert not df.empty
        assert call_encodings[0] in ["utf-8", "utf-8-sig", "cp1250", "iso-8859-2"]

    def test_read_transaction_csv_respects_non_latin1_encoding(self, mocker: MockerFixture) -> None:
        """Test that non-latin1 caller encoding is tried first.

        Given: the caller requests cp1250 encoding
        When:  read_transaction_csv() is called and succeeds on the first try
        Then:  the first attempt uses cp1250
        """
        # Arrange
        call_encodings: list[str | None] = []

        def track_encoding(*args, **kwargs):
            call_encodings.append(kwargs.get("encoding"))
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = track_encoding

        # Act
        df = read_transaction_csv("test.csv", "cp1250")

        # Assert
        assert not df.empty
        assert call_encodings[0] == "cp1250"

    def test_read_transaction_csv_permission_denied(self, mocker: MockerFixture) -> None:
        """Test that PermissionError is logged and re-raised.

        Given: pandas.read_csv raises PermissionError
        When:  read_transaction_csv() is called
        Then:  the error is logged once and re-raised
        """
        # Arrange
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = PermissionError("access denied")
        mock_log_error = mocker.patch("loguru.logger.error")

        # Act + Assert
        with pytest.raises(PermissionError, match="access denied"):
            read_transaction_csv("protected.csv", "utf-8")

        mock_log_error.assert_called_once()

    def test_read_transaction_csv_utf8_bom_encoding(self, tmp_path: Path) -> None:
        """Test that UTF-8 BOM files are read correctly.

        Given: a real CSV file written with a UTF-8 BOM preamble
        When:  read_transaction_csv() is called with utf-8-sig encoding
        Then:  the file is read successfully and the data column contains the expected value
        """
        # Arrange
        csv_file = tmp_path / "bom.csv"
        csv_file.write_bytes(b"\xef\xbb\xbfdata,price,month,year\norlen,-50.0,1,2024\n")

        # Act
        df = read_transaction_csv(str(csv_file), "utf-8-sig")

        # Assert
        assert not df.empty
        assert "data" in df.columns
        assert df["data"].iloc[0] == "orlen"

    def test_read_transaction_csv_encoding_related_exception(self, mocker: MockerFixture) -> None:
        """Test that encoding-related exceptions trigger fallback to next encoding.

        Given: the first read attempt raises a generic 'codec error' exception
        When:  read_transaction_csv() is called
        Then:  it retries and succeeds on the second attempt
        """
        # Arrange
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("codec error detected")
            return pd.DataFrame({"col1": ["val1"]})

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = side_effect

        # Act
        df = read_transaction_csv("test.csv", "utf-8")

        # Assert
        assert not df.empty
        assert call_count == 2  # First failed with codec error, second succeeded
