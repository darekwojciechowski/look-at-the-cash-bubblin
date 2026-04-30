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
        "day": [15] * len(data_values),
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
        "price",
        ["-10.0", "-100.50", "-1.0"],
        ids=["minus", "minus_decimal", "minus_one"],
    )
    def test_export_for_google_sheets_escapes_formula_chars(
        self,
        price: str,
        isolated_cwd: Path,
    ) -> None:
        """Given a negative price, export_for_google_sheets must prefix the Amount
        column with a literal quote so spreadsheets treat it as plain text.

        When:  export_for_google_sheets() is called with a negative price
        Then:  the Amount column in the written CSV starts with a quote prefix
        """
        # Arrange
        df = pd.DataFrame({
            "data": ["some description"],
            "price": [price],
            "day": [15],
            "month": [1],
            "year": [2023],
            "category": ["MISC"],
        })

        # Act
        output = export_for_google_sheets(df)

        # Assert — read back with tab separator and confirm Amount is sanitized
        result_df = pd.read_csv(output, sep="\t")
        sanitized_value = result_df["Amount"].iloc[0]
        assert isinstance(sanitized_value, str) and sanitized_value.startswith("'"), (
            f'Expected negative Amount {price!r} to be prefixed with "\'" but cell value was {sanitized_value!r}'
        )

    @pytest.mark.parametrize(
        "payload",
        ["=A1", "+1", "-1", "@SUM(1,2)"],
        ids=["eq", "plus", "minus", "at"],
    )
    def test_export_cleaned_data_escapes_formula_chars_in_category(
        self,
        payload: str,
        isolated_cwd: Path,
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
            "day": [1],
            "month": [1],
            "year": [2023],
            "category": [payload],
        })
        output = isolated_cwd / "out.csv"

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
        """Given prices and categories without injection-triggering characters,
        export_for_google_sheets must not add a spurious quote prefix to output columns.

        When:  export_for_google_sheets() is called with a positive price
        Then:  Amount, Category and Importance are written unchanged (no spurious quote prefix)
        """
        # Arrange — positive price and a known-safe category produce benign output values
        df = pd.DataFrame({
            "data": ["regular description"],
            "price": ["100.0"],
            "day": [15],
            "month": [1],
            "year": [2023],
            "category": ["FOOD"],
        })

        # Act
        output = export_for_google_sheets(df)

        # Assert — read back with tab separator and confirm no spurious quote prefix
        result_df = pd.read_csv(output, sep="\t")
        assert result_df["Amount"].iloc[0] == "100,0", f"Benign Amount was mangled: {result_df['Amount'].iloc[0]!r}"
        assert not str(result_df["Category"].iloc[0]).startswith("'"), "Benign Category was mangled"
        assert not str(result_df["Importance"].iloc[0]).startswith("'"), "Benign Importance was mangled"

    def test_export_handles_embedded_tab_and_cr(self, isolated_cwd: Path) -> None:
        """Given a description with embedded \\t or \\r (not at position 0), the export
        must not break out of the CSV row.

        When:  export_for_google_sheets() is called with embedded control chars
        Then:  the CSV is valid (can be read back with the same row count)
        """
        # Arrange — embedded, not leading, so no sanitization needed; just row integrity
        df = _make_df(["safe\tstuff", "also\rsafe", "with\nnewline"])

        # Act
        output = export_for_google_sheets(df)

        # Assert — CSV is still parseable and has the right row count
        result = pd.read_csv(output)
        assert len(result) == len(df)
