"""Export-hardening tests (M14, M15).

Covers:
- Symlink TOCTOU on the fixed output filename (M15) — xfail.
- File-mode 0o600 on POSIX after export — xfail.
- ipko_import robustness to wrong column counts (M14).
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_imports import ipko_import
from data_processing.exporter import export_for_google_sheets

pytestmark = pytest.mark.security


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_raw_ipko_df(n_cols: int) -> pd.DataFrame:
    """Build a raw DataFrame mimicking an IPKO CSV export with *n_cols* columns."""
    row: dict[int, list[str]] = {i: [f"val_{i}"] for i in range(n_cols)}
    if n_cols >= 1:
        row[0] = ["2023-01-15"]  # transaction_date
    if n_cols >= 4:
        row[3] = ["-100.0"]  # price
    return pd.DataFrame(row)


def _make_export_df() -> pd.DataFrame:
    return pd.DataFrame({
        "data": ["regular description"],
        "amount": ["-10.0"],
        "day": [15],
        "month": [1],
        "year": [2023],
        "category": ["MISC"],
    })


# ---------------------------------------------------------------------------
# Symlink TOCTOU (M15) — xfail
# ---------------------------------------------------------------------------


class TestSymlinkToctou:
    @pytest.mark.skipif(sys.platform == "win32", reason="symlinks require elevated privileges on Windows")
    def test_export_refuses_symlink_target(self, isolated_cwd: Path) -> None:
        """Given that google_sheets_expenses.csv already exists as a symlink
        pointing at a victim file, export_for_google_sheets must refuse to follow it.
        """
        # Arrange — create the symlink before the export call
        victim = isolated_cwd / "victim.txt"
        victim.write_text("SENSITIVE DATA", encoding="utf-8")
        symlink = isolated_cwd / "google_sheets_expenses.csv"
        try:
            symlink.symlink_to(victim)
        except (OSError, NotImplementedError):
            pytest.skip("Cannot create symlink on this platform")

        with pytest.raises((OSError, PermissionError)):
            export_for_google_sheets(_make_export_df())

        # Victim file must be untouched
        assert victim.read_text(encoding="utf-8") == "SENSITIVE DATA"


# ---------------------------------------------------------------------------
# File mode (M02 / PII) — xfail
# ---------------------------------------------------------------------------


class TestExportFileMode:
    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes not applicable on Windows")
    def test_export_file_mode_is_0o600_on_posix(self, isolated_cwd: Path) -> None:
        """After export, the output file must be readable only by the owner (0o600)."""
        output = export_for_google_sheets(_make_export_df())
        file_mode = output.stat().st_mode & 0o777
        assert file_mode == 0o600, f"Expected 0o600 but got 0o{file_mode:o}"


# ---------------------------------------------------------------------------
# Column-count robustness (M14)
# ---------------------------------------------------------------------------


class TestIpkoImportColumnCounts:
    def test_ipko_import_rejects_too_few_columns(self) -> None:
        """Given a raw CSV with only 7 columns (expected: 9),
        when ipko_import() is called,
        then an explicit error is raised (not a silent column-shift).
        """
        # Arrange — 7-column DataFrame
        df = _make_raw_ipko_df(7)

        # Act + Assert — IndexError from df.columns[8] access
        with pytest.raises((IndexError, KeyError, ValueError)):
            ipko_import(df)

    def test_ipko_import_with_extra_columns_documents_behavior(self) -> None:
        """Given a raw CSV with 10 columns instead of the expected 9,
        when ipko_import() is called,
        then the documented behavior is that the extra column is silently ignored.

        This test pins the current behavior.  A future hardening task should make
        the column-count mismatch explicit (raise ValueError for M14).
        """
        # Arrange — 10-column DataFrame (one extra beyond the expected 9)
        df = _make_raw_ipko_df(10)

        # Act — current code accesses columns[0..8] by position and ignores [9]
        result = ipko_import(df)

        # Assert — pipeline still produces the required output columns
        assert {"amount", "data", "month", "year"}.issubset(result.columns)
