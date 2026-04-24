"""Input validation and sanitization tests.

Replaces TestInputValidation (F03, F04, F06) and TestDataTypeValidation (F07, F08).
Adds M11 (NaN/inf in price), byte-for-byte payload preservation, and timeout-guarded
long-string handling.
"""

from collections.abc import Callable
from unittest.mock import patch

import pandas as pd
import pytest

from data_processing.data_core import process_dataframe

pytestmark = pytest.mark.security

# Type alias mirroring the one in tests/conftest.py so local helpers stay typed.
type TransactionRow = dict[str, str | int | float]


def _mock_mappings(data: str) -> str:
    return "MISC"


def _make_df(rows: list[TransactionRow]) -> pd.DataFrame:
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Payload preservation (replaces F03, F04, F06 — gives them real oracles)
# ---------------------------------------------------------------------------


class TestPayloadPreservation:
    """process_dataframe must not alter the content of the data column for arbitrary payloads."""

    @pytest.mark.parametrize(
        "payload",
        [
            "'; DROP TABLE transactions; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>",
            "test\x00malicious",
            "file.csv\x00.txt",
            "data\x00\x00\x00",
        ],
        ids=[
            "sql_drop",
            "sql_or",
            "sql_admin",
            "sql_union",
            "xss_script",
            "xss_img",
            "xss_js",
            "xss_svg",
            "null_0",
            "null_1",
            "null_triple",
        ],
    )
    def test_process_dataframe_preserves_payload_byte_for_byte(
        self,
        payload: str,
        make_transaction_dataframe: Callable[[list[TransactionRow]], pd.DataFrame],
    ) -> None:
        """Given an adversarial payload in the data column,
        when process_dataframe() runs with a MISC-returning mapping,
        then the data column value is preserved exactly (no silent transformation).
        """
        # Arrange
        df = make_transaction_dataframe([{"data": payload, "price": "-10.0", "month": 1, "year": 2023}])

        # Act
        with patch("data_processing.data_core.mappings", _mock_mappings):
            result = process_dataframe(df)

        # Assert — byte-for-byte preservation
        assert result["data"].iloc[0] == payload, f"Payload {payload!r} was unexpectedly modified during processing"

    def test_process_dataframe_with_null_bytes_runs_to_completion(
        self,
        make_transaction_dataframe: Callable[[list[TransactionRow]], pd.DataFrame],
    ) -> None:
        """Given null bytes in all three rows,
        when process_dataframe() runs,
        then it completes without raising and returns a non-empty DataFrame.

        Replaces F06 which only tested pd.DataFrame construction, not the SUT.
        """
        # Arrange
        null_byte_inputs = ["test\x00malicious", "file.csv\x00.txt", "data\x00\x00\x00"]
        df = make_transaction_dataframe([
            {"data": v, "price": "-10.0", "month": 1, "year": 2023} for v in null_byte_inputs
        ])

        # Act
        with patch("data_processing.data_core.mappings", _mock_mappings):
            result = process_dataframe(df)

        # Assert — pipeline ran; all three rows survive (negative price, MISC category)
        assert len(result) == len(null_byte_inputs)


# ---------------------------------------------------------------------------
# Price field type validation (replaces F07)
# ---------------------------------------------------------------------------


class TestPriceValidation:
    """process_dataframe must reject non-numeric price strings with ValueError."""

    @pytest.mark.parametrize(
        "bad_price",
        ["not_a_number", "abc", ""],
        ids=["string", "alpha", "empty"],
    )
    def test_process_dataframe_rejects_non_numeric_price(
        self,
        bad_price: str,
        make_transaction_dataframe: Callable[[list[TransactionRow]], pd.DataFrame],
    ) -> None:
        """Given a non-numeric string in the price column,
        when process_dataframe() runs,
        then ValueError is raised (locked behaviour — astype(float) contract).
        """
        # Arrange
        df = make_transaction_dataframe([{"data": "test", "price": bad_price, "month": 1, "year": 2023}])

        # Act + Assert
        with patch("data_processing.data_core.mappings", _mock_mappings), pytest.raises(ValueError):
            process_dataframe(df)

    @pytest.mark.parametrize(
        "price,expected_rows",
        [
            ("NaN", 0),  # NaN <= 0 is False → filtered out
            ("inf", 0),  # inf <= 0 is False → filtered out
            ("-inf", 1),  # -inf <= 0 is True → kept (abs = inf → str "inf")
            ("1e308", 0),  # very large positive → filtered out as income
        ],
        ids=["nan", "pos_inf", "neg_inf", "large_float"],
    )
    def test_process_dataframe_special_float_documented_behavior(
        self,
        price: str,
        expected_rows: int,
        make_transaction_dataframe: Callable[[list[TransactionRow]], pd.DataFrame],
    ) -> None:
        """Documents how process_dataframe handles special float strings.

        NaN and positive inf are silently filtered out by the ``<= 0`` guard.
        Negative inf passes the guard and is kept — this is a known gap (M11).
        """
        # Arrange
        df = make_transaction_dataframe([{"data": "test", "price": price, "month": 1, "year": 2023}])

        # Act
        with patch("data_processing.data_core.mappings", _mock_mappings):
            result = process_dataframe(df)

        # Assert — document the actual (not necessarily ideal) behavior
        assert len(result) == expected_rows


# ---------------------------------------------------------------------------
# Long input strings (replaces F05)
# ---------------------------------------------------------------------------


class TestLongInputHandling:
    @pytest.mark.timeout(5)
    def test_process_dataframe_with_long_description_preserves_value(
        self,
        make_transaction_dataframe: Callable[[list[TransactionRow]], pd.DataFrame],
    ) -> None:
        """Given a 1 MB description string,
        when process_dataframe() runs,
        then it completes within 5 s and the original value is returned unchanged.
        """
        # Arrange
        long_string = "A" * 1_000_000
        df = make_transaction_dataframe([{"data": long_string, "price": "-10.0", "month": 1, "year": 2023}])

        # Act
        with patch("data_processing.data_core.mappings", _mock_mappings):
            result = process_dataframe(df)

        # Assert
        assert result["data"].iloc[0] == long_string


# ---------------------------------------------------------------------------
# Month / year range (replaces F08)
# ---------------------------------------------------------------------------


class TestMonthYearDocumentedBehavior:
    def test_process_dataframe_with_out_of_range_month_year_does_not_validate(
        self,
        make_transaction_dataframe: Callable[[list[TransactionRow]], pd.DataFrame],
    ) -> None:
        """Documents that process_dataframe does NOT validate month/year ranges.

        Given out-of-range month (13, -1, 0) and unusual year values,
        when process_dataframe() runs,
        then it returns a DataFrame without raising — validation is a known gap.
        """
        # Arrange
        df = make_transaction_dataframe([
            {"data": "test_a", "price": "-10.0", "month": 13, "year": 1800},
            {"data": "test_b", "price": "-20.0", "month": -1, "year": 3000},
            {"data": "test_c", "price": "-30.0", "month": 0, "year": -1},
        ])

        # Act
        with patch("data_processing.data_core.mappings", _mock_mappings):
            result = process_dataframe(df)

        # Assert — structural, not value-range, validation
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
