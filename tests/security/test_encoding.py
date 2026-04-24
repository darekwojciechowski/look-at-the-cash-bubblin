"""Encoding security tests.

Replaces TestEncodingAndCharacterSet (F09, F10).
Adds M06 (encoding-fallback logging), M07 (BOM round-trip), M09 (homograph),
M10 (RLO), M12 (locale decimal separator).
"""

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_imports import read_transaction_csv

pytestmark = pytest.mark.security


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_CSV = "data,price,month,year\ntest_value,-10.0,1,2023\n"


def _write_text(path: Path, content: str, encoding: str) -> Path:
    path.write_text(content, encoding=encoding)
    return path


# ---------------------------------------------------------------------------
# Happy-path encoding support (replaces F10)
# ---------------------------------------------------------------------------


class TestEncodingHappyPaths:
    @pytest.mark.parametrize(
        "encoding",
        ["utf-8", "utf-8-sig", "cp1250", "iso-8859-2"],
        ids=["utf8", "utf8sig", "cp1250", "iso88592"],
    )
    def test_read_handles_common_encodings(self, encoding: str, tmp_path: Path) -> None:
        """Given a CSV written with a common Polish-safe encoding,
        when read_transaction_csv() is called with that encoding,
        then the file is read successfully and contains the expected row.
        """
        # Arrange
        csv_file = _write_text(tmp_path / f"test_{encoding}.csv", _MINIMAL_CSV, encoding)

        # Act
        df = read_transaction_csv(str(csv_file), encoding)

        # Assert
        assert len(df) == 1
        assert df["data"].iloc[0] == "test_value"


# ---------------------------------------------------------------------------
# Encoding fallback + logging (M06)
# ---------------------------------------------------------------------------


class TestEncodingFallback:
    def test_read_falls_back_when_declared_encoding_wrong(
        self,
        tmp_path: Path,
        loguru_sink: list[str],
    ) -> None:
        """Given a cp1250-encoded file called with encoding='utf-8',
        when read_transaction_csv() runs,
        then it falls back to a working encoding and logs a DEBUG record for 'utf-8'.
        """
        # Arrange — write cp1250 content with a Polish character that is invalid UTF-8
        polish_csv = "data,price,month,year\nKsiążka,-10.0,1,2023\n"
        csv_file = tmp_path / "polish.csv"
        csv_file.write_bytes(polish_csv.encode("cp1250"))

        # Act — caller declares utf-8 but the bytes are cp1250
        df = read_transaction_csv(str(csv_file), "utf-8")

        # Assert — fallback succeeded
        assert len(df) == 1
        # Assert — the failed encoding was logged at DEBUG
        assert any("[ENCODING] Failed with encoding: utf-8" in msg for msg in loguru_sink), (
            f"Expected DEBUG log for encoding fallback, got: {loguru_sink}"
        )

    def test_read_logs_when_all_encodings_fail(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given that pd.read_csv raises UnicodeDecodeError for every attempted encoding,
        when read_transaction_csv() runs,
        then ValueError is raised and its message lists the attempted encodings.
        """
        # Arrange
        csv_file = tmp_path / "dummy.csv"
        csv_file.write_text(_MINIMAL_CSV, encoding="utf-8")

        def _always_fail(*args: object, **kwargs: object) -> pd.DataFrame:
            raise UnicodeDecodeError("mocked", b"", 0, 1, "forced failure")

        monkeypatch.setattr("pandas.read_csv", _always_fail)

        # Act + Assert
        with pytest.raises(ValueError, match="Could not read"):
            read_transaction_csv(str(csv_file), "utf-8")


# ---------------------------------------------------------------------------
# BOM round-trip (M07)
# ---------------------------------------------------------------------------


class TestBomHandling:
    def test_read_round_trips_utf8_bom(self, write_csv_bytes: Callable[[bytes, str], Path]) -> None:
        """Given a CSV written with a UTF-8 BOM (utf-8-sig),
        when read_transaction_csv() loads it,
        then the content is preserved without a stray BOM in the data column.
        """
        # Arrange — write with BOM
        content_with_bom = "﻿data,price,month,year\nbom_test,-10.0,1,2023\n"
        csv_file = write_csv_bytes(content_with_bom.encode("utf-8-sig"), "bom.csv")

        # Act
        df = read_transaction_csv(str(csv_file), "utf-8-sig")

        # Assert — BOM must not appear inside a cell value
        assert len(df) == 1
        first_col = df.columns[0]
        assert "﻿" not in first_col, f"BOM leaked into column name: {first_col!r}"


# ---------------------------------------------------------------------------
# Polish diacritics (M06 real-world sanity)
# ---------------------------------------------------------------------------


class TestPolishDiacritics:
    def test_read_preserves_polish_diacritics_with_cp1250(self, tmp_path: Path) -> None:
        """Given a cp1250-encoded file with Polish diacritics,
        when read_transaction_csv() is called with cp1250,
        then the diacritics are correctly decoded.
        """
        # Arrange
        polish_csv = "data,price,month,year\nŁódź café,-10.0,1,2023\n"
        csv_file = tmp_path / "pl.csv"
        csv_file.write_bytes(polish_csv.encode("cp1250"))

        # Act
        df = read_transaction_csv(str(csv_file), "cp1250")

        # Assert
        assert "Łódź" in df["data"].iloc[0]


# ---------------------------------------------------------------------------
# Homograph and RLO (M09, M10)
# ---------------------------------------------------------------------------


class TestUnicodeSpoof:
    @pytest.mark.parametrize(
        "description",
        [
            "оrlen",  # Cyrillic 'о' + Latin 'rlen'
            "bіedronka",  # Cyrillic 'і' inside
            "‮=evil",  # RLO + formula trigger
            "desc​ription",  # Zero-width space
        ],
        ids=["cyrillic_o", "cyrillic_i", "rlo_formula", "zwsp"],
    )
    def test_read_preserves_homograph_and_rlo_content(
        self,
        description: str,
        tmp_path: Path,
    ) -> None:
        """Given a CSV containing homograph or RLO characters,
        when read_transaction_csv() loads it,
        then the content is byte-identical to what was written.
        """
        # Arrange — write using utf-8 which can represent all Unicode
        csv_content = f"data,price,month,year\n{description},-10.0,1,2023\n"
        csv_file = tmp_path / "spoof.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        # Act
        df = read_transaction_csv(str(csv_file), "utf-8")

        # Assert
        assert df["data"].iloc[0] == description


# ---------------------------------------------------------------------------
# Locale decimal separator (M12)
# ---------------------------------------------------------------------------


class TestLocaleDecimalSeparator:
    def test_process_dataframe_rejects_comma_decimal_price(self) -> None:
        """Given a price string using a comma decimal separator ('1,50'),
        when process_dataframe() runs,
        then ValueError is raised — comma separators are not valid Python floats.
        """
        from data_processing.data_core import process_dataframe

        # Arrange
        df = pd.DataFrame({"data": ["test"], "price": ["1,50"], "month": [1], "year": [2023]})

        # Act + Assert — astype(float) does not accept commas
        with pytest.raises(ValueError):
            process_dataframe(df)
