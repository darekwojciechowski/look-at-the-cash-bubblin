"""Resource-exhaustion security tests.

Replaces TestResourceExhaustion (F05, F11, F12).
Adds M08 (decompression bomb — xfail, unguarded).
All tests carry @pytest.mark.timeout to bound wall-clock time.
"""

import gzip
from pathlib import Path

import pytest

from data_processing.data_core import clean_descriptions
from data_processing.data_imports import read_transaction_csv

pytestmark = [pytest.mark.security, pytest.mark.slow]


def _mock_mappings(data: str) -> str:
    return "MISC"


# ---------------------------------------------------------------------------
# Large-file read (replaces F11)
# ---------------------------------------------------------------------------


class TestLargeFileHandling:
    @pytest.mark.timeout(30)
    def test_read_large_csv_within_time_budget(self, tmp_path: Path) -> None:
        """Given a CSV with 100 000 rows,
        when read_transaction_csv() is called,
        then all rows are loaded within 30 s without a MemoryError.
        """
        # Arrange
        large_csv = tmp_path / "large.csv"
        with open(large_csv, "w", encoding="utf-8") as fh:
            fh.write("data,price,month,year\n")
            for i in range(100_000):
                fh.write(f"transaction{i},-{i % 100 + 1}.0,1,2023\n")

        # Act

        df = read_transaction_csv(str(large_csv), "utf-8")

        # Assert
        assert len(df) == 100_000


# ---------------------------------------------------------------------------
# Decompression bomb (M08) — xfail
# ---------------------------------------------------------------------------


class TestDecompressionBomb:
    @pytest.mark.timeout(10)
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "read_transaction_csv() uses pd.read_csv with no size guard on gzip "
            "expansion; a streaming-reader cap is not yet implemented."
        ),
    )
    def test_read_rejects_decompression_bomb(self, tmp_path: Path) -> None:
        """Given a gzip-compressed CSV that inflates to a huge size,
        when read_transaction_csv() is called,
        then it raises or caps memory rather than exhausting the process.

        xfail: pandas autodetects gzip without a size guard; this path is
        unguarded in the current codebase.  A future hardening task must add
        a streaming reader with a size cap.
        """
        # Arrange — 100 B compressed, ~1 MB inflated (harmless for xfail)
        row = "transaction,-10.0,1,2023\n"
        repeated = (row * 5_000).encode("utf-8")
        bomb_path = tmp_path / "bomb.csv.gz"
        with gzip.open(bomb_path, "wb") as gz:
            gz.write(b"data,price,month,year\n")
            gz.write(repeated)

        # Assert — must raise rather than inflating unbounded
        with pytest.raises((MemoryError, OSError, ValueError)):
            read_transaction_csv(str(bomb_path), "utf-8")


# ---------------------------------------------------------------------------
# Long string / deeply nested parentheses (replaces F05, F12)
# ---------------------------------------------------------------------------


class TestPathologicalInputStrings:
    @pytest.mark.timeout(5)
    def test_deeply_nested_paren_string_does_not_stall_cleaning(self) -> None:
        """Given a description with 1 000 levels of parentheses,
        when clean_descriptions() runs,
        then it completes within 5 s without a stack overflow.

        Replaces F12 which only tested pd.DataFrame construction, not the SUT.
        """
        import pandas as pd

        # Arrange
        nested = "(" * 1_000 + "data" + ")" * 1_000
        df = pd.DataFrame({"data": [nested], "price": ["-10.0"], "month": [1], "year": [2023]})

        # Act
        result = clean_descriptions(df)

        # Assert
        assert result["data"].iloc[0] == nested

    @pytest.mark.timeout(5)
    def test_pathological_regex_input_does_not_stall(self) -> None:
        """Given a description designed to trigger catastrophic backtracking,
        when clean_descriptions() runs,
        then it completes within 5 s.

        clean_descriptions uses regex=False (data_core.py:49) so ReDoS is not
        a concern; this test locks that invariant in.
        """
        import pandas as pd

        # Arrange — classic ReDoS pattern for (a+)+ style engines
        evil_regex_input = "a" * 30 + "!"  # triggers backtracking in vulnerable engines
        df = pd.DataFrame({"data": [evil_regex_input], "price": ["-10.0"], "month": [1], "year": [2023]})

        # Act
        result = clean_descriptions(df)

        # Assert — value unchanged (no replacements match this string)
        assert result["data"].iloc[0] == evil_regex_input
