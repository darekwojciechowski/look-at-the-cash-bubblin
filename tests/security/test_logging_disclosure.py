"""PII / data-disclosure tests for logging behaviour (M02, M05).

Covers:
- export_for_google_sheets must not log the full DataFrame (M02).
- export_for_google_sheets logs row count only (positive assertion).
- read_transaction_csv must log a WARNING for each skipped bad line (M05).
"""

from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_imports import read_transaction_csv
from data_processing.exporter import export_for_google_sheets

pytestmark = pytest.mark.security

_SENTINEL = "SECRET_TOKEN_zQ9xKpL2mN7vR4wT"


def _make_export_df(extra_data: str = "regular description") -> pd.DataFrame:
    return pd.DataFrame({
        "data": [extra_data],
        "price": ["-10.0"],
        "month": [1],
        "year": [2023],
        "category": ["MISC"],
    })


# ---------------------------------------------------------------------------
# M02 — No full-DataFrame logging
# ---------------------------------------------------------------------------


class TestPiiNotLeakedToLogs:
    def test_export_does_not_log_full_dataframe_content(
        self,
        loguru_sink: list[str],
        isolated_cwd: Path,
    ) -> None:
        """Given a DataFrame containing a known unique token,
        when export_for_google_sheets() is called,
        then the token must NOT appear in any log record.

        This guards against exporter.py previously dumping the entire DataFrame
        via to_string(), which would expose raw transaction text in app.log.
        """
        # Arrange
        df = _make_export_df(extra_data=_SENTINEL)

        # Act
        export_for_google_sheets(df)

        # Assert — the unique sentinel must not be in any log message
        leaking_records = [msg for msg in loguru_sink if _SENTINEL in msg]
        assert not leaking_records, f"Sensitive data '{_SENTINEL}' was found in log records:\n" + "\n".join(
            leaking_records
        )

    def test_export_logs_row_count_only(
        self,
        loguru_sink: list[str],
        isolated_cwd: Path,
    ) -> None:
        """Given a DataFrame with 3 rows,
        when export_for_google_sheets() is called,
        then at least one log record mentions the row count (3).
        """
        # Arrange
        df = pd.DataFrame({
            "data": ["desc_a", "desc_b", "desc_c"],
            "price": ["-10.0", "-20.0", "-30.0"],
            "month": [1, 1, 1],
            "year": [2023, 2023, 2023],
            "category": ["MISC", "FOOD", "FUEL"],
        })

        # Act
        export_for_google_sheets(df)

        # Assert — some log record references the row count
        assert any("3" in msg for msg in loguru_sink), (
            f"Expected a log record mentioning 3 rows. Records:\n{loguru_sink}"
        )


# ---------------------------------------------------------------------------
# M05 — Bad-line skip must emit WARNING
# ---------------------------------------------------------------------------


class TestBadLineLogging:
    def test_read_skipped_bad_line_logged_at_warning(
        self,
        tmp_path: Path,
        loguru_sink: list[str],
    ) -> None:
        """Given a CSV with one malformed row (too many fields),
        when read_transaction_csv() is called,
        then a WARNING-level log record containing '[SKIP_BAD_LINE]' is emitted.

        The malformed row is still skipped so the good rows are returned.
        """
        # Arrange — header has 4 fields; bad row has 6
        csv_content = (
            "data,price,month,year\n"
            "good_row,-10.0,1,2023\n"
            "bad_row,-20.0,1,2023,EXTRA,FIELD\n"  # too many fields → bad line
            "another_good,-30.0,2,2023\n"
        )
        csv_file = tmp_path / "bad_lines.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        # Act
        df = read_transaction_csv(str(csv_file), "utf-8")

        # Assert — good rows still loaded
        assert len(df) == 2
        # Assert — warning was emitted for the bad line
        assert any("[SKIP_BAD_LINE]" in msg for msg in loguru_sink), (
            f"Expected '[SKIP_BAD_LINE]' WARNING in logs. Records:\n{loguru_sink}"
        )
