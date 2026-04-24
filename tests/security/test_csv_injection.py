"""CSV / spreadsheet formula-injection tests (M01).

The pipeline's primary export target is Google Sheets.  Any merchant text that
starts with ``=``, ``+``, ``-``, ``@``, ``\\t``, or ``\\r`` is executed as a
formula when the CSV is opened in Sheets or Excel.  These tests verify that
all export functions neutralise such values by prefixing them with ``'``.
"""

from pathlib import Path

import pandas as pd
import pytest

from data_processing.exporter import (
    export_cleaned_data,
    export_for_google_sheets,
    export_unassigned_transactions_to_csv,
)

pytestmark = pytest.mark.security


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_csv_raw(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def _make_df(data_values: list[str]) -> pd.DataFrame:
    return pd.DataFrame({
        "data": data_values,
        "price": ["-10.0"] * len(data_values),
        "month": [1] * len(data_values),
        "year": [2023] * len(data_values),
        "category": ["MISC"] * len(data_values),
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFormulaInjectionOnExport:
    """All export functions must sanitize leading formula-injection characters."""

    @pytest.mark.parametrize(
        "payload",
        [
            "=A1",
            "+1+1",
            "-1",
            "@SUM(A1:A2)",
            "\t=tabbed",
            "\r=cr-leading",
            '=HYPERLINK("https://evil.example.com","click")',
            "=cmd|'/c calc'!A0",
        ],
        ids=["eq", "plus", "minus", "at", "tab", "cr", "hyperlink", "dde"],
    )
    def test_export_for_google_sheets_escapes_formula_chars(
        self,
        payload: str,
        isolated_cwd: Path,
    ) -> None:
        """Given a description starting with a formula trigger, export_for_google_sheets
        must prefix it with a literal quote so spreadsheets treat it as plain text.

        When:  export_for_google_sheets() is called
        Then:  the written CSV does not contain an unescaped formula trigger in the data column
        """
        # Arrange
        df = _make_df([payload])

        # Act
        export_for_google_sheets(df)

        # Assert — read back and confirm the cell starts with the quote prefix.
        # Using pandas to parse avoids platform-specific line-ending issues with
        # payloads containing \r (which CSV quoting wraps across two raw lines).
        output = isolated_cwd / "for_google_spreadsheet.csv"
        result_df = pd.read_csv(output)
        sanitized_value = result_df["data"].iloc[0]
        assert isinstance(sanitized_value, str) and sanitized_value.startswith("'"), (
            f'Expected formula trigger {payload!r} to be prefixed with "\'" but cell value was {sanitized_value!r}'
        )

    @pytest.mark.parametrize(
        "payload",
        ["=A1", "+1", "-1", "@SUM(1,2)"],
        ids=["eq", "plus", "minus", "at"],
    )
    def test_export_cleaned_data_escapes_formula_chars_in_category(
        self,
        payload: str,
        tmp_path: Path,
    ) -> None:
        """Given a category value starting with a formula trigger, export_cleaned_data
        must sanitize it in the written CSV.

        When:  export_cleaned_data() is called
        Then:  the category column in the CSV has the quote prefix applied
        """
        # Arrange
        df = pd.DataFrame({
            "data": ["safe description"],
            "price": ["10.0"],
            "month": [1],
            "year": [2023],
            "category": [payload],
        })
        output = tmp_path / "out.csv"

        # Act
        export_cleaned_data(df, output_file=output)

        # Assert
        content = _read_csv_raw(output)
        assert "'" + payload[0] in content, f"Category {payload!r} should be sanitized but got:\n{content}"

    @pytest.mark.parametrize(
        "payload",
        ["=WEBSERVICE('evil')", "+1+cmd"],
        ids=["webservice", "plus_cmd"],
    )
    def test_export_unassigned_escapes_formula_chars(
        self,
        payload: str,
        isolated_cwd: Path,
    ) -> None:
        """Given formula-injection text in a MISC row, export_unassigned_transactions_to_csv
        must sanitize it in the written CSV.

        When:  export_unassigned_transactions_to_csv() is called
        Then:  the data column is prefixed with a quote
        """
        # Arrange
        df = pd.DataFrame({
            "data": [payload],
            "price": ["10.0"],
            "month": [1],
            "year": [2023],
            "category": ["MISC"],
        })

        # Act
        export_unassigned_transactions_to_csv(df)

        # Assert
        output = isolated_cwd / "unassigned_transactions.csv"
        content = _read_csv_raw(output)
        assert "'" + payload[0] in content, f"Expected {payload!r} to be sanitized but got:\n{content}"

    def test_export_preserves_benign_leading_chars(self, isolated_cwd: Path) -> None:
        """Given descriptions starting with safe characters, export must not mangle them.

        When:  export_for_google_sheets() is called
        Then:  benign values are written unchanged (no spurious quote prefix)
        """
        # Arrange
        benign = ["regular description", "123 amount", "Starbucks coffee"]
        df = _make_df(benign)

        # Act
        export_for_google_sheets(df)

        # Assert
        output = isolated_cwd / "for_google_spreadsheet.csv"
        content = _read_csv_raw(output)
        for desc in benign:
            assert desc in content, f"Benign description {desc!r} was mangled. CSV:\n{content}"

    def test_export_handles_embedded_tab_and_cr(self, isolated_cwd: Path) -> None:
        """Given a description with embedded \\t or \\r (not at position 0), the export
        must not break out of the CSV row.

        When:  export_for_google_sheets() is called with embedded control chars
        Then:  the CSV is valid (can be read back with the same row count)
        """
        # Arrange — embedded, not leading, so no sanitization needed; just row integrity
        df = _make_df(["safe\tstuff", "also\rsafe", "with\nnewline"])

        # Act
        export_for_google_sheets(df)

        # Assert — CSV is still parseable and has the right row count
        output = isolated_cwd / "for_google_spreadsheet.csv"
        result = pd.read_csv(output)
        assert len(result) == len(df)
