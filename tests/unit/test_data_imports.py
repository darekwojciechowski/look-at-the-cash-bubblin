"""Tests for data_processing.data_imports module.
Covers IPKO format import and CSV reading with encoding fallback.
"""

from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_imports import _check_gzip_bomb, ipko_import, read_transaction_csv


@pytest.mark.unit
class TestIpkoImport:
    """Test suite for IPKO bank format import."""

    def test_ipko_import_columns_and_structure(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """Verify column set, date conversion, data concatenation, and dropped columns.

        Given: a raw IPKO-formatted DataFrame
        When:  ipko_import() is called
        Then:  the result has [price, data, month, year, day] columns with correct values and dropped extras
        """
        # Arrange — via sample_ipko_dataframe fixture
        processed_df = ipko_import(sample_ipko_dataframe)

        # Assert
        # Verify the expected columns are present
        # ipko_import now retains source columns required for stable txn_id
        # computation alongside the merged `data` column.
        expected_columns = [
            "booking_date",
            "value_date",
            "txn_type",
            "amount",
            "currency",
            "description",
            "data",
            "month",
            "year",
            "day",
        ]
        assert list(processed_df.columns) == expected_columns

        # Verify date conversion
        assert processed_df["month"].iloc[0] == 1
        assert processed_df["year"].iloc[0] == 2023
        assert processed_df["day"].iloc[0] == 1

        # Verify data column transformation
        assert processed_df["data"].iloc[0] == "transfer//description1//extra1//extra3//data1"

        # Verify helper columns are dropped
        assert "unnamed_6" not in processed_df.columns
        assert "unnamed_8" not in processed_df.columns

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
        """Test that amount column is preserved correctly.

        Given: a raw IPKO DataFrame with known amount values
        When:  ipko_import() is called
        Then:  the amount column is present with the original string values
        """
        # Arrange — via sample_ipko_dataframe fixture
        processed_df = ipko_import(sample_ipko_dataframe)

        # Assert
        assert "amount" in processed_df.columns
        assert processed_df["amount"].iloc[0] == "-100.0"
        assert processed_df["amount"].iloc[1] == "-50.0"

    def test_ipko_import_strips_nan_from_data_column(self) -> None:
        """Verify that NaN cells are excluded from the concatenated data column.

        Given: a raw IPKO DataFrame where unnamed_6, unnamed_8, and data columns are NaN
        When:  ipko_import() is called
        Then:  the resulting data column contains no '//nan' fragments
        """
        # Arrange
        import numpy as np

        raw_df = pd.DataFrame({
            0: ["2023-01-01"],
            1: ["PLN"],
            2: ["przelew z rachunku"],
            3: ["-500.0"],
            4: ["PLN"],
            5: ["car repair"],
            6: [np.nan],
            7: [np.nan],
            8: [np.nan],
        })

        # Act
        result = ipko_import(raw_df)

        # Assert
        assert "nan" not in result["data"].iloc[0]
        assert result["data"].iloc[0] == "przelew z rachunku//car repair"


@pytest.mark.unit
class TestReadTransactionCsv:
    """Test suite for CSV file reading with encoding fallback."""

    def test_read_transaction_csv_success(self, tmp_path: Path) -> None:
        """A valid UTF-8 CSV is read successfully with the declared encoding."""
        # Arrange
        csv_file = tmp_path / "transactions.csv"
        csv_file.write_text("data,amount,month,year\norlen,-10.0,1,2023\n", encoding="utf-8")

        # Act
        df = read_transaction_csv(csv_file, "utf-8")

        # Assert
        assert len(df) == 1
        assert list(df.columns) == ["data", "amount", "month", "year"]
        assert df["data"].iloc[0] == "orlen"

    def test_read_transaction_csv_with_path_object(self, tmp_path: Path) -> None:
        """Path objects are accepted and decoded the same as string paths."""
        # Arrange
        csv_file = tmp_path / "transactions_path_obj.csv"
        csv_file.write_text("data,amount,month,year\nshop,-15.0,2,2023\n", encoding="utf-8")

        # Act
        df = read_transaction_csv(csv_file, "utf-8")

        # Assert
        assert len(df) == 1
        assert df["data"].iloc[0] == "shop"

    def test_read_transaction_csv_unicode_error_fallback(self, tmp_path: Path) -> None:
        """When UTF-8 fails, fallback encodings decode real cp1250 CSV content."""
        # Arrange
        csv_file = tmp_path / "cp1250_transactions.csv"
        csv_file.write_text("data,amount,month,year\nŁódź,-22.0,3,2023\n", encoding="cp1250")

        # Act
        df = read_transaction_csv(csv_file, "utf-8")

        # Assert
        assert len(df) == 1
        assert df["data"].iloc[0] == "Łódź"

    def test_read_transaction_csv_tries_polish_encodings(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """Encoding retries follow utf-8 -> utf-8-sig -> cp1250 order for Polish text."""
        # Arrange
        csv_file = tmp_path / "order.csv"
        csv_file.write_text("data,amount,month,year\nŻabka,-30.0,4,2023\n", encoding="cp1250")
        real_read_csv = pd.read_csv
        attempted_encodings: list[str | None] = []

        def _side_effect(*args: object, **kwargs: object) -> pd.DataFrame:
            encoding = kwargs.get("encoding")
            attempted_encodings.append(encoding if isinstance(encoding, str) else None)
            if encoding in {"utf-8", "utf-8-sig"}:
                raise UnicodeDecodeError(str(encoding), b"\x81", 0, 1, "invalid")
            return real_read_csv(*args, **kwargs)

        mocker.patch("pandas.read_csv", side_effect=_side_effect)

        # Act
        df = read_transaction_csv(csv_file, "utf-8")

        # Assert
        assert len(df) == 1
        assert attempted_encodings[:3] == ["utf-8", "utf-8-sig", "cp1250"]

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

    def test_read_transaction_csv_file_not_found(self) -> None:
        """Missing files raise FileNotFoundError with no silent fallback."""
        # Arrange
        missing_file = Path("nonexistent.csv")

        # Act + Assert
        with pytest.raises(FileNotFoundError):
            read_transaction_csv(missing_file, "utf-8")

    def test_read_transaction_csv_skips_malformed_rows(self, tmp_path: Path, loguru_sink: list[str]) -> None:
        """Malformed rows are skipped while valid rows are still loaded."""
        # Arrange
        csv_file = tmp_path / "malformed_rows.csv"
        csv_file.write_text(
            "data,amount,month,year\ngood,-10.0,1,2023\nbad,-20.0,1,2023,EXTRA\ngood2,-30.0,2,2023\n",
            encoding="utf-8",
        )

        # Act
        result = read_transaction_csv(csv_file, "utf-8")

        # Assert
        assert len(result) == 2
        assert set(result["data"]) == {"good", "good2"}
        assert any("[SKIP_BAD_LINE]" in entry for entry in loguru_sink)

    def test_read_transaction_csv_latin1_deprioritized(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """Test that latin-1 encoding is deprioritized to avoid mojibake.

        Given: the caller requests latin-1 encoding
        When:  read_transaction_csv() tries encodings in its preferred order
        Then:  the first attempt uses a Polish-friendly encoding, not latin-1
        """
        # Arrange
        csv_file = tmp_path / "latin1_order_test.csv"
        csv_file.write_text("data,amount,month,year\nshop,-10.0,1,2023\n", encoding="utf-8")
        real_read_csv = pd.read_csv
        call_encodings: list[str | None] = []

        def track_encoding(*args: object, **kwargs: object) -> pd.DataFrame:
            encoding = kwargs.get("encoding")
            call_encodings.append(encoding if isinstance(encoding, str) else None)
            return real_read_csv(*args, **kwargs)

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = track_encoding

        # Act
        try:
            df = read_transaction_csv(csv_file, "latin-1")
        finally:
            csv_file.unlink(missing_ok=True)

        # Assert
        assert not df.empty
        assert call_encodings[0] in ["utf-8", "utf-8-sig", "cp1250", "iso-8859-2"]

    def test_read_transaction_csv_respects_non_latin1_encoding(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """Test that non-latin1 caller encoding is tried first.

        Given: the caller requests cp1250 encoding
        When:  read_transaction_csv() is called and succeeds on the first try
        Then:  the first attempt uses cp1250
        """
        # Arrange
        csv_file = tmp_path / "cp1250_first.csv"
        csv_file.write_text("data,amount,month,year\nŻabka,-33.0,1,2023\n", encoding="cp1250")
        real_read_csv = pd.read_csv
        call_encodings: list[str | None] = []

        def track_encoding(*args: object, **kwargs: object) -> pd.DataFrame:
            encoding = kwargs.get("encoding")
            call_encodings.append(encoding if isinstance(encoding, str) else None)
            return real_read_csv(*args, **kwargs)

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = track_encoding

        # Act
        df = read_transaction_csv(csv_file, "cp1250")

        # Assert
        assert not df.empty
        assert call_encodings[0] == "cp1250"

    def test_read_transaction_csv_permission_denied(self, mocker: MockerFixture) -> None:
        """Permission errors are re-raised without being swallowed."""
        # Arrange
        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = PermissionError("access denied")

        # Act + Assert
        with pytest.raises(PermissionError, match="access denied"):
            read_transaction_csv("protected.csv", "utf-8")

    def test_read_transaction_csv_utf8_bom_encoding(self, tmp_path: Path) -> None:
        """Test that UTF-8 BOM files are read correctly.

        Given: a real CSV file written with a UTF-8 BOM preamble
        When:  read_transaction_csv() is called with utf-8-sig encoding
        Then:  the file is read successfully and the data column contains the expected value
        """
        # Arrange
        csv_file = tmp_path / "bom.csv"
        csv_file.write_bytes(b"\xef\xbb\xbfdata,amount,month,year\norlen,-50.0,1,2024\n")

        # Act
        df = read_transaction_csv(str(csv_file), "utf-8-sig")

        # Assert
        assert not df.empty
        assert "data" in df.columns
        assert df["data"].iloc[0] == "orlen"

    def test_read_transaction_csv_encoding_related_exception(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """Test that encoding-related parser errors trigger fallback to next encoding.

        Given: the first read attempt raises a ParserError whose message mentions a codec
        When:  read_transaction_csv() is called
        Then:  it retries and succeeds on the second attempt
        """
        # Arrange
        csv_file = tmp_path / "encoding_related.csv"
        csv_file.write_text("data,amount,month,year\nshop,-10.0,1,2023\n", encoding="utf-8")
        real_read_csv = pd.read_csv
        call_count = 0

        def side_effect(*args: object, **kwargs: object) -> pd.DataFrame:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise pd.errors.ParserError("codec error detected")
            return real_read_csv(*args, **kwargs)

        mock_read_csv = mocker.patch("pandas.read_csv")
        mock_read_csv.side_effect = side_effect

        # Act
        df = read_transaction_csv(csv_file, "utf-8")

        # Assert
        assert not df.empty
        assert call_count == 2  # First failed with codec error, second succeeded


@pytest.mark.unit
class TestCheckGzipBomb:
    """Tests for the _check_gzip_bomb defensive guard."""

    def test_returns_silently_for_zero_byte_file(self, tmp_path: Path) -> None:
        gz_file = tmp_path / "empty.gz"
        gz_file.write_bytes(b"")

        _check_gzip_bomb(gz_file)  # must not raise

    def test_returns_silently_for_safe_ratio(self, tmp_path: Path) -> None:
        import gzip as _gzip

        gz_file = tmp_path / "safe.gz"
        gz_file.write_bytes(_gzip.compress(b"test data " * 100))

        _check_gzip_bomb(gz_file)  # must not raise


@pytest.mark.unit
class TestReadTransactionCsvSymlink:
    """Symlink safety tests for read_transaction_csv."""

    def test_allows_safe_symlink_within_parent(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        real_csv = data_dir / "real.csv"
        real_csv.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
        symlink_path = data_dir / "link.csv"
        symlink_path.symlink_to(real_csv)

        result = read_transaction_csv(symlink_path, "utf-8")

        assert not result.empty
        assert "col1" in result.columns
